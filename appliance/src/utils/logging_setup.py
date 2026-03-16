# appliance/src/logging_setup.py (updated for JSON, rotating files, prune)
import json
import logging
import os
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Any

from shared.src.config.settings import app_settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.msg,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging(level: str | None = None) -> logging.Logger:
    level = level or app_settings.log_level  # From .env
    logger = logging.getLogger("NetworkChanAppliance")
    logger.setLevel(getattr(logging, level.upper()))

    # Create logs dir if not exists
    logs_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Daily rotating file: Log-YYYY-MM-DD.log
    today = datetime.now().strftime("%Y-%m-%d")
    log_file: str = os.path.join(logs_dir, f"Log-{today}.log")
    handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=90)  # Keeps 90 days
    handler.setFormatter(JSONFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)

    return logger


def prune_logs() -> None:
    """Prune logs older than config.prune_days."""
    logs_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    if not os.path.exists(logs_dir):
        return

    now = time.time()
    cutoff = now - (int(app_settings.prune_days) * 24 * 3600)  # Days to seconds

    for file in os.listdir(logs_dir):
        if file.startswith("Log-") and file.endswith(".log"):
            file_path: str = os.path.join(logs_dir, file)
            try:
                if os.stat(file_path).st_mtime < cutoff:
                    os.remove(file_path)
                    logger.info(f"Pruned old log: {file}")
            except (OSError, PermissionError):
                logger.warning(f"Failed to prune {file}: Permission denied or OS error")


logger = setup_logging()  # Global instance

# Usage in other files: from .logging_setup import logger; logger.info(...)
# Call prune_logs() periodically, e.g., in main.py startup or cron script