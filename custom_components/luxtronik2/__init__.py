from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_IP, CONF_PASSWORD
from .websocket_client import LuxtronikClient

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    ip = entry.data[CONF_IP]
    password = entry.data[CONF_PASSWORD]

    client = LuxtronikClient(ip, password)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    hass.loop.create_task(client.run())

    hass.config_entries.async_setup_platforms(entry, ["sensor"])

    return True
