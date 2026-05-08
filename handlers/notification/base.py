"""Base module for notification handling"""

import abc
import enum

from common.tools import is_debug_enabled
from logger import logger


class MessageType(enum.Enum):
    """Types of messages"""

    DEBUG = enum.auto()
    INFO = enum.auto()
    QUESTION = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    CRITICAL = enum.auto()


_MSG_TYPE_LOG_LEVEL_MAP = {
    MessageType.DEBUG: logger.debug,
    MessageType.INFO: logger.info,
    MessageType.QUESTION: logger.info,
    MessageType.WARNING: logger.warning,
    MessageType.ERROR: logger.error,
    MessageType.CRITICAL: logger.critical,
}


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
        self._has_started = False

    def mark_started(self) -> None:
        """Mark the tool as started, allowing late info messages to be shown"""
        self._has_started = True

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        _MSG_TYPE_LOG_LEVEL_MAP[msg_type]("%s: %s", title, message)
        self._notification_handler.show(message, title, msg_type)

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        """Ask the user a yes or no question"""
        return self._notification_handler.ask_yes_no(message, title)

    def user_input(self, message: str, title: str = "", hidden_text: bool = False) -> str | None:
        """Get an input from the user"""
        return self._notification_handler.user_input(message, title, hidden_text)

    def debug(self, message: str, title: str = "") -> None:
        """Show a debug message to the user"""
        if is_debug_enabled():
            self.show(message=message, title=title, msg_type=MessageType.DEBUG)
        else:
            # special case for debug messages, as they are not shown to the user, but we still want to log them
            logger.debug("%s: %s", title, message)

    def info(self, message: str, title: str = "") -> None:
        """Show an info message to the user"""
        self.show(message=message, title=title, msg_type=MessageType.INFO)

    def late_info(self, message: str, title: str = "") -> None:
        """Show an info message to the user, but only after the tool has been started"""
        if self._has_started:
            self.info(message, title)

    def warning(self, message: str, title: str = "") -> None:
        """Show a warning message to the user"""
        self.show(message=message, title=title, msg_type=MessageType.WARNING)

    def error(self, message: str, title: str = "") -> None:
        """Show an error message to the user"""
        self.show(message=message, title=title, msg_type=MessageType.ERROR)

    def critical(self, message: str, title: str = "") -> None:
        """Show a critical message to the user"""
        self.show(message=message, title=title, msg_type=MessageType.CRITICAL)
