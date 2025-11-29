from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from homeassistant.core import callback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    client = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = []

    # Temperatur-Sensoren
    temp_defs = [
        ("Vorlauf", "vorlauf"),
        ("Rücklauf", "ruecklauf"),
        ("Rückl.-Soll", "ruecklauf_soll"),
        ("Heissgas", "heissgas"),
        ("Aussentemperatur", "aussentemperatur"),
        ("Warmwasser-Ist", "warmwasser_ist"),
        ("Warmwasser-Soll", "warmwasser_soll"),
    ]

    for name, field in temp_defs:
        sensors.append(
            LuxtronikSensor(
                client=client,
                name=f"{name}",
                field=field,
                unit="°C",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            )
        )

    sensors.append(LuxtronikPowerSensor(client, "Heizleistung", "heizleistung"))

    # Wärmemengen & Durchfluss
    waerme_defs = [
        (
            "Wärmemenge Heizung",
            "waerme_heizung",
            "kWh",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL,
        ),
        (
            "Wärmemenge Warmwasser",
            "waerme_ww",
            "kWh",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL,
        ),
        (
            "Wärmemenge Gesamt",
            "waerme_gesamt",
            "kWh",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL,
        ),
        (
            "Durchfluss",
            "durchfluss",
            "l/h",
            SensorDeviceClass.VOLUME_FLOW_RATE,
            SensorStateClass.MEASUREMENT,
        ),
    ]

    for name, field, unit, dev_class, state_class in waerme_defs:
        sensors.append(
            LuxtronikSensor(
                client=client,
                name=f"{name}",
                field=field,
                unit=unit,
                device_class=dev_class,
                state_class=state_class,
            )
        )

    binary_outputs = {
        "av_abtauventil": "AV-Abtauventil",
        "bup": "BUP",
        "fup1": "FUP 1",
        "hup": "HUP",
        "ventilation": "Ventilation",
        "ventil_bosup": "Ventil.-BOSUP",
        "verdichter": "Verdichter",
        "zip": "ZIP",
        "zup": "ZUP",
        "zwe1": "ZWE 1",
        "zwe2": "ZWE 2 - SST",
        "zwe3": "ZWE 3",
        "slp": "SLP",
        "fup2": "FUP 2",
        "fup3": "FUP 3",
    }

    for key, name in binary_outputs.items():
        sensors.append(LuxtronikBinaryOutput(client, name, key))

    sensors.append(LuxtronikStringSensor(client, "Betriebszustand", "Betriebszustand"));

    async_add_entities(sensors, True)


class LuxtronikSensor(SensorEntity):
    """Generischer Luxtronik-Sensor."""

    def __init__(
        self,
        client,
        name: str,
        field: str,
        unit: str | None = None,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
    ):
        self._client = client
        self._client.register_listener(self._handle_client_update)
        self._field = field

        self._attr_name = name
        self._attr_unique_id = f"luxtronik2_{field}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self):
        """Letzten Wert aus dem Client holen."""
        return self._client.get_value(self._field)

    async def async_update(self):
        # Polling macht der Client, hier nur Debug falls gewünscht
        # print(f"LUX SENSOR ASYNC UPDATE {self._field}")
        return

    @callback
    def _handle_client_update(self):
        """Handle push-update from client."""
        self.async_write_ha_state()


class LuxtronikPowerSensor(SensorEntity):
    """Berechnete Heizleistung (Watt)."""

    def __init__(self, client, name: str, field: str):
        self._client = client
        self._field = field
        self._client.register_listener(self._handle_client_update)

        self._attr_name = f"{name}"
        self._attr_unique_id = f"luxtronik2_{field}"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = "W"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return calculated heat power."""
        value = self._client.get_value(self._field)
        if value is None:
            return None

        # Muss Zahl sein
        try:
            return float(value)
        except:
            return None

    async def async_update(self):
        return

    @callback
    def _handle_client_update(self):
        """Handle push-update from client."""
        self.async_write_ha_state()


from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)


class LuxtronikBinaryOutput(BinarySensorEntity):
    def __init__(self, client, name, field):
        self._client = client
        self._field = field
        self._client.register_listener(self._handle_client_update)
        self._attr_name = f"{name}"
        self._attr_unique_id = f"luxtronik2_{field}"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self):
        value = self._client.get_value(self._field)
        if value is None:
            return None

        return str(value).lower() == "ein"

    @callback
    def _handle_client_update(self):
        """Handle push-update from client."""
        self.async_write_ha_state()


class LuxtronikStringSensor(SensorEntity):
    def __init__(self, client, name, field):
        self._client = client
        self._field = field
        self._client.register_listener(self._handle_client_update)
        self._attr_name = f"{name}"
        self._attr_unique_id = f"luxtronik2_{field}"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None

    @property
    def native_value(self):
        return self._client.get_value(self._field)

    @callback
    def _handle_client_update(self):
        """Handle push-update from client."""
        self.async_write_ha_state()
