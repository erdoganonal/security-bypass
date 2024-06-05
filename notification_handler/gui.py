"""GUI notification handler"""

import tkinter as tk
from tkinter import messagebox

from notification_handler.base import MessageType, NotificationHandlerBase

_MSG_ACTION_MAP = {
    MessageType.DEBUG: messagebox.showinfo,
    MessageType.INFO: messagebox.showinfo,
    MessageType.WARNING: messagebox.showwarning,
    MessageType.ERROR: messagebox.showerror,
    MessageType.CRITICAL: messagebox.showerror,
}


class GUINotificationHandler(NotificationHandlerBase):
    """Show messages to the user"""

    def __init__(self, timeout_ms: int | None = 2000) -> None:
        self.timeout_ms = timeout_ms
        self._temp_timeout_ms: int | None = None

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        return messagebox.askyesno(title or message, message)

    def set_temp_timeout(self, timeout_ms: int) -> None:
        """Set the timeout for the next message, once"""
        self._temp_timeout_ms = timeout_ms

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", 1)

        if msg_type not in (MessageType.ERROR, MessageType.CRITICAL):
            if self._temp_timeout_ms is not None:
                root.after(self._temp_timeout_ms, root.destroy)
            elif self.timeout_ms is not None:
                root.after(self.timeout_ms, root.destroy)
        self._temp_timeout_ms = None

        try:
            _MSG_ACTION_MAP[msg_type](title=title or message, message=message, master=root)
        except tk.TclError:
            pass

        try:
            root.destroy()
        except tk.TclError:
            pass
