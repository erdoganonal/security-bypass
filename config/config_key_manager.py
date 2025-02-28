"""Helper functions to get the master key from the user."""

import os
import sys
import tkinter as tk
from getpass import getpass
from tkinter import ttk

from tkhelper.widgets import update_and_center

from authentication import fingerprint
from common.tools import InplaceInt
from helpers.config_manager import AuthMethod, ConfigManager
from settings import CREDENTIALS_FILE, DFT_ENCODING, MK_ENV_NAME, MK_REQUEST_PARAM

NOT_SET = 0
FROM_CLI = 1
FROM_ENV = 2
FROM_UI = 3


def check_config_file() -> None:
    """Check if the config file exists"""
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError()


def get_mk(prompt: str | None = None, which: InplaceInt | None = None) -> bytes | None:
    """Tries to get the master key with all possible ways"""

    return get_mk_cli_on_request(prompt=prompt, which=which) or get_mk_from_env(which=which) or get_mk_ui(prompt=prompt, which=which)


def validate_and_get_mk(prompt: str | None = None, which: InplaceInt | None = None) -> bytes:
    """Call the get_mk and validate"""

    cfg = ConfigManager.get_config()
    mk: bytes | None = None
    if cfg.auth_method == AuthMethod.PASSWORD:
        mk = get_mk(prompt=prompt, which=which)
    elif cfg.auth_method == AuthMethod.FINGERPRINT:
        mk = get_fingerprint_hash_bytes()

    if mk:
        return mk

    raise KeyError(
        f"Master Key must be specified. Use {MK_REQUEST_PARAM} for cli or"
        f" {MK_ENV_NAME} environment variable or GUI to enter the Master Key."
    )


def get_mk_cli_on_request(prompt: str | None = None, which: InplaceInt | None = None) -> bytes | None:
    """Check the cli arguments for user request to pass the key."""

    if MK_REQUEST_PARAM in sys.argv:
        if which:
            which.set(FROM_CLI)
        if prompt is None:
            return getpass().encode(encoding=DFT_ENCODING)
        return getpass(prompt).encode(encoding=DFT_ENCODING)

    return None


def get_mk_from_env(which: InplaceInt | None = None) -> bytes | None:
    """Check the environment variables for the master key"""
    if (key := os.getenv(MK_ENV_NAME)) is not None:
        if which:
            which.set(FROM_ENV)
        return key.encode(DFT_ENCODING)

    return None


def get_mk_ui(prompt: str | None = None, which: InplaceInt | None = None) -> bytes | None:
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
    mk_entry.bind("<Return>", lambda e: _close(False))

    mk_preview_button = ttk.Button(main_frame, text="Show Password")
    mk_preview_button.grid_configure(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)
    mk_ok_button = ttk.Button(main_frame, text="OK", command=lambda: _close(False))
    mk_ok_button.grid_configure(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)

    def _preview() -> None:
        nonlocal mk_preview_button, mk_entry
        if mk_entry.config("show")[-1] == "*":
            mk_entry.config(show="")
            mk_preview_button.configure(text="Hide Password")
        else:
            mk_entry.config(show="*")
            mk_preview_button.configure(text="Show Password")

    mk_preview_button.configure(command=_preview)

    def _close(is_cancelled: bool = True) -> None:
        nonlocal mk, mk_entry, root

        if not is_cancelled:
            mk = mk_entry.get()

        root.destroy()

    root.wm_title(prompt or "Please enter the Master Key")
    root.wm_geometry("350x75")
    root.resizable(False, False)
    root.wm_protocol("WM_DELETE_WINDOW", _close)
    mk_entry.focus_force()
    update_and_center(root)
    root.mainloop()

    if mk:
        if which:
            which.set(FROM_UI)
        return mk.encode(DFT_ENCODING)
    return None


def get_fingerprint_hash_bytes() -> bytes | None:
    """Get the fingerprint hash bytes from the user"""

    fingerprint_result = fingerprint.get_fingerprint_result()
    if fingerprint_result["error"]:
        return None

    return fingerprint_result["hash"].encode(DFT_ENCODING)
