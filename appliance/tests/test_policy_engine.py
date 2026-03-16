# appliance/tests/test_policy_engine.py

import pytest

from appliance.src.governance.policy_engine import PolicyEngine, check_autonomy_level


@pytest.mark.asyncio
async def test_approve_action() -> None:
    engine = PolicyEngine()
    approved, msg = await engine.approve_action("reset_interface")
    assert approved is True
    assert msg == "Approved"


@pytest.mark.asyncio
async def test_approve_action_denied_level() -> None:
    engine = PolicyEngine()
    engine.current_level = 2  # Set low level
    approved, msg = await engine.approve_action("reset_interface")
    assert approved is False
    assert "Insufficient" in msg


@pytest.mark.asyncio
async def test_approve_action_denied_whitelist() -> None:
    engine = PolicyEngine()
    approved, msg = await engine.approve_action("unknown")
    assert approved is False
    assert "whitelisted" in msg


@pytest.mark.asyncio
async def test_approve_action_denied_role() -> None:
    engine = PolicyEngine()
    engine.role = "viewer"  # Set bad role
    approved, msg = await engine.approve_action("reset_interface")
    assert approved is False
    assert "Unauthorized" in msg


def test_check_autonomy_level_numba() -> None:
    assert check_autonomy_level(3, 3) is True
    assert check_autonomy_level(2, 3) is False