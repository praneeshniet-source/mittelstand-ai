
import json
import logging
from datetime import datetime, timezone

from config.settings import settings


class JSONFormatter(logging.Formatter):
    """Format application logs as structured JSON."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_entry)


def configure_logging():
    """Configure application-specific structured logging."""

    log_level = logging.DEBUG if settings.debug else logging.INFO

    app_logger = logging.getLogger("mittelstand_ai")
    app_logger.setLevel(log_level)
    app_logger.propagate = False

    # Prevent duplicate handlers if configuration runs more than once.
    if not any(
        getattr(handler, "_mittelstand_ai_json", False)
        for handler in app_logger.handlers
    ):
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        handler._mittelstand_ai_json = True
        app_logger.addHandler(handler)
