"""Factory for creating secure, retry-enabled MQTT clients in Network-Chan.

Uses asyncio-mqtt (preferred async library) with TLS support, certificate validation,
authentication, and retry logic via @aretry_network decorator.

Exports:
    create_secure_mqtt_client() -> AsyncMQTTClient
"""

from __future__ import annotations

from asyncio_mqtt import Client as AsyncMQTTClient
from typing import Optional

from shared.src.models.mqtt_model import MqttClientOptions
from shared.src.utils.retry import aretry_network
from shared.src.utils.logging_factory import get_logger
from shared.src.utils.tls_utils import create_mqtt_tls_context

logger = get_logger(__name__)


@aretry_network
async def create_secure_mqtt_client(
    options: Optional[MqttClientOptions] = None,
) -> AsyncMQTTClient:
    """
    Creates a secure MQTT client using provided or default options.
    """
    if options is None:
        options = MqttClientOptions.from_settings()

    logger.info(
        "Creating secure MQTT client",
        hostname=options.hostname,
        port=options.port,
        tls=options.tls_enabled,
        client_id=options.client_id,
    )

    tls_context = create_mqtt_tls_context()  # from tls_utils.py

    client = AsyncMQTTClient(
        hostname=options.hostname,
        port=options.port,
        client_id=options.client_id,
        tls_context=tls_context,
        username=options.username,
        password=options.password,
        keepalive=options.keepalive,
    )

    logger.debug(
        "MQTT client factory complete",
        client_id=options.client_id,
        broker=options.hostname,
    )
    return client
