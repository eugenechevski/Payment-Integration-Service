import logging
import sys

from app.core.config import settings


def configure_logging() -> logging.Logger:
    log = logging.getLogger("payment_service")
    if log.handlers:
        return log

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    log.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    log.addHandler(handler)
    log.propagate = False
    return log


logger = configure_logging()
