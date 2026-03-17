"""Global pytest fixtures and config."""

from unittest.mock import patch

import pytest
from shared.src.config.shared_settings import Settings


@pytest.fixture(autouse=True)
def mock_settings():  # noqa: ANN201
    """Mock Settings singleton for all tests with safe defaults."""
    test_settings = Settings(
        SECRET_KEY="test-secret-key",
        JWT_SECRET="test-jwt-secret",
        PASSWORD_SALT="test-salt",
        ADMIN_PASSWORD_HASH="test-bcrypt-hash",
        # add other required fields if any
        # ... other defaults as needed ...
    )
    with patch("src.config.settings.settings", test_settings):
        yield
