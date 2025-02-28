"""Tray notification handler"""

from common.tools import is_debug_enabled
from notification_handler.base import MessageType, NotificationHandlerBase
from notification_handler.gui import GUINotificationHandler


class TrayNotificationHandler(NotificationHandlerBase):
    """Show messages to the user with tray notifications"""

    def __init__(self) -> None:
        self._gui_notification_handler = GUINotificationHandler()

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        return self._gui_notification_handler.ask_yes_no(title or message, message)

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        if is_debug_enabled():
            self._gui_notification_handler.show(message, title, msg_type)
