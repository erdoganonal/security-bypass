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

    def __init__(self, timeout_secs: int | None = 2000) -> None:
        self.timeout_secs = timeout_secs

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        root = tk.Tk()
        root.withdraw()
        try:
            if self.timeout_secs is not None:
                root.after(self.timeout_secs, root.destroy)
            _MSG_ACTION_MAP[msg_type](title=title, message=message)
        except tk.TclError:
            pass
