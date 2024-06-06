"""Base module for notification handling"""

import abc
import enum

from common.tools import is_debug_enabled
from updater.helpers import NotifyType


class MessageType(enum.Enum):
    """Types of messages"""

    DEBUG = enum.auto()
    INFO = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    CRITICAL = enum.auto()


class NotificationHandlerBase(abc.ABC):
    """Base class for notification handling"""

    @abc.abstractmethod
    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        """Show a message to the user"""

    def debug(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        return self.show(message=message, title=title, msg_type=MessageType.DEBUG)

    def info(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        return self.show(message=message, title=title, msg_type=MessageType.INFO)

    def warning(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        return self.show(message=message, title=title, msg_type=MessageType.WARNING)

    def error(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        return self.show(message=message, title=title, msg_type=MessageType.ERROR)

    def critical(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        return self.show(message=message, title=title, msg_type=MessageType.CRITICAL)

    @abc.abstractmethod
    def ask_yes_no(self, message: str, title: str = "") -> bool:
        """Ask the user a yes or no question"""

    def updater_callback(self, message: str, kind: NotifyType) -> bool:
        """Default user notify callback function."""

        if kind == NotifyType.QUESTION:
            return self.ask_yes_no(message)

        if kind == NotifyType.DEBUG and not is_debug_enabled():
            pass
        else:
            self.info(message)

        return True
