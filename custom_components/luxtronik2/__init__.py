from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady

from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_IP, CONF_PORT, CONF_PASSWORD
from .websocket_client import LuxtronikClient

from homeassistant.helpers import config_validation as cv
from .const import DOMAIN

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict):
    """Nothing to set up during YAML phase."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    ip = entry.data[CONF_IP]
    port = entry.data.get(CONF_PORT, 8214)
    pwd = entry.data[CONF_PASSWORD]

    client = LuxtronikClient(ip, pwd, port)

    try:
        # Testverbindung herstellen
        await client.test_connection()
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client
    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload integration and stop WS client."""
    client = hass.data[DOMAIN][entry.entry_id]

    await client.close()

    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    hass.data[DOMAIN].pop(entry.entry_id)

    return True
