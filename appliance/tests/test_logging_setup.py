# appliance/tests/test_logging_setup.py
import pytest
import logging
import os
import time
import json
from datetime import datetime
from unittest.mock import patch, Mock
from appliance.src.logging_setup import JSONFormatter, setup_logging, prune_logs, logger as global_logger

@pytest.fixture
def temp_logs_dir(tmpdir):
    logs_dir = tmpdir.mkdir("logs")
    return str(logs_dir)

def test_setup_logging(temp_logs_dir):
    with patch('appliance.src.logging_setup.os.path.join', return_value=temp_logs_dir):
        with patch('appliance.src.logging_setup.config.log_level', 'DEBUG'):
            logger = setup_logging()
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
    handler = logger.handlers[0]
    assert isinstance(handler, logging.handlers.TimedRotatingFileHandler)
    assert isinstance(handler.formatter, JSONFormatter)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(temp_logs_dir, f'Log-{today}.log')
    assert os.path.exists(log_file)

def test_json_formatter():
    formatter = JSONFormatter()
    record = logging.LogRecord('name', logging.INFO, 'path', 10, 'Test message', (), None)
    record.created = time.time()
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert 'timestamp' in data
    assert data['level'] == 'INFO'
    assert data['message'] == 'Test message'
    assert data['module'] == 'unknown'
    assert data['funcName'] == '<unknown>'
    assert data['lineno'] == 10

def test_json_formatter_with_exc():
    formatter = JSONFormatter()
    record = logging.LogRecord('name', logging.ERROR, 'path', 10, 'Error msg', (), (ValueError, ValueError('test err'), None))
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert 'exc_info' in data
    assert 'ValueError: test err' in data['exc_info']

def test_prune_logs_no_dir(temp_logs_dir):
    with patch('appliance.src.logging_setup.os.path.exists', return_value=False):
        prune_logs()  # No crash

def test_prune_logs_empty_dir(temp_logs_dir):
    with patch('appliance.src.logging_setup.os.path.join', return_value=temp_logs_dir):
        prune_logs()  # No files, no issue

def test_prune_logs_prunes_old(temp_logs_dir):
    with patch('appliance.src.logging_setup.os.path.join', return_value=temp_logs_dir):
        # Mock old file
        old_file = os.path.join(temp_logs_dir, 'Log-2025-12-01.log')
        with open(old_file, 'w') as f:
            f.write('old')
        # Mock st_mtime < cutoff
        with patch('os.stat') as mock_stat:
            mock_stat_obj = Mock()
            mock_stat_obj.st_mtime = time.time() - 91*24*3600
            mock_stat.return_value = mock_stat_obj
            with patch('os.remove') as mock_remove:
                with patch('appliance.src.logging_setup.logger.info') as mock_log:
                    prune_logs()
                mock_remove.assert_called_once_with(old_file)
                mock_log.assert_called_once_with("Pruned old log: Log-2025-12-01.log")

def test_prune_logs_non_log_files(temp_logs_dir):
    with patch('appliance.src.logging_setup.os.path.join', return_value=temp_logs_dir):
        non_log = os.path.join(temp_logs_dir, 'not_log.txt')
        with open(non_log, 'w') as f:
            f.write('ignore')
        # Mock old mtime
        with patch('os.stat') as mock_stat:
            mock_stat_obj = Mock()
            mock_stat_obj.st_mtime = time.time() - 100*24*3600
            mock_stat.return_value = mock_stat_obj
            with patch('os.remove') as mock_remove:
                prune_logs()
                mock_remove.assert_not_called()  # Not pruned

def test_global_logger():
    assert global_logger.name == 'NetworkChanAppliance'
    assert len(global_logger.handlers) > 0