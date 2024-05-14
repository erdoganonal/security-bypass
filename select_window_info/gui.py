"""Select the window by using tkinter GUI"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Iterable, Tuple

from pygetwindow import Win32Window  # type: ignore[import-untyped]
from tkhelper.widgets import MultiColumnListbox

from select_window_info.base import SelectWindowInfoBase, WindowInfo


class GUISelectWindowInfo(SelectWindowInfoBase):
    """Select the window by using tkinter GUI"""

    def __init__(self) -> None:
        self._root: tk.Tk | None = None
        self._listbox: MultiColumnListbox | None = None
        self._name: str | None = None

    def _on_ok(self) -> None:
        if self._root is None or self._listbox is None:
            return

        self._name = self._listbox.get_selected("name")
        self._root.destroy()

    def _configure_window(self) -> None:
        self._root = tk.Tk()
        self._root.grid_rowconfigure(0, weight=1)
        self._root.grid_columnconfigure(0, weight=1)
        self._listbox = MultiColumnListbox(self._root, ["name"], title="Please select the value")
        next(widget for widget in self._listbox.tree.master.winfo_children() if isinstance(widget, ttk.Scrollbar)).grid_forget()

        ttk.Button(self._root, text="OK", command=self._on_ok).grid(sticky=tk.NSEW)

    def _update(self, window: Win32Window | None) -> None:
        if window is None or self._root is None:
            return

        left, top, width, height = window.left, window.top, window.width, window.height
        window.minimize()
        window.maximize()
        window.resizeTo(width, height)
        window.moveTo(left, top)

        self._root.wm_geometry(f"+{left + width}+{top}")

    def select(self, windows_info: Iterable[WindowInfo]) -> Tuple[Win32Window, str] | None:
        window_info_list = list(windows_info)
        if not window_info_list:
            return None

        self._configure_window()
        if self._root is None or self._listbox is None:
            return None

        window_pin_rel: Dict[str, Tuple[Win32Window, str]] = {}

        window: Win32Window | None = None
        for window_info in window_info_list:
            if window is None:
                window = window_info.window
            for pin_name, pin in window_info.pin_info.items():
                self._listbox.add_row([pin_name])
                window_pin_rel[pin_name] = (window_info.window, pin)

        self._root.wm_overrideredirect(True)
        self._root.wm_attributes("-topmost", True)
        self._root.wm_geometry("160x300")
        self._root.after(100, lambda: self._update(window))
        self._root.mainloop()

        if self._name is None:
            return None

        try:
            return window_pin_rel[self._name]
        except KeyError:
            return None
