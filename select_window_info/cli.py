"""Select the window by using cli"""

import sys
from typing import Sequence

from config.config import WindowData
from select_window_info.base import SelectWindowInfoBase


class CLISelectWindowInfo(SelectWindowInfoBase):
    """Select the window by using cli"""

    @property
    def supports_thread(self) -> bool:
        return False

    def select(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> str | None:
        """Let user to pick the password from the list"""
        window_pin_rel: dict[str, str] = {}

        if not windows_data:
            return None

        for idx, window_data in enumerate(windows_data, start=1):
            print(f"[{idx}] {window_data.title} - {window_data.name}")
            window_pin_rel[str(idx)] = window_data.passkey

        try:
            return window_pin_rel[input("Select the password/pin from the list: ")]
        except KeyError:
            sys.exit("Invalid pin/password name")
