import re
import asyncio
import logging
import websocket

_LOGGER = logging.getLogger(__name__)


class LuxtronikClient:
    """WebSocket client for Luxtronik heat pump."""

    def __init__(self, ip: str, password: str, port: int, interval: int):
        self.ip = ip
        self.password = password
        self.port = port
        self.interval = interval

        self.ws = None
        self._task = None
        self._should_run = True
        self._listeners = []

        self.values = {}
        self.temp_id = None
        self.waerm_id = None
        self.output_id = None
        self.values["heizleistung"] = None

    def register_listener(self, callback):
        self._listeners.append(callback)

    def _notify_listeners(self):
        for callback in self._listeners:
            try:
                callback()
            except Exception:
                pass

    async def connect_once(self):
        import websocket

        self.ws = websocket.WebSocket()
        self.ws.connect(f"ws://{self.ip}:{self.port}", subprotocols=["Lux_WS"])
        self.ws.send(f"LOGIN;{self.password}")

    async def test_connection(self):
        import asyncio

        try:
            await asyncio.wait_for(self.connect_once(), timeout=5)
        except Exception as e:
            raise e

    # -------------------------------------------------------------
    # Public API used by HA
    # -------------------------------------------------------------
    async def start(self):
        """Start background polling loop."""
        if self._task is None:
            self._task = asyncio.create_task(self.run())
            _LOGGER.debug("LuxtronikClient: Background task started")

    async def close(self):
        """Stop background loop and close socket."""
        _LOGGER.debug("LuxtronikClient: Closing...")

        self._should_run = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

        _LOGGER.debug("LuxtronikClient: Closed.")

    # -------------------------------------------------------------
    # Core loop
    # -------------------------------------------------------------
    async def run(self):
        """Reconnect loop with polling."""
        _LOGGER.debug("LuxtronikClient RUN start")

        await asyncio.to_thread(self._connect)
        # Navigation lesen
        nav_xml = await asyncio.to_thread(self.ws.recv)
        self._parse_navigation(nav_xml)
        while self._should_run:
            try:
                await self._poll()
            except Exception as err:
                _LOGGER.error("Luxtronik Error: %s", err)
                await asyncio.sleep(20)
                await asyncio.to_thread(self._connect)

            await asyncio.sleep(self.interval)

    # -------------------------------------------------------------
    async def _poll(self):
        """Poll all categories exactly once each cycle."""

        # Temperaturen
        if self.temp_id:
            await asyncio.to_thread(self.ws.send, f"GET;{self.temp_id}")
            xml_temp = await asyncio.to_thread(self.ws.recv)
            self._parse_values(xml_temp)

        # Wärmemenge
        if self.waerm_id:
            await asyncio.to_thread(self.ws.send, f"GET;{self.waerm_id}")
            xml_waerme = await asyncio.to_thread(self.ws.recv)
            self._parse_waermemenge(xml_waerme)

        # Ausgänge
        if self.output_id:
            await asyncio.to_thread(self.ws.send, f"GET;{self.output_id}")
            xml_outputs = await asyncio.to_thread(self.ws.recv)
            self._parse_outputs(xml_outputs)

        # Heizleistung berechnen
        self._calculate_heizleistung()

        self._notify_listeners()

    def _calculate_heizleistung(self):
        """Berechnung der Heizleistung (Watt), Formel wird noch ergänzt."""

        try:
            # Formel folgt später – Platzhalter:

            try:
                vor = float(self.values.get("vorlauf"))
                rueck = float(self.values.get("ruecklauf"))
                flow = float(self.values.get("durchfluss"))  # l/h

            except (TypeError, ValueError):
                return None

            # Platzhalterformel (du gibst später genau an)
            delta = vor - rueck

            if flow <= 0 or delta < 0:
                self.values["heizleistung"] = 0
            else:
                heat_watts = flow / 3600 * 4180 * delta
                self.values["heizleistung"] = round(heat_watts, 2)

        except Exception as e:
            print("Heizleistung-Berechnung Fehler:", e)
            self.values["heizleistung"] = None

    # -------------------------------------------------------------
    # Blocking WS ops → wrapped into asyncio threads
    # -------------------------------------------------------------
    def _connect(self):
        """Blocking WebSocket connect."""
        url = f"ws://{self.ip}:{self.port}"
        self.ws = websocket.WebSocket()
        self.ws.connect(url, subprotocols=["Lux_WS"])
        self.ws.send(f"LOGIN;{self.password}")

    # -------------------------------------------------------------
    # Parsing helpers
    # -------------------------------------------------------------
    def _parse_navigation(self, xml: str):
        import re

        """Extract navigation IDs."""
        # Example: find Temperatures menu entry
        if "Temperaturen" in xml:
            m = re.search(r"<item id='([^']+)'><name>Temperaturen</name>", xml)
            if m:
                self.temp_id = m.group(1)

        if "Wärmemenge" in xml:
            m = re.search(r"<item id='([^']+)'><name>Wärmemenge</name>", xml)
            if m:
                self.waerm_id = m.group(1)

        if "Ausgänge" in xml:
            m = re.search(r"<item id='([^']+)'><name>Ausgänge</name>", xml)
            if m:
                self.output_id = m.group(1)

    # -------------------------------------------------------------
    def get_value(self, key):
        """Public getter used by sensors."""
        return self.values.get(key)

    def _clean_value(self, value: str):
        """Strip Einheit und als float zurückgeben, sofern möglich."""
        v = value.strip()

        # Temperatur
        if v.endswith("°C"):
            try:
                return float(v[:-2].strip())
            except ValueError:
                return None

        # Energie (kWh)
        if v.endswith("kWh"):
            try:
                return float(v[:-3].strip())
            except ValueError:
                return None

        # Durchfluss (l/h oder ' l/h')
        if v.endswith("l/h"):
            try:
                return float(v[:-3].strip())
            except ValueError:
                return None

        # Fallback: nackt als float versuchen
        try:
            return float(v)
        except ValueError:
            return None

    def _parse_values(self, xml: str):
        """Temperatur-XML: <name><value>-Paare auslesen."""
        NAME_MAP = {
            "Vorlauf": "vorlauf",
            "Rücklauf": "ruecklauf",
            "Rückl.-Soll": "ruecklauf_soll",
            "Heissgas": "heissgas",
            "Aussentemperatur": "aussentemperatur",
            "Mitteltemperatur": "mitteltemperatur",
            "Warmwasser-Ist": "warmwasser_ist",
            "Warmwasser-Soll": "warmwasser_soll",
            "Solarkollektor": "solarkollektor",
            "Solarspeicher": "solarspeicher",
            "Externe Energ.Quelle": "externe_energiequelle",
        }

        for name, value in re.findall(
            r"<name>([^<]+)</name><value>([^<]+)</value>", xml
        ):
            clean_value = self._clean_value(value)
            key = NAME_MAP.get(name, name)
            self.values[key] = clean_value

    def _parse_waermemenge(self, xml: str):
        """Wärmemenge-XML parsen (kWh & Durchfluss)."""
        NAME_MAP_WAERME = {
            "Heizung": "waerme_heizung",
            "Warmwasser": "waerme_ww",
            "Gesamt": "waerme_gesamt",
            "Durchfluss": "durchfluss",
            "seit : 14. 2.2025": "waerme_seit_datum",
            "seit Reset:": "waerme_seit_reset",
        }

        for name, value in re.findall(
            r"<name>([^<]+)</name><value>([^<]+)</value>", xml
        ):
            clean_value = self._clean_value(value)
            key = NAME_MAP_WAERME.get(name, name)
            self.values[key] = clean_value

    def _parse_outputs(self, xml: str):
        OUTPUT_MAP = {
            "AV-Abtauventil": "av_abtauventil",
            "BUP": "bup",
            "FUP 1": "fup1",
            "HUP": "hup",
            "Ventilation": "ventilation",
            "Ventil.-BOSUP": "ventil_bosup",
            "Verdichter": "verdichter",
            "ZIP": "zip",
            "ZUP": "zup",
            "ZWE 1": "zwe1",
            "ZWE 2 - SST": "zwe2",
            "ZWE 3": "zwe3",
            "SLP": "slp",
            "FUP 2": "fup2",
            "FUP 3": "fup3",
        }
        for name, value in re.findall(
            r"<name>([^<]+)</name><value>([^<]+)</value>", xml
        ):
            if name in OUTPUT_MAP:
                self.values[OUTPUT_MAP[name]] = value
