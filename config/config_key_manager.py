"""Helper functions to get the master key from the user."""

import os
import sys
import tkinter as tk
from getpass import getpass
from tkinter import ttk

from settings import DFT_ENCODING, MK_ENV_NAME, MK_REQUEST_PARAM


def get_mk() -> bytes | None:
    """Tries to get the master key with all possible ways"""
    return get_mk_cli_on_request() or get_mk_from_env() or get_mk_ui()


def validate_and_get_mk() -> bytes:
    """Call the get_mk and validate"""
    mk = get_mk()
    if mk:
        return mk

    raise ValueError(
        f"Master Key must be specified. Use {MK_REQUEST_PARAM} for cli or"
        f" {MK_ENV_NAME} environment variable or GUI to enter the Master Key."
    )


def get_mk_cli_on_request() -> bytes | None:
    """Check the cli arguments for user request to pass the key."""

    if MK_REQUEST_PARAM in sys.argv:
        return getpass().encode(encoding=DFT_ENCODING)

    return None


def get_mk_from_env() -> bytes | None:
    """Check the environment variables for the master key"""
    if (key := os.getenv(MK_ENV_NAME)) is not None:
        return key.encode(DFT_ENCODING)

    return None


def get_mk_ui() -> bytes | None:
    """Create a window to let user to enter the master key"""
    mk = ""

    root = tk.Tk()
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    main_frame = ttk.Frame(root)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_configure(sticky=tk.NSEW)

    mk_entry = ttk.Entry(main_frame, show="*")
    mk_entry.grid_configure(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5, columnspan=2)

    mk_preview_button = ttk.Button(main_frame, text="Preview")
    mk_preview_button.grid_configure(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)
    mk_ok_button = ttk.Button(main_frame, text="OK", command=lambda: _close(False))
    mk_ok_button.grid_configure(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)

    def _preview() -> None:
        nonlocal mk_preview_button, mk_entry
        if mk_entry.config("show")[-1] == "*":
            mk_entry.config(show="")
        else:
            mk_entry.config(show="*")

    mk_preview_button.configure(command=_preview)

    def _close(is_cancelled: bool = True) -> None:
        nonlocal mk, mk_entry, root

        if not is_cancelled:
            mk = mk_entry.get()

        root.destroy()

    root.wm_title("Please enter the Master Key")
    root.wm_geometry("350x75")
    root.wm_protocol("WM_DELETE_WINDOW", _close)
    root.mainloop()

    if mk:
        return mk.encode(DFT_ENCODING)
    return None
