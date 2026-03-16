# appliance/src/telemetry_ingest.py

import asyncio
import random  # Mock data; replace with psutil/PySNMP later
from typing import Any

import numpy as np  # Add for arrays
from numba import jit  # type: ignore

from shared.src.db.db_schema import init_db  # Shared dep


@jit(nopython=True)  # type: ignore[misc]
def compute_metric_average(values: np.ndarray) -> float:  # Numba for perf in aggregations
    if values.size == 0:
        return 0.0
    return np.sum(values) / values.size


class TelemetryIngestor:
    def __init__(self, db_path: str = "network_chan.db") -> None:
        self.db_path: str = db_path
        self.metrics: list[dict[str, Any]] = []  # In-memory buffer

    async def collect_metrics(self, devices: list[str]) -> None:
        loop = asyncio.get_running_loop()
        tasks: list[asyncio.Task[dict[str, Any]]] = [loop.create_task(self._scrape_device(device)) for device in devices]
        results: list[dict[str, Any] | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if not isinstance(result, BaseException):
                self.metrics.append(result)  # type: ignore[arg-type]
        # Compute avg with Numba
        if self.metrics:
            values_list: list[float] = [m["cpu"] for m in self.metrics if "cpu" in m]
            values: np.ndarray = np.array(values_list)
            avg: float = compute_metric_average(values)
            print(f"Mock average CPU: {avg}")

    async def _scrape_device(self, device: str) -> dict[str, Any]:
        await asyncio.sleep(0.1)  # Simulate async I/O delay
        return {
            "device": device,
            "cpu": random.uniform(0, 100),
            "bandwidth": random.randint(0, 1000),
            "timestamp": asyncio.get_event_loop().time()
        }

    async def persist_metrics(self) -> None:
        await init_db(self.db_path)  # From shared
        # Stub: Insert to DB async (use aiosqlite later for full async DB)
        await asyncio.sleep(0)  # Placeholder
        print(f"Mock persisted {len(self.metrics)} metrics")


# Usage stub (run async)
async def main() -> None:
    ingestor = TelemetryIngestor()
    await ingestor.collect_metrics(["router", "switch"])
    await ingestor.persist_metrics()


if __name__ == "__main__":
    asyncio.run(main())