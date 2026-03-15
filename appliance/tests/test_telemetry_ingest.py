# appliance/tests/test_telemetry_ingest.py

from typing import Dict, Any
from unittest.mock import patch
import pytest
import numpy as np  # For mocks if needed
from appliance.src.telemetry.telemetry_ingest import TelemetryIngestor, compute_metric_average

@pytest.mark.asyncio
async def test_collect_metrics() -> None:
    ingestor = TelemetryIngestor()
    await ingestor.collect_metrics(['test_device'])
    assert len(ingestor.metrics) == 1
    metric = ingestor.metrics[0]
    assert 'device' in metric and metric['device'] == 'test_device'
    assert 'cpu' in metric and 0 <= metric['cpu'] <= 100
    assert 'bandwidth' in metric and isinstance(metric['bandwidth'], int)

@pytest.mark.asyncio
async def test_persist_metrics() -> None:
    ingestor = TelemetryIngestor(db_path=':memory:')  # In-memory DB for test
    ingestor.metrics = [{'cpu': 50.0}]  # Mock data
    await ingestor.persist_metrics()  # Just checks no crash; expand with DB asserts later
    # Add branch: Empty metrics
    ingestor.metrics = []
    await ingestor.persist_metrics()

def test_compute_metric_average_numba() -> None:
    assert compute_metric_average(np.array([1.0, 2.0, 3.0])) == 2.0
    assert compute_metric_average(np.array([])) == 0.0  # Edge case

@pytest.mark.asyncio
async def test_collect_metrics_empty_devices() -> None:
    ingestor = TelemetryIngestor()
    await ingestor.collect_metrics([])
    assert len(ingestor.metrics) == 0

@pytest.mark.asyncio
async def test_collect_metrics_with_exception() -> None:
    async def failing_scrape(device: str) -> Dict[str, Any]:
        raise ValueError("Mock scrape fail")
    ingestor = TelemetryIngestor()
    with patch.object(ingestor, '_scrape_device', failing_scrape):
        await ingestor.collect_metrics(['test'])
    assert len(ingestor.metrics) == 0  # Exception skipped