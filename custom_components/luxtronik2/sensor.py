from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

SENSOR_KEYS = [
    "Vorlauf",
    "Rücklauf",
    "Warmwasser-Ist",
    "Warmwasser-Soll",
    "Durchfluss"
]

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    client = list(hass.data[DOMAIN].values())[0]

    sensors = [ LuxtronikSensor(client, key) for key in SENSOR_KEYS ]
    add_entities(sensors)

class LuxtronikSensor(SensorEntity):
    def __init__(self, client, key):
        self.client = client
        self.key = key
        self._attr_name = f"Luxtronik {key}"

    @property
    def native_value(self):
        return self.client.get_value(self.key)

    @property
    def should_poll(self):
        return False
