"""GUI notification handler"""

import tkinter as tk
from tkinter import messagebox, ttk

from common.tools import update_and_center
from handlers.notification.base import MessageType, NotificationInterface

_MSG_ACTION_MAP = {
    MessageType.DEBUG: messagebox.showinfo,
    MessageType.INFO: messagebox.showinfo,
    MessageType.WARNING: messagebox.showwarning,
    MessageType.ERROR: messagebox.showerror,
    MessageType.CRITICAL: messagebox.showerror,
}


class NotificationGUI(NotificationInterface):
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

    def user_input(self, message: str, title: str = "", hidden_text: bool = False) -> str | None:
        ui = _UserInputUI()
        ui.show(message, title, hidden_text=hidden_text)

        return ui.user_input


class _UserInputUI:
    def __init__(self) -> None:
        self._user_input: str | None = None

    @property
    def user_input(self) -> str | None:
        """get the user input"""
        return self._user_input

    @staticmethod
    def _preview(entry: ttk.Entry, button: ttk.Button) -> None:
        if entry.config("show")[-1] == "*":
            entry.config(show="")
            button.configure(text="Hide Password")
        else:
            entry.config(show="*")
            button.configure(text="Show Password")

    def _close(self, root: tk.Tk, entry: ttk.Entry, is_cancelled: bool = True) -> None:
        if not is_cancelled:
            self._user_input = entry.get()

        root.destroy()

    def show(self, prompt: str, title: str | None = None, hidden_text: bool = False) -> None:
        """Show a dialog to get user input"""

        root = tk.Tk()

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        main_frame = ttk.Frame(root)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_configure(sticky=tk.NSEW)

        mk_entry = ttk.Entry(main_frame, show="*" if hidden_text else "")
        mk_entry.grid_configure(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5, columnspan=2)
        mk_entry.bind("<Return>", lambda e: self._close(root, mk_entry, False))

        if hidden_text:
            mk_preview_button = ttk.Button(main_frame, text="Show Password")
            mk_preview_button.grid_configure(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)
            mk_preview_button.configure(command=lambda: self._preview(mk_entry, mk_preview_button))

        mk_ok_button = ttk.Button(main_frame, text="OK", command=lambda: self._close(root, mk_entry, False))
        mk_ok_button.grid_configure(row=1, column=int(hidden_text), sticky=tk.NSEW, padx=5, pady=5, columnspan=int(not hidden_text) + 1)

        root.wm_title(title or prompt)
        root.wm_geometry("350x75")
        root.wm_resizable(False, False)
        root.wm_protocol("WM_DELETE_WINDOW", lambda: self._close(root, mk_entry))
        mk_entry.focus_force()
        update_and_center(root)
        root.mainloop()
