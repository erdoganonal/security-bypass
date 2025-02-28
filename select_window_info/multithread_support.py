"""helper class for supporting parallel executions. Normally, neither
tkinter nor PyQt are supporting the applications that are run in a thread.
Desired behavior might cause some problems during runtime. This module is
a helper file to create a subprocess to call the desired functions.
"""

import argparse
import json
import subprocess
import sys
from typing import Protocol, Sequence

from config.config import WindowData


# pylint: disable=too-few-public-methods
class SupportsSelect(Protocol):
    """a protocol class to let user to pass a parameter with a function or method named select."""

    def select(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> WindowData | None:
        """protocol function or method called select"""


def get_params() -> tuple[int, list[WindowData]]:
    """require the data parameter and try to get the value of it."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    param = json.loads(args.data)

    return param["hwnd"], [WindowData.from_dict(data) for data in param["data"]]


def main_execute(func_or_method: SupportsSelect) -> None:
    """execute the given function or method with cli arguments"""

    hwnd, windows_data = get_params()
    window_data = func_or_method.select(hwnd, windows_data)
    to_dump = None
    if window_data is not None:
        to_dump = window_data.to_dict()
    print(json.dumps(to_dump), end="")


def dump_params(window_hwnd: int, windows_data: Sequence[WindowData]) -> str:
    """convert the data to cli argument string"""

    data = {"hwnd": window_hwnd, "data": [window_data.to_dict() for window_data in windows_data]}
    return json.dumps(data).replace('"', '\\"')


def thread_execute(file: str, window_hwnd: int, windows_data: Sequence[WindowData]) -> WindowData | None:
    """allow to run this function in the thread and run the actual file with the subprocess"""

    dumped = dump_params(window_hwnd, windows_data)

    try:
        data = subprocess.check_output(f'{sys.executable} {file} --data "{dumped}"')
        loaded = json.loads(data)
        if loaded is None:
            return None
        return WindowData.from_dict(loaded)
    except subprocess.CalledProcessError:
        return None
