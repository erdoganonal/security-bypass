"""This module configures the logger for the application."""

import logging

logger = logging.getLogger(__name__)


def initialize() -> None:
    """Setup and initialize the logger."""

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s")

    file_handler = logging.FileHandler("security_bypass.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.setLevel(logging.DEBUG)

    logger.info("Logger is configured and ready to use.")
