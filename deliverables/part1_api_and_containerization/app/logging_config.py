import json
import logging
import time
import warnings

from app.context import correlation_id_var

# Standard LogRecord attributes that should not be forwarded as extra fields.
_RESERVED_ATTRS = frozenset(
    {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


class JsonFormatter(logging.Formatter):
    """Formats every log record as a single-line JSON object.

    Standard fields always present:
        timestamp   — ISO-8601 UTC
        level       — DEBUG / INFO / WARNING / ERROR / CRITICAL
        logger      — dotted module name
        message     — formatted log message
        correlation_id — current request's ID (from ContextVar, "-" outside a request)

    Any kwargs passed via ``extra={}`` are merged in at the top level.
    Exception tracebacks are included as ``exc_info`` when present.
    """

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        log_obj: dict = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "correlation_id": correlation_id_var.get(),
        }

        # Merge extra fields added by callers via extra={...}
        for key, val in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                log_obj[key] = val

        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


def setup_logging(level: str | int = logging.INFO) -> None:
    """Configure root logger to emit structured JSON to stdout."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.root.setLevel(level)
    logging.root.handlers = [handler]

    # Suppress a spurious Pydantic V2 / LangChain compatibility warning that fires
    # when MemorySaver serialises AIMessage objects whose `parsed` field contains a
    # structured-output Pydantic model.  The warning is harmless — serialisation
    # succeeds and the value is preserved — but it pollutes the log stream.
    warnings.filterwarnings(
        "ignore", message=".*PydanticSerializationUnexpectedValue.*"
    )
