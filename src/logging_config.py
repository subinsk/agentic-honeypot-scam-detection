"""
Production-grade logging: structured JSON for aggregators, optional file rotation,
request-scoped context (request_id), and consistent logger naming.
"""
import json
import logging
import sys
from contextvars import ContextVar
from logging.handlers import TimedRotatingFileHandler
from typing import Any

from src.config import settings

# Request-scoped context: set by middleware, included in all log records in that request.
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_session_id_ctx: ContextVar[str | None] = ContextVar("session_id", default=None)

LOG_LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON for production (ELK, Datadog, etc.)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt or "%Y-%m-%dT%H:%M:%S.000Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Include request/session context when set
        request_id = _request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id
        session_id = _session_id_ctx.get()
        if session_id:
            payload["session_id"] = session_id
        # Extra fields passed via logger.info(..., extra={...})
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            for k, v in record.extra_fields.items():
                if k not in payload:
                    payload[k] = v
        return json.dumps(payload, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable format for local development."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = []
        request_id = _request_id_ctx.get()
        if request_id:
            extras.append(f"request_id={request_id}")
        session_id = _session_id_ctx.get()
        if session_id:
            extras.append(f"session_id={session_id}")
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            for k, v in record.extra_fields.items():
                extras.append(f"{k}={v}")
        if extras:
            base += " | " + " ".join(extras)
        return base


def _install_extra_fields(record: logging.LogRecord) -> None:
    """Merge 'extra' dict into record.extra_fields so formatters can use it."""
    if not hasattr(record, "extra_fields"):
        record.extra_fields = {}
    _standard = frozenset((
        "name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno",
        "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated",
        "stack_info", "exc_info", "message", "taskName", "extra_fields",
        "thread", "threadName", "exc_text", "sinfo",
    ))
    for k, v in record.__dict__.items():
        if k not in _standard:
            record.extra_fields[k] = v


def setup_logging() -> None:
    """
    Configure root logging once at startup. Idempotent: safe to call multiple times.
    Uses settings: log_level, log_format, log_file.
    """
    root = logging.getLogger("honeypot")
    if root.handlers:
        return  # already configured

    # Install record factory first so all logs (including initial) get extra_fields
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        _install_extra_fields(record)
        return record

    logging.setLogRecordFactory(record_factory)

    root.propagate = False  # avoid duplicate logs to Python root
    level_name = (getattr(settings, "log_level", None) or "INFO").upper()
    level = LOG_LEVELS.get(level_name, logging.INFO)
    root.setLevel(level)

    fmt = (getattr(settings, "log_format", None) or "json").lower()
    if fmt == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = ConsoleFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Optional file with daily rotation
    log_file = getattr(settings, "log_file", None)
    if log_file:
        try:
            file_handler = TimedRotatingFileHandler(
                log_file,
                when="midnight",
                backupCount=30,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(JsonFormatter())
            root.addHandler(file_handler)
        except OSError as e:
            root.warning("Could not add log file handler: %s", e)

    root.info("logging_initialized", extra={"log_level": level_name, "log_format": fmt, "log_file": bool(log_file)})


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under 'honeypot' so all logs use the same config."""
    if not name.startswith("honeypot"):
        name = f"honeypot.{name}"
    return logging.getLogger(name)


def set_request_context(request_id: str | None = None, session_id: str | None = None) -> None:
    """Set request-scoped context so all logs in this request include these fields."""
    if request_id is not None:
        _request_id_ctx.set(request_id)
    if session_id is not None:
        _session_id_ctx.set(session_id)


def clear_request_context() -> None:
    """Clear request context (e.g. at end of request)."""
    try:
        _request_id_ctx.set(None)
    except LookupError:
        pass
    try:
        _session_id_ctx.set(None)
    except LookupError:
        pass
