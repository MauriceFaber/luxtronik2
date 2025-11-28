import asyncio
import websocket
import xml.etree.ElementTree as ET


class LuxtronikClient:
    def __init__(self, ip: str, password: str, port: int = 8214):
        self.ip = ip
        self.password = password
        self.port = port
        self.values = {}
        self.temp_id = None
        self.waerm_id = None

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

    def get_value(self, key):
        return self.values.get(key)

    async def run(self):
        while True:
            try:
                await self._connect_and_poll()
            except Exception as e:
                print("Luxtronik Fehler:", e)
            await asyncio.sleep(3)

    async def _connect_and_poll(self):
        ws = websocket.WebSocket()
        ws.connect(f"ws://{self.ip}:{self.port}", subprotocols=["Lux_WS"])
        ws.send(f"LOGIN;{self.password}")

        # initial navigation from WS
        xml_nav = ws.recv()
        nav_id = self._get_id_from_xml(xml_nav)

        # request navigation properly
        ws.send(f"GET;{nav_id}")
        xml_nav2 = ws.recv()

        self.temp_id = self._find_menu_id(xml_nav2, "Temperaturen")
        self.waerm_id = self._find_menu_id(xml_nav2, "Wärmemenge")

        while True:
            # Temperaturen
            ws.send(f"GET;{self.temp_id}")
            xml_temp = ws.recv()
            self._parse_values(xml_temp)

            # Wärmemenge
            ws.send(f"GET;{self.waerm_id}")
            xml_waerm = ws.recv()
            self._parse_values(xml_waerm)

            await asyncio.sleep(2)

    def _get_id_from_xml(self, xml):
        root = ET.fromstring(xml)
        return root.attrib["id"]

    def _find_menu_id(self, xml, name):
        root = ET.fromstring(xml)
        for item in root.iter("item"):
            n = item.find("name")
            if n is not None and n.text == name:
                return item.attrib.get("id")
        return None

    def _parse_values(self, xml):
        root = ET.fromstring(xml)
        for item in root.findall(".//item"):
            name = item.findtext("name")
            value = item.findtext("value")
            if name and value:
                self.values[name] = value
