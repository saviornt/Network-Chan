"""Utility to detect if the current runtime is a Raspberry Pi (edge/Appliance mode).

Used by logging factory, settings, and other components to enable Pi-specific
behavior (e.g. lower verbosity, different paths, edge context in logs).

Detection is cached for performance — file I/O only happens once.
"""

from __future__ import annotations

import os
import platform
from functools import cache
from typing import Final

from ..utils.logging_factory import get_logger

logger = get_logger("device_detection")


@cache  # ← caches result forever (safe: hardware doesn't change at runtime)
def is_edge_device() -> bool:
    """Detect whether we are running on a Raspberry Pi (Appliance / edge mode).

    Detection priority (ordered by reliability):
    1. OS/distribution name contains 'Raspbian' or 'Raspberry Pi OS'
    2. Machine/hardware identifier is ARM + Pi-specific model string in files
    3. Presence of Raspberry Pi hallmark paths (/proc/device-tree/model, etc.)

    Returns:
        bool: True if likely running on Raspberry Pi, False otherwise.

    Note:
        Result is cached (@cache) — file I/O occurs only on first call.
    """
    # Quick OS filter — non-Linux can't be Pi in our context
    if platform.system().lower() != "linux":
        logger.debug("Non-Linux platform detected", system=platform.system())
        return False

    # 1. Most reliable: check /etc/os-release PRETTY_NAME
    dist_name = ""
    os_release_path: Final = "/etc/os-release"
    if os.path.isfile(os_release_path):
        try:
            with open(os_release_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        dist_name = line.split("=", 1)[1].strip().strip('"').lower()
                        break
        except (PermissionError, OSError) as exc:
            logger.warning(
                "Cannot read /etc/os-release",
                path=os_release_path,
                exc_info=exc,
            )

    if "raspbian" in dist_name or "raspberry pi os" in dist_name:
        logger.debug("Detected Raspberry Pi OS via /etc/os-release", dist=dist_name)
        return True

    # 2. Architecture filter — only ARM platforms can be Pi
    machine = platform.machine().lower()
    if "arm" not in machine and "aarch64" not in machine:
        logger.debug("Non-ARM architecture", machine=machine)
        return False

    # 3. Pi-specific file/model checks
    pi_model_indicators = [
        "/proc/device-tree/model",
        "/sys/firmware/devicetree/base/model",
        "/proc/cpuinfo",
    ]

    for path in pi_model_indicators:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read().lower()
                    if "raspberry pi" in content:
                        logger.debug(
                            "Detected Raspberry Pi via model string",
                            path=path,
                            snippet=content[:80] + "...",
                        )
                        return True
            except (PermissionError, OSError) as exc:
                logger.warning(
                    "Cannot read Pi indicator file",
                    path=path,
                    exc_info=exc,
                )

    # 4. Last-resort: existence of common Pi pseudo-files (OR logic)
    pi_hallmarks = [
        "/proc/device-tree",
        "/sys/class/thermal/thermal_zone0",
        "/sys/firmware/devicetree",
    ]

    hallmark_hits = sum(1 for p in pi_hallmarks if os.path.exists(p))

    if hallmark_hits >= 2:  # at least two strong indicators
        logger.debug(
            "Detected Raspberry Pi via hallmark paths",
            hits=hallmark_hits,
            paths=pi_hallmarks,
        )
        return True

    logger.debug("No Raspberry Pi indicators found")
    return False


# Public API
__all__ = ["is_edge_device"]
