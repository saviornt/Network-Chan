"""Unit tests for core.exceptions module."""

from shared.src.core.exceptions import (
    InvalidRLStateError,
    NetworkChanError,
    PolicyViolationError,
    ValidationError,
)


def test_base_exception_has_attributes():
    exc = NetworkChanError(
        "Test error", error_code="TEST-001", details={"key": "value"}
    )
    assert exc.message == "Test error"
    assert exc.error_code == "TEST-001"
    assert exc.details == {"key": "value"}


def test_policy_violation_error_formats_message():
    exc = PolicyViolationError(
        message="",
        action="change_channel",
        current_mode=2,
        required_mode=4,
        device="AP-01",
    )
    assert "change_channel" in str(exc)
    assert "mode 2" in str(exc)
    assert "needs >= 4" in str(exc)
    assert exc.details["device"] == "AP-01"


def test_exception_hierarchy():
    exc = InvalidRLStateError("Bad state")
    assert isinstance(exc, NetworkChanError)
    assert isinstance(exc, ValidationError)
    assert not isinstance(exc, PolicyViolationError)
