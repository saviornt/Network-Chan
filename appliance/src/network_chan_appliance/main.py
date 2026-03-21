# appliance/src/main.py
"""Minimal entrypoint stub for Appliance container smoke test."""

import sys
import asyncio
from datetime import datetime, timezone

from network_chan_shared.utils.logging_factory import get_logger


logger = get_logger(__name__)


async def main() -> None:
    """Async main loop stub."""
    logger.info("Network-Chan Appliance starting (stub mode)")
    logger.info("UTC time: %s", datetime.now(timezone.utc).isoformat())

    # Simulate running forever
    while True:
        await asyncio.sleep(60)
        logger.debug("Heartbeat")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Appliance stub OK")
        sys.exit(0)

    asyncio.run(main())
