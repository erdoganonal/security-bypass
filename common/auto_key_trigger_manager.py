"""This module contains the AutoKeyTriggerManager class."""

import time
from typing import Dict

from config.config import WindowData


class AutoKeyTriggerManager:
    """manage the triggered windows and their timeouts."""

    TIMEOUT_SECS = 30

    def __init__(self) -> None:
        self.__windows_data: Dict[WindowData, float] = {}

    def is_already_triggered(self, window_data: WindowData) -> bool:
        """return whether the given window is already triggered or not."""
        self.clear_timeout_triggered()
        return window_data in self.__windows_data

    def clear_timeout_triggered(self) -> None:
        """clear the triggered windows that are timed out."""
        now = time.time()
        self.__windows_data = {
            window_hwnd: triggered_time
            for window_hwnd, triggered_time in self.__windows_data.items()
            if now - triggered_time < self.TIMEOUT_SECS
        }

    def add_triggered(self, window_data: WindowData) -> None:
        """add the given window as a triggered window."""
        self.__windows_data[window_data] = time.time()
