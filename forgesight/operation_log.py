"""Persistent rotating operation log for the Jetson live service.

record.json and advice_report.json already carry typed per-inspection
results; this log ties a whole run together across requests, worker
crashes, cold fallbacks and restarts, so a failure can be traced end to
end without guessing. It records failures that previously disappeared
silently (for example a worker respawn raising in a background thread).
It never changes decisions, grades or stored evidence, and it writes no
image bytes or model data, only operational metadata.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time

LOGGER_NAME = "forgesight.operations"
_FORMAT = "%(asctime)sZ %(levelname)s %(message)s"


def operation_logger():
    return logging.getLogger(LOGGER_NAME)


def configure_operation_log(log_dir, *, max_bytes=1024 * 1024, backups=5,
                            level=logging.INFO):
    """Attach one rotating file handler plus stderr; safe to call twice."""
    logger = operation_logger()
    logger.setLevel(level)
    logger.propagate = False
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = (log_dir / "forgesight-operations.log").resolve()
    formatter = logging.Formatter(_FORMAT)
    formatter.converter = time.gmtime
    for handler in logger.handlers:
        if (isinstance(handler, RotatingFileHandler)
                and Path(handler.baseFilename) == target):
            return logger
    handler = RotatingFileHandler(target, maxBytes=max_bytes, backupCount=backups,
                                  encoding="utf-8")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if not any(isinstance(existing, logging.StreamHandler)
               and not isinstance(existing, RotatingFileHandler)
               for existing in logger.handlers):
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        logger.addHandler(stream)
    return logger
