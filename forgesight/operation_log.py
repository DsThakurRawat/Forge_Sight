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
import re
import time
import traceback

LOGGER_NAME = "forgesight.operations"
_FORMAT = "%(asctime)sZ %(levelname)s %(message)s"

# Operational text can carry exception messages and child-process stderr.
# Those are useful for diagnosis but must never persist credentials and
# must stay bounded so one noisy child cannot fill the rotation budget.
# Bounded redaction policy: credential-shaped assignments (including env-var
# style prefixes like API_TOKEN and quoted multiword values), Bearer tokens,
# URL userinfo, and PEM blocks. This is a policy for known shapes, not a
# guarantee that every possible secret form is caught; the first defense is
# never logging request bodies, image bytes or model data at all.
_ASSIGNMENT = re.compile(
    r"(?i)(?<![A-Za-z0-9])"
    r"([A-Z0-9_-]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API[-_]?KEY|AUTHORIZATION"
    r"|CREDENTIAL)[A-Z0-9_-]*)"
    r"(\s*[:=]\s*)"
    r"(\"[^\"]*\"|'[^']*'|\S+)")
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_URL_USERINFO = re.compile(r"://[^/\s:@]+:[^/\s@]+@")
_PEM_BLOCK = re.compile(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", re.DOTALL)
MAX_FIELD_CHARS = 500
MAX_TRACEBACK_CHARS = 4000


def scrub(text, *, limit=MAX_FIELD_CHARS):
    """Redact the known credential shapes above and bound a log field's length."""
    text = _PEM_BLOCK.sub("[redacted-pem]", str(text))
    text = _URL_USERINFO.sub("://[redacted]@", text)
    text = _BEARER.sub("Bearer [redacted]", text)
    text = _ASSIGNMENT.sub(lambda match: match.group(1) + match.group(2)
                           + "[redacted]", text)
    if len(text) > limit:
        text = text[:limit] + "...[truncated]"
    return text


class _ScrubFilter(logging.Filter):
    """Apply scrub() to every record this logger emits, tracebacks included."""

    def filter(self, record):
        # Render first, then scrub: a secret passed as a separate %-arg would
        # survive template-only scrubbing because the key and value sit in
        # different fields.
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        record.msg = scrub(message)
        record.args = ()
        if record.exc_info:
            record.exc_text = scrub(
                "".join(traceback.format_exception(*record.exc_info)),
                limit=MAX_TRACEBACK_CHARS)
            record.exc_info = None
        return True


def operation_logger():
    return logging.getLogger(LOGGER_NAME)


def configure_operation_log(log_dir, *, max_bytes=1024 * 1024, backups=5,
                            level=logging.INFO):
    """Attach one rotating file handler plus stderr; safe to call twice.

    Logging is diagnostic only: if the log directory cannot be created or
    the file opened (full disk, read-only mount, permissions), the service
    degrades to stderr with an explicit warning instead of failing to
    start. Every handler output is passed through scrub().
    """
    logger = operation_logger()
    logger.setLevel(level)
    logger.propagate = False
    if not any(isinstance(existing, _ScrubFilter) for existing in logger.filters):
        logger.addFilter(_ScrubFilter())
    formatter = logging.Formatter(_FORMAT)
    formatter.converter = time.gmtime
    if not any(isinstance(existing, logging.StreamHandler)
               and not isinstance(existing, RotatingFileHandler)
               for existing in logger.handlers):
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        logger.addHandler(stream)
    try:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        target = (log_dir / "forgesight-operations.log").resolve()
        for handler in logger.handlers:
            if (isinstance(handler, RotatingFileHandler)
                    and Path(handler.baseFilename) == target):
                return logger
        handler = RotatingFileHandler(target, maxBytes=max_bytes,
                                      backupCount=backups, encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except OSError as error:
        logger.warning("Persistent operation log unavailable; continuing "
                       "with stderr only: %s", scrub(error))
    return logger
