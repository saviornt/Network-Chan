"""Central MQTT topic definitions and patterns."""

TELEMETRY_PREFIX = "network-chan/telemetry/"
CONTROL_PREFIX = "network-chan/control/"


def telemetry_topic(device_id: str) -> str:
    return f"{TELEMETRY_PREFIX}{device_id}"


def command_topic() -> str:
    return f"{CONTROL_PREFIX}commands"
