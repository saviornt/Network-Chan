"""TLS utility functions for Network-Chan.

Currently focused on MQTT client TLS context creation, but designed to be
extended for other components (Omada API, FastAPI server, etc.) in the future.

TODO: When another integration needs TLS (e.g. Omada HTTPS client, dashboard server),
      consider extracting shared TLSSettings model and validation logic here.
"""

import ssl
from pathlib import Path
from typing import Optional

from ..settings.mqtt_settings import mqtt_settings


def create_mqtt_tls_context() -> Optional[ssl.SSLContext]:
    """
    Creates an SSLContext for secure MQTT connections based on mqtt_settings.

    Returns:
        ssl.SSLContext or None if TLS is disabled.

    Raises:
        FileNotFoundError: If specified certificate files do not exist.
        ssl.SSLError: If certificate loading fails.
    """
    if not mqtt_settings.use_tls:
        return None

    ctx = ssl.create_default_context()

    # Custom CA certificate (overrides system store if provided)
    if mqtt_settings.ca_cert_path:
        ca_path = Path(mqtt_settings.ca_cert_path).expanduser().resolve()
        if not ca_path.is_file():
            raise FileNotFoundError(f"CA certificate not found: {ca_path}")
        ctx.load_verify_locations(cafile=str(ca_path))

    # Mutual TLS (client certificate + key)
    if mqtt_settings.client_cert_path and mqtt_settings.client_key_path:
        cert_path = Path(mqtt_settings.client_cert_path).expanduser().resolve()
        key_path = Path(mqtt_settings.client_key_path).expanduser().resolve()
        if not cert_path.is_file() or not key_path.is_file():
            raise FileNotFoundError("Client certificate/key files missing")
        ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

    return ctx
