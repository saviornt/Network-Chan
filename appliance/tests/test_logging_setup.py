# appliance/tests/test_logging_setup.py
import json  # For loads in tests
import logging
import logging.handlers  # For TimedRotatingFileHandler
import os
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from appliance.src.utils.logging_setup import (
    JSONFormatter,
    prune_logs,
    setup_logging,
)
from appliance.src.utils.logging_setup import (
    logger as global_logger,
)


@pytest.fixture
def temp_logs_dir() -> str:
    # Mock path; no real dir
    return "D:/Projects/Network-Chan/appliance/temp/logs"  # Use your path, but patch all ops


def test_setup_logging(temp_logs_dir: str) -> None:
    with patch("appliance.src.logging_setup.os.path.join", return_value=temp_logs_dir):
        with patch("appliance.src.logging_setup.os.makedirs") as mock_makedirs:
            with patch(
                "appliance.src.logging_setup.os.path.exists", return_value=False
            ):  # Force makedirs call
                with patch("appliance.src.logging_setup.config.log_level", "DEBUG"):
                    logger = setup_logging()
            mock_makedirs.assert_called_once_with(temp_logs_dir)
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
    handler = logger.handlers[0]
    assert isinstance(handler, logging.handlers.TimedRotatingFileHandler)
    assert isinstance(handler.formatter, JSONFormatter)
    # Mock log_file existence
    with patch("os.path.exists", return_value=True):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file: str = os.path.join(temp_logs_dir, f"Log-{today}.log")
        assert os.path.exists(log_file)  # Mocked true


def test_json_formatter() -> None:
    formatter = JSONFormatter()
    record = logging.LogRecord(
        "name", logging.INFO, "path", 10, "Test message", (), None
    )
    record.created = time.time()
    record.funcName = "<unknown>"  # Explicitly set to match code default
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["module"] == "path"
    assert data["funcName"] == "<unknown>"
    assert data["lineno"] == 10


def test_json_formatter_with_exc() -> None:
    formatter = JSONFormatter()
    record = logging.LogRecord(
        "name",
        logging.ERROR,
        "path",
        10,
        "Error msg",
        (),
        (ValueError, ValueError("test err"), None),
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert "exc_info" in data
    assert "ValueError: test err" in data["exc_info"]


def test_prune_logs_no_dir() -> None:
    with patch("appliance.src.logging_setup.os.path.exists", return_value=False):
        prune_logs()  # No crash


def test_prune_logs_empty_dir(temp_logs_dir: str) -> None:
    with patch("appliance.src.logging_setup.os.path.join", return_value=temp_logs_dir):
        with patch("os.listdir", return_value=[]):  # Mock empty
            prune_logs()  # No files, no issue


def test_prune_logs_prunes_old(temp_logs_dir: str) -> None:
    with patch("appliance.src.logging_setup.os.path.join", return_value=temp_logs_dir):
        with patch("os.listdir", return_value=["Log-2025-12-01.log"]):
            # Mock stat
            with patch("os.stat") as mock_stat:
                mock_stat_obj = Mock()
                mock_stat_obj.st_mtime = time.time() - 91 * 24 * 3600
                mock_stat.return_value = mock_stat_obj
                with patch("os.remove") as mock_remove:
                    with patch("appliance.src.logging_setup.logger.info") as mock_log:
                        prune_logs()
                    mock_remove.assert_called_once()
                    mock_log.assert_called_once()


def test_prune_logs_non_log_files(temp_logs_dir: str) -> None:
    with patch("appliance.src.logging_setup.os.path.join", return_value=temp_logs_dir):
        with patch("os.listdir", return_value=["not_log.txt"]):
            with patch("os.stat") as mock_stat:
                mock_stat_obj = Mock()
                mock_stat_obj.st_mtime = time.time() - 100 * 24 * 3600
                mock_stat.return_value = mock_stat_obj
                with patch("os.remove") as mock_remove:
                    prune_logs()
                    mock_remove.assert_not_called()  # Not pruned


def test_global_logger() -> None:
    assert global_logger.name == "NetworkChanAppliance"
    assert len(global_logger.handlers) > 0


def test_prune_logs_permission_error(temp_logs_dir: str) -> None:
    with patch("appliance.src.logging_setup.os.path.join", return_value=temp_logs_dir):
        with patch("os.listdir", return_value=["Log-2025-12-01.log"]):
            with patch("os.stat") as mock_stat:
                mock_stat_obj = Mock()
                mock_stat_obj.st_mtime = time.time() - 91 * 24 * 3600
                mock_stat.return_value = mock_stat_obj
                with patch(
                    "os.remove", side_effect=PermissionError("Mock deny")
                ) as mock_remove:
                    with patch(
                        "appliance.src.logging_setup.logger.warning"
                    ) as mock_warn:
                        prune_logs()
                    mock_remove.assert_called_once()
                    mock_warn.assert_called_once()
