# ================================
# File: app/core/logger.py
# Path: backend/app/core/logger.py
# ================================

import logging

LOGGER_NAME = "legal-ai"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger  # 이미 설정됨

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    handler.setFormatter(logging.Formatter(fmt))

    logger.addHandler(handler)
    return logger


logger = setup_logging()
