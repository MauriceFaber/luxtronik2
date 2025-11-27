from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_IP, CONF_PORT, CONF_PASSWORD
from .websocket_client import LuxtronikClient


async def async_setup(hass: HomeAssistant, config: dict):
    """Nothing to set up during YAML phase."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Luxtronik2 from a config entry."""

    ip = entry.data[CONF_IP]
    port = entry.data.get(CONF_PORT)
    pwd = entry.data[CONF_PASSWORD]

    client = LuxtronikClient(ip, pwd, port)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    hass.loop.create_task(client.run())

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload integration and stop WS client."""
    client = hass.data[DOMAIN][entry.entry_id]

    await client.close()

    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    hass.data[DOMAIN].pop(entry.entry_id)

    return True
