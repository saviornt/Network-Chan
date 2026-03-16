# appliance/src/anomaly_detection.py

import asyncio

import numpy as np  # Dep later; mock with lists for now
from numba import jit  # type: ignore


@jit(nopython=True)  # type: ignore[misc]
def detect_anomaly(values: np.ndarray, threshold: float = 90.0) -> bool:
    if values.size == 0:
        return False  # Handle empty gracefully
    mean = np.sum(values) / values.size
    return mean > threshold


class AnomalyDetector:
    def __init__(self, model_path: str | None = None) -> None:
        self.model_path: str | None = model_path  # For TinyML load later

    async def check_anomalies(self, metrics: list[float]) -> tuple[bool, str]:
        await asyncio.sleep(0)  # Async yield for concurrency
        values: np.ndarray = np.array(metrics)  # Convert to array
        is_anomaly: bool = detect_anomaly(values)
        return is_anomaly, "High CPU detected" if is_anomaly else "Normal"


# Usage stub
async def main() -> None:
    detector = AnomalyDetector()
    result: tuple[bool, str] = await detector.check_anomalies([85.0, 95.0, 100.0])
    print(result)


if __name__ == "__main__":
    asyncio.run(main())