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

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", 1)

        if self.timeout_ms is not None:
            root.after(self.timeout_ms, root.destroy)

        try:
            _MSG_ACTION_MAP[msg_type](title=title or message, message=message, master=root)
        except tk.TclError:
            pass

        try:
            root.destroy()
        except tk.TclError:
            pass
