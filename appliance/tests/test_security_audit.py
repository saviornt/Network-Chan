# appliance/tests/test_security_audit.py
import pytest
import numpy as np
from unittest.mock import patch, Mock
from typing import Any
from appliance.src.security.security_audit import SecurityAudit, compute_audit_score

@pytest.mark.asyncio
async def test_perform_audit_pass() -> None:
    audit = SecurityAudit()
    with patch('random.uniform', return_value=50.0):  # Mock low scores
        success, msg = await audit.perform_audit()
        assert success is True
        assert "Passed" in msg

@pytest.mark.asyncio
async def test_perform_audit_fail() -> None:
    audit = SecurityAudit()
    with patch('random.uniform', return_value=90.0):  # Mock high scores
        success, msg = await audit.perform_audit()
        assert success is False
        assert "High risk" in msg

@pytest.mark.asyncio
async def test_schedule_audit() -> None:
    audit = SecurityAudit(off_peak_hour=12)  # Mock current hour for test
    class StopLoop(Exception):
        pass

    async def mock_sleep(*args: Any):
        raise StopLoop  # Break after one iteration

    with patch('time.localtime') as mock_time:
        mock_time_obj = Mock(tm_hour=12)  # Force off-peak
        mock_time.return_value = mock_time_obj
        with patch('asyncio.sleep', mock_sleep):
            with patch.object(audit, 'perform_audit', return_value=(True, "Passed")) as mock_audit:
                with pytest.raises(StopLoop):
                    await audit.schedule_audit()
        mock_audit.assert_called_once()  # Called since off-peak

def test_compute_audit_score_numba() -> None:
    assert compute_audit_score(np.array([50.0, 60.0])) == 55.0
    assert compute_audit_score(np.array([])) == 0.0
    assert compute_audit_score(np.array([90.0])) == 90.0