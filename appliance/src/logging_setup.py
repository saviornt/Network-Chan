# appliance/src/logging_setup.py

import logging
from typing import Optional, Dict, Any
from logging.handlers import TimedRotatingFileHandler
import json
import os
import time
from datetime import datetime
from .config import config

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'message': record.msg,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        if record.exc_info:
            log_record['exception_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(level: Optional[str] = None) -> logging.Logger:
    level = level or config.log_level  # From .env
    logger = logging.getLogger(f'NetworkChanAppliance: {__name__}')
    logger.setLevel(getattr(logging, level.upper()))

    # Create logs dir if not exists
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')  # appliance/logs/
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Daily rotating file: Log-YYYY-MM-DD.log
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(logs_dir, f'Log-{today}.log')
    handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=int(config.log_prune_timeframe))  # Keeps 90 days
    handler.setFormatter(JSONFormatter(datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(handler)

    return logger

def prune_logs() -> None:
    """Prune logs older than 90 days."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    logger = setup_logging()
    if not os.path.exists(logs_dir):
        return

    now = time.time()
    cutoff = now - (int(config.log_prune_timeframe) * 24 * 3600)  # 90 days in seconds

    for file in os.listdir(logs_dir):
        if file.startswith('Log-') and file.endswith('.log'):
            file_path = os.path.join(logs_dir, file)
            try:
                if os.stat(file_path).st_mtime < cutoff:
                    os.remove(file_path)
                    logger.info(f"Pruned old log: {file}")
            except (OSError, PermissionError):
                logger.warning(f"Failed to prune {file}: Permission denied or OS error")

logger = setup_logging()  # Global instance

# Usage in other files: from .logging_setup import logger; logger.info(...)
# Call prune_logs() periodically, e.g., in main.py startup or cron script
