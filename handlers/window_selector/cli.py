"""Select the window by using cli"""

from typing import Sequence

from config.config import SelectedWindowProperties, WindowData
from handlers.window_selector.base import WindowSelectorInterface


class WindowSelectorCLI(WindowSelectorInterface):
    """Select the window by using cli"""

    @property
    def supports_thread(self) -> bool:
        return False

    def select(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> SelectedWindowProperties | None:
        """Let user to pick the password from the list"""
        window_pin_rel: dict[str, WindowData] = {}

        if not windows_data:
            return None

        for idx, window_data in enumerate(windows_data, start=1):
            print(f"[{idx}] {window_data.title} - {window_data.name}")
            window_pin_rel[str(idx)] = window_data

        try:
            w_data = window_pin_rel[input("Select the password/pin from the list: ")]
        except KeyError:
            return None

        return SelectedWindowProperties(
            send_enter=input("Send Enter after selecting? (y/n): ").strip().lower() == "y",
            passkey=w_data.passkey,
            verify_sent=w_data.verify_sent,
        )
