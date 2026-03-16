# appliance/tests/test_remediation_mockup.py
import pytest
import numpy as np
from appliance.src.remediation.remediation_mockup import RemediationDaemon, simulate_rollback

@pytest.mark.asyncio
async def test_execute_action_success() -> None:
    daemon = RemediationDaemon()
    success, msg = await daemon.execute_action('reset_interface', {'interface': 'eth0'})
    assert success is True
    assert "Interface reset" in msg
    assert 'reset_interface' in daemon.state_snapshot

@pytest.mark.asyncio
async def test_execute_action_unknown() -> None:
    daemon = RemediationDaemon()
    success, msg = await daemon.execute_action('unknown', {})
    assert success is False
    assert "Unknown action" in msg
    assert 'unknown' not in daemon.state_snapshot  # Not added if unknown

@pytest.mark.asyncio
async def test_rollback_action() -> None:
    daemon = RemediationDaemon()
    daemon.state_snapshot['test'] = np.array([1.0, 2.0])
    await daemon.rollback_action('test')
    assert 'test' not in daemon.state_snapshot  # Removed after rollback

@pytest.mark.asyncio
async def test_rollback_action_no_snapshot() -> None:
    daemon = RemediationDaemon()
    await daemon.rollback_action('missing')  # No crash

def test_simulate_rollback_numba() -> None:
    state = np.array([1.0, 2.0])
    restored = simulate_rollback(state)
    np.testing.assert_array_equal(restored, np.array([-1.0, -2.0]))
    assert simulate_rollback(np.array([])).size == 0  # Empty