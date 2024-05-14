"""Base class for SelectWindowInfo"""

import abc
from dataclasses import dataclass
from typing import Iterable

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
    def select(self, windows_info: Iterable[WindowInfo]) -> WindowInfo | None:
        """Let user to pick the password from the list"""

    @classmethod
    def reserved(cls) -> None:
        """reserved"""
