from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Set up sensors from config entry."""
    client = hass.data[DOMAIN][entry.entry_id]

    # Liste deiner Temperaturfelder
    temperature_sensors = [
        ("Vorlauf", "vorlauf"),
        ("Rücklauf", "ruecklauf"),
        # du kannst hier beliebig erweitern…
    ]

    sensors = [
        LuxtronikTemperatureSensor(client, name, field)
        for name, field in temperature_sensors
    ]

    async_add_entities(sensors, True)



class LuxtronikTemperatureSensor(SensorEntity):
    """Representation of a Luxtronik temperature sensor."""

    def __init__(self, client, name: str, field: str):
        self._client = client
        self._field = field

        # Home Assistant Entity Metadata
        self._attr_name = f"Luxtronik {name}"
        self._attr_unique_id = f"luxtronik2_{field}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = "°C"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the latest temperature value from the client."""

        value = self._client.get_value(self._field)

        if value is None:
            return None

        # Entferne °C falls als Text geliefert
        if isinstance(value, str) and value.endswith("°C"):
            try:
                value = float(value.replace("°C", "").strip())
            except ValueError:
                return None

        return value

    async def async_update(self):
        """No polling — updates are pushed via websocket."""
        return
