"""Select the window by using cli"""

import sys
from typing import Iterable

from pygetwindow import Win32Window  # type: ignore[import-untyped]

from select_window_info.base import SelectWindowInfoBase, WindowInfo


class CLISelectWindowInfo(SelectWindowInfoBase):
    """Select the window by using cli"""

    def select(self, windows_info: Iterable[WindowInfo]) -> Win32Window | None:
        """Let user to pick the password from the list"""
        window_pin_rel = {}

        idx = 1
        for window_info in windows_info:
            print(f"[{idx}] {window_info.window_data.title} - {window_info.window_data.name}")
            window_pin_rel[str(idx)] = window_info
            idx += 1

        if idx == 1:
            return None

        try:
            return window_pin_rel[input("Select the password/pin from the list: ")]
        except KeyError:
            sys.exit("Invalid pin/password name")
