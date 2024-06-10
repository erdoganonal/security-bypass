"""Base class for SelectWindowInfo"""

import abc
from dataclasses import dataclass
from typing import Sequence

from pygetwindow import Win32Window  # type: ignore[import-untyped]

from config.config import WindowData


@dataclass
class WindowInfo:
    """Holder for window information"""

    window: Win32Window
    window_data: WindowData


class SelectWindowInfoBase(abc.ABC):
    """Base class for SelectWindowInfo"""

    @abc.abstractmethod
    def select(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> WindowData | None:
        """Let user to pick the password from the list"""

    @property
    @abc.abstractmethod
    def supports_thread(self) -> bool:
        """return the information that the class supports running in the thread"""
