from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    client = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        LuxtronikTemperatureSensor(client, "Vorlauf", "vorlauf"),
        LuxtronikTemperatureSensor(client, "Rücklauf", "ruecklauf"),
    ]

    async_add_entities(sensors, True)


class LuxtronikTemperatureSensor(SensorEntity):
    def __init__(self, client, name, field):
        self._client = client
        self._name = name
        self._field = field
        self._attr_name = name
        self._attr_unique_id = f"luxtronik2_{field}"

    @property
    def native_value(self):
        return self._client.get_value(self._field)

    async def async_update(self):
        await self._client.request_update()
