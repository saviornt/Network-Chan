# appliance/tests/test_anomaly.py
import pytest
import numpy as np
from unittest.mock import patch
from appliance.src.security.anomaly_detection import AnomalyDetector, detect_anomaly, main as anomaly_main

@pytest.mark.asyncio
async def test_check_anomalies() -> None:
    detector = AnomalyDetector()
    is_anomaly, msg = await detector.check_anomalies([95.0, 100.0])
    assert is_anomaly is True
    assert msg == "High CPU detected"

@pytest.mark.asyncio
async def test_check_anomalies_no_anomaly() -> None:
    detector = AnomalyDetector()
    is_anomaly, msg = await detector.check_anomalies([50.0, 60.0])
    assert is_anomaly is False
    assert msg == "Normal"

@pytest.mark.asyncio
async def test_check_anomalies_empty() -> None:
    detector = AnomalyDetector()
    is_anomaly, msg = await detector.check_anomalies([])
    assert is_anomaly is False
    assert msg == "Normal"

@pytest.mark.asyncio
async def test_check_anomalies_with_model_path() -> None:
    detector = AnomalyDetector(model_path='mock_path.onnx')  # Covers init branch
    assert detector.model_path == 'mock_path.onnx'
    is_anomaly, msg = await detector.check_anomalies([95.0])
    assert is_anomaly is True  # Logic still works
    assert msg == "High CPU detected"

def test_detect_anomaly_numba() -> None:
    values = np.array([95.0, 100.0])
    assert detect_anomaly(values) is True

def test_detect_anomaly_numba_no_anomaly() -> None:
    values = np.array([50.0])
    assert detect_anomaly(values) is False

def test_detect_anomaly_numba_empty() -> None:
    values = np.array([])
    assert detect_anomaly(values) is False

def test_detect_anomaly_numba_custom_threshold() -> None:
    values = np.array([85.0])
    assert detect_anomaly(values, threshold=80.0) is True
    assert detect_anomaly(values, threshold=90.0) is False  # Branch for > threshold

@pytest.mark.asyncio
async def test_main() -> None:
    with patch('builtins.print') as mock_print:  # Patch print for assert
        await anomaly_main()  # Covers main stub
        mock_print.assert_called_once_with((True, 'High CPU detected'))  # Matches mock metrics