"""Tray notification handler"""

from tkinter import messagebox

from notification_handler.base import MessageType, NotificationHandlerBase


class TrayNotificationHandler(NotificationHandlerBase):
    """Show messages to the user with tray notifications"""

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        return messagebox.askyesno(title or message, message)

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        pass
