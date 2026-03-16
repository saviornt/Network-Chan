"""MQTT bridge for Home Assistant integration.

Uses the shared AsyncMQTTClient with Pydantic-validated settings.
"""

from typing import Awaitable, Callable, Any

from shared.src.mqtt.mqtt_utils import AsyncMQTTClient
from shared.src.config.settings import mqtt_settings


class HomeAssistantMQTTBridge:
    """Bridge between Network-Chan and Home Assistant via MQTT."""

    def __init__(self) -> None:
        self.client = AsyncMQTTClient(settings=mqtt_settings)

    async def connect(self) -> None:
        await self.client.connect()

    async def subscribe_to_ha_events(
        self,
        callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Subscribe to relevant Home Assistant topics."""
        await self.client.subscribe("homeassistant/#", callback, qos=1)

    async def publish_network_health(
        self,
        status: str = "healthy",
        latency_ms: float = 0.0,
        packet_loss: float = 0.0,
    ) -> None:
        """Publish network health summary as a sensor value."""
        payload = f'{{"status":"{status}","latency_ms":{latency_ms},"packet_loss":{packet_loss}}}'
        await self.client.publish(
            "network-chan/sensor/network_health/state",
            payload,
            retain=True,
        )

    async def disconnect(self) -> None:
        await self.client.disconnect()