"""Base module for notification handling"""

import abc
import enum

from common.tools import is_debug_enabled
from logger import logger


class MessageType(enum.Enum):
    """Types of messages"""

    DEBUG = enum.auto()
    INFO = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    CRITICAL = enum.auto()


class NotifyType(enum.Enum):
    """Notification type."""

    DEBUG = enum.auto()
    INFO = enum.auto()
    QUESTION = enum.auto()
    ERROR = enum.auto()


class NotificationInterface(abc.ABC):
    """Interface for notification handling"""

    @abc.abstractmethod
    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        """Show a message to the user"""

    @abc.abstractmethod
    def ask_yes_no(self, message: str, title: str = "") -> bool:
        """Ask the user a yes or no question"""

    @abc.abstractmethod
    def user_input(self, message: str, title: str = "", hidden_text: bool = False) -> str | None:
        """Get an input from the user"""


class NotificationController(NotificationInterface):
    """Base class for notification handling"""

    def __init__(self, handler_type: NotificationInterface) -> None:
        self._notification_handler = handler_type

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        self._notification_handler.show(message, title, msg_type)

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        """Ask the user a yes or no question"""
        return self._notification_handler.ask_yes_no(message, title)

    def user_input(self, message: str, title: str = "", hidden_text: bool = False) -> str | None:
        """Get an input from the user"""
        return self._notification_handler.user_input(message, title, hidden_text)

    def debug(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        logger.debug("%s: %s", title, message)
        if is_debug_enabled():
            self.show(message=message, title=title, msg_type=MessageType.DEBUG)

    def info(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        logger.info("%s: %s", title, message)
        self.show(message=message, title=title, msg_type=MessageType.INFO)

    def warning(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        logger.warning("%s: %s", title, message)
        self.show(message=message, title=title, msg_type=MessageType.WARNING)

    def error(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        logger.error("%s: %s", title, message)
        self.show(message=message, title=title, msg_type=MessageType.ERROR)

    def critical(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        logger.critical("%s: %s", title, message)
        self.show(message=message, title=title, msg_type=MessageType.CRITICAL)

    def updater_callback(self, message: str, kind: NotifyType) -> bool:
        """Default user notify callback function."""
        logger.info(message)

        if kind == NotifyType.QUESTION:
            return self.ask_yes_no(message)

        if kind == NotifyType.ERROR:
            self.show(message, "", MessageType.ERROR)
        elif kind == NotifyType.INFO:
            self.show(message, "", MessageType.INFO)
        elif kind == NotifyType.DEBUG:
            self.show(message, "", MessageType.DEBUG)

        return True
