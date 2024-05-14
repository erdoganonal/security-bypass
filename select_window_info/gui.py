"""Select the window by using tkinter GUI"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Sequence

from pygetwindow import PyGetWindowException, Win32Window  # type: ignore[import-untyped]
from tkhelper.widgets import MultiColumnListbox

from common.tools import get_window_by_hwnd
from config.config import WindowData
from select_window_info.base import SelectWindowInfoBase


class _GUISelectWindowInfoHelper:
    """helper class for GUISelectWindowInfo"""

    def __init__(self) -> None:
        self._name: str | None = None
        self._send_enter: bool = True

        self._root: tk.Tk | None = None
        self._root, self._send_enter_checkbox, self._listbox = self.configure_window()

    def render(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> str | None:
        """show a ui to the user and get the values"""
        if self._root is None:
            return None

        window_pin_rel: Dict[str | None, str] = {}

        for window_data in windows_data:
            self._listbox.add_row([window_data.name])
            window_pin_rel[window_data.name] = window_data.passkey

        self._root.wm_overrideredirect(True)
        self._root.wm_attributes("-topmost", True)
        self._root.wm_geometry("160x300")
        self._root.after(100, lambda: self._update(get_window_by_hwnd(window_hwnd)))
        self._root.mainloop()

        try:
            return window_pin_rel[self._name] + ("\n" if self._send_enter else "")
        except KeyError:
            return None

    def configure_window(self) -> tuple[tk.Tk, tk.BooleanVar, MultiColumnListbox]:
        """configure and return the variables"""
        if self._root is not None:
            raise ValueError("can only configure once")

        root = tk.Tk()
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        send_enter_checkbox = tk.BooleanVar(root, self._send_enter)

        listbox = MultiColumnListbox(root, ["name"], title="Please select the value")
        ttk.Checkbutton(root, text="send enter", variable=send_enter_checkbox).grid(sticky=tk.NSEW)
        ttk.Button(root, text="OK", command=self._on_ok).grid(sticky=tk.NSEW)

        listbox.tree.bind("<Double-1>", lambda e: self._on_ok())

        # remove the vertical scroll bar from the listbox
        next(widget for widget in listbox.tree.master.winfo_children() if isinstance(widget, ttk.Scrollbar)).grid_forget()

        return root, send_enter_checkbox, listbox

    def _on_ok(self) -> None:
        if self._root is None:
            return

        self._name = self._listbox.get_selected("name")
        self._send_enter = self._send_enter_checkbox.get()

        self._root.destroy()
        self._root = None

    def __update_loop(self, window: Win32Window) -> None:
        if self._root is None:
            return

        try:
            left, top, width = window.left, window.top, window.width
        except PyGetWindowException:
            self._on_ok()
            return
        self._root.wm_geometry(f"+{left + width}+{top}")
        self._root.after(1000, lambda: self.__update_loop(window))

    def _update(self, window: Win32Window | None) -> None:
        if window is None or self._root is None:
            return

        left, top, width, height = window.left, window.top, window.width, window.height
        window.minimize()
        window.maximize()
        window.resizeTo(width, height)
        window.moveTo(left, top)

        self._root.after(500, lambda: self.__update_loop(window))


class GUISelectWindowInfo(SelectWindowInfoBase):
    """Select the window by using tkinter GUI"""

    @property
    def supports_thread(self) -> bool:
        return True

    def select(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> str | None:
        if not windows_data:
            return None

        return _GUISelectWindowInfoHelper().render(window_hwnd, windows_data)
