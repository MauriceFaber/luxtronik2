from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_INTERVAL,
    CONF_IP,
    CONF_PASSWORD,
    CONF_PORT,
    DEFAULT_INTERVAL,
    DEFAULT_PORT,
    DOMAIN,
)
from .websocket_client import LuxtronikClient

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict):
    """Nothing to set up during YAML phase."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Luxtronik via config entry."""

    ip = entry.data[CONF_IP]
    pwd = entry.data[CONF_PASSWORD]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    inverval = entry.data.get(CONF_INTERVAL, DEFAULT_INTERVAL)

    client = LuxtronikClient(ip, pwd, port, inverval)

    # Test connection (Bronze requirement)
    try:
        await client.test_connection()
    except Exception as exc:
        raise ConfigEntryNotReady from exc

    # Store shared instance
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    entry.runtime_data = client  # Bronze requirement

    # 🚀 WICHTIG: Hintergrund-Task starten
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
