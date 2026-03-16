"""MQTT client utilities for Network-Chan.

Provides a typed, asynchronous wrapper around paho-mqtt with Pydantic integration.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional

import asyncio
import logging

from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.reasoncodes import ReasonCode
from paho.mqtt.properties import Properties
from paho.mqtt.client import DisconnectFlags  # Typed flags dict

from shared.src.config.settings import MQTTSettings, mqtt_settings

logger = logging.getLogger(__name__)


class AsyncMQTTClient:
    """Asynchronous MQTT client wrapper with type safety and Pydantic config."""

    def __init__(self, settings: Optional[MQTTSettings] = None) -> None:
        """Initialize with optional custom settings (defaults to global mqtt_settings)."""
        self.settings: MQTTSettings = settings or mqtt_settings

        self.client_id: str = self.settings.client_id
        self.client = mqtt_client.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
            protocol=mqtt_client.MQTTv5,
        )

        # Apply credentials if provided
        if self.settings.username and self.settings.password:
            self.client.username_pw_set(
                username=self.settings.username,
                password=self.settings.password.get_secret_value(),
            )

        # Apply TLS if configured
        if self.settings.tls_ca_cert:
            self.client.tls_set(ca_certs=self.settings.tls_ca_cert)  # type: ignore[no-untyped-call]
            self.client.tls_insecure_set(self.settings.tls_insecure)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.sub_callbacks: Dict[str, Callable[[str, Any], Awaitable[None]]] = {}

    def _on_connect(
        self,
        client: mqtt_client.Client,
        userdata: Any,
        flags: Dict[str, Any],
        reason_code: ReasonCode,
        properties: Properties | None = None,
    ) -> None:
        if reason_code == 0:
            logger.info(
                "Connected to MQTT broker %s:%d as %s",
                self.settings.broker,
                self.settings.port,
                self.client_id,
            )
        else:
            logger.error("Connection failed with reason code %s", reason_code)

    def _on_message(
        self,
        client: mqtt_client.Client,
        userdata: Any,
        msg: mqtt_client.MQTTMessage,
    ) -> None:
        topic = msg.topic
        try:
            payload: str | bytes = msg.payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = msg.payload  # raw bytes fallback
        if topic in self.sub_callbacks:
            coro = self.sub_callbacks[topic](topic, payload)
            if self.loop is not None:
                asyncio.create_task(coro, name=f"mqtt-callback-{topic}")  # type: ignore[arg-type]
            else:
                logger.warning("Loop not set; dropping callback for %s", topic)

    def _on_disconnect(
        self,
        client: mqtt_client.Client,
        userdata: Any,
        flags: DisconnectFlags,
        reason_code: ReasonCode,
        properties: Properties | None = None,
    ) -> None:
        logger.warning("Disconnected from MQTT broker (reason_code=%s)", reason_code)

    async def connect(self) -> None:
        """Connect to the MQTT broker asynchronously."""
        self.loop = asyncio.get_running_loop()
        await self.loop.run_in_executor(
            None,
            self.client.connect,
            self.settings.broker,
            self.settings.port,
            self.settings.keepalive,
        )
        self.client.loop_start()

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[str, Any], Awaitable[None]],
        qos: int = 1,
    ) -> None:
        """Subscribe to a topic with an async callback."""
        self.sub_callbacks[topic] = callback
        if self.loop is None:
            raise RuntimeError("Client not connected; loop not initialized")
        result, mid = await self.loop.run_in_executor(
            None, lambda: self.client.subscribe(topic, qos=qos)
        )
        if result == mqtt_client.MQTT_ERR_SUCCESS:
            logger.info("Subscribed to %s (QoS %d, mid=%d)", topic, qos, mid)
        else:
            logger.error("Subscribe failed for %s (result=%d)", topic, result)

    async def publish(
        self, topic: str, payload: str | bytes, qos: int = 1, retain: bool = False
    ) -> None:
        """Publish a message asynchronously."""
        if self.loop is None:
            raise RuntimeError("Client not connected; loop not initialized")
        result = await self.loop.run_in_executor(
            None,
            lambda: self.client.publish(topic, payload, qos=qos, retain=retain),
        )
        if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
            logger.debug("Published to %s", topic)
        else:
            logger.error("Publish failed to %s (rc=%d)", topic, result.rc)

    async def disconnect(self) -> None:
        """Gracefully disconnect."""
        if self.loop is not None:
            await self.loop.run_in_executor(None, self.client.disconnect)
            self.client.loop_stop()