# shared/src/mqtt_utils.py

from typing import Any
import asyncio
# paho-mqtt import later; stub with mocks

class MQTTClient:
    def __init__(self, broker: str = 'localhost:1883') -> None:
        self.broker: str = broker
        self.connected: bool = False  # Stub state

    async def connect(self) -> None:
        await asyncio.sleep(0)  # Async connect stub
        self.connected = True
        print(f"Mock connected to {self.broker}")

    async def publish(self, topic: str, payload: Any) -> None:
        if not self.connected:
            await self.connect()
        await asyncio.sleep(0)  # Async yield
        print(f"Mock publish to {topic}: {payload}")  # Real paho later

    async def subscribe(self, topic: str) -> None:
        await asyncio.sleep(0)
        print(f"Mock subscribe to {topic}")