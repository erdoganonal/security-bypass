"""Tray notification handler"""

# pylint: disable=c-extension-no-member

from PyQt6 import QtWidgets

from handlers.notification.base import MessageType, NotificationInterface
from handlers.notification.gui import NotificationGUI

TITLE = "Security Bypass"

_MESSAGE_TYPE_TO_ICON = {
    MessageType.DEBUG: QtWidgets.QSystemTrayIcon.MessageIcon.Information,
    MessageType.INFO: QtWidgets.QSystemTrayIcon.MessageIcon.Information,
    MessageType.WARNING: QtWidgets.QSystemTrayIcon.MessageIcon.Warning,
    MessageType.ERROR: QtWidgets.QSystemTrayIcon.MessageIcon.Critical,
    MessageType.CRITICAL: QtWidgets.QSystemTrayIcon.MessageIcon.Critical,
}


class NotificationTray(NotificationInterface):
    """Show messages to the user with tray notifications"""

    def __init__(self, tray_icon: QtWidgets.QSystemTrayIcon) -> None:
        self._tray_icon = tray_icon
        self._gui_notification_handler = NotificationGUI()

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        self._tray_icon.showMessage(title or TITLE, message, _MESSAGE_TYPE_TO_ICON[msg_type], msecs=1000)

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        return self._gui_notification_handler.ask_yes_no(message, title or TITLE)

    def user_input(self, message: str, title: str = "", hidden_text: bool = False) -> str | None:
        return self._gui_notification_handler.user_input(message, title or TITLE, hidden_text)
