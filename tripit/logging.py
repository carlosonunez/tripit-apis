"""
Logging module for TripIt APIs.
"""
import logging
import os
import sys


# pylint: disable=too-few-public-methods
class Log:
    """
    Behold! A log.
    """

    def __init__(self):
        """
        Creates or retrieves a logger, set its log level and configures it
        to write to stdout.
        """
        log_level = os.getenv("LOG_LEVEL").upper() if os.getenv("LOG_LEVEL") else "INFO"
        log = logging.getLogger(__name__)
        log.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s [%(filename)s::%(funcName)s:%(lineno)d]: %(message)s"
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        log.addHandler(handler)
        self.logger = log


logger = Log().logger
