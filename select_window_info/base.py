"""Base class for SelectWindowInfo"""

import abc
from dataclasses import dataclass
from typing import Iterable, Tuple

from pygetwindow import Win32Window  # type: ignore[import-untyped]


@dataclass
class WindowInfo:
    """Holder for window information"""

    title: str
    name: str
    passkey: str
    group: str | None
    window: Win32Window


class SelectWindowInfoBase(abc.ABC):
    """Base class for SelectWindowInfo"""

    @abc.abstractmethod
    def select(self, windows_info: Iterable[WindowInfo]) -> Tuple[Win32Window, str] | None:
        """Let user to pick the password from the list"""

    @classmethod
    def reserved(cls) -> None:
        """reserved"""
