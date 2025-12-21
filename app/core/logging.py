from __future__ import annotations

import logging
import sys
from app.core.config import settings


def configure_logging() -> None:
    # Simple, production-friendly baseline. Can upgrade to JSON logs later.
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
