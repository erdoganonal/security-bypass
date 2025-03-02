"""Fingerprint authentication module."""

import ctypes
import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
from ctypes import Structure, c_ubyte, c_ulong, windll
from ctypes.wintypes import DWORD, HANDLE
from pathlib import Path
from typing import TypedDict

from common.tools import is_debug_enabled
from helpers.ui_helpers.background_authenticator import BackgroundAuthenticatorBase, BgWindowData

# Load Windows Biometric Framework (WBF)
winbio = windll.Winbio

# Define Constants
WINBIO_TYPE_FINGERPRINT = 0x00000008
WINBIO_POOL_SYSTEM = 0x00000001
WINBIO_NO_PURPOSE_AVAILABLE = 0x00000000
WINBIO_FLAG_DEFAULT = 0x00000000
WINBIO_ID_TYPE_WILDCARD = 0x00000000
WINBIO_ID_VALUE_ANY = 0xFFFFFFFF


class _WinbioIdentity(Structure):  # pylint: disable=too-few-public-methods
    """WinbioIdentity structure for fingerprint identity."""

    _fields_ = [("Type", DWORD), ("Value", c_ubyte * 78)]  # Windows stores fingerprint templates as 78 bytes


class FingerprintResult(TypedDict):
    """Fingerprint result type."""

    hash: str
    error: str
    error_code: int


class FingerprintException(Exception):
    """Fingerprint exception class."""

    def __init__(self, message: str, error_code: int) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


def is_user_admin() -> bool:
    """Check if the user has administrative privileges."""

    return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[no-any-return]


def get_fingerprint_result() -> FingerprintResult:
    """read the fingerprint from the sensor and return the hash of the fingerprint data"""

    if is_user_admin():
        # get the result directly if the user is an admin
        fingerprint_result = _get_fingerprint_result()

        if len(sys.argv) == 2:
            # send the result to the server if a port is provided
            try:
                client_socket = socket.socket()
                client_socket.connect(("127.0.0.1", int(sys.argv[1])))

                client_socket.send(json.dumps(fingerprint_result).encode())

                client_socket.close()
            except (ConnectionRefusedError, socket.timeout):
                pass
    else:
        fingerprint_result = request_admin_get_fingerprint_result()

    return fingerprint_result


class FingerprintBGAuthenticator(BackgroundAuthenticatorBase):
    """Fingerprint background authenticator UI."""

    def get_window_data(self) -> BgWindowData:
        return {
            "window_title": "Fingerprint Authenticator",
            "title": "Place your finger",
            "info": "Ensure your finger covers the entire sensor.\n\
Please scan the same finger used during encryption.",
            "icon_path": os.path.abspath("ui/resources/fingerprint.ico"),
        }


def _get_fingerprint_result() -> FingerprintResult:
    fingerprint_bg_auth = FingerprintBGAuthenticator()

    result = FingerprintResult(hash="", error="", error_code=0)
    threading.Thread(target=__get_fingerprint_result, args=(fingerprint_bg_auth, result), daemon=True).start()

    fingerprint_bg_auth.show()

    return result


def __get_fingerprint_result(fingerprint_ui: FingerprintBGAuthenticator, result: FingerprintResult) -> None:
    """Captures fingerprint data and returns a consistent SHA-256 hash."""

    try:
        result["hash"] = _get_fingerprint_hash()
    except FingerprintException as e:
        result["error"] = e.message
        result["error_code"] = e.error_code

    fingerprint_ui.thread_quit()


def _get_fingerprint_hash() -> str:

    # Open a biometric session
    session = HANDLE()
    result = winbio.WinBioOpenSession(
        WINBIO_TYPE_FINGERPRINT,  # Fingerprint reader
        WINBIO_POOL_SYSTEM,  # Use the system pool
        WINBIO_NO_PURPOSE_AVAILABLE,  # No specific purpose
        None,  # No specific sensor list
        0,  # No sensor count
        WINBIO_FLAG_DEFAULT,  # Default settings
        ctypes.byref(session),  # Store session handle
    )

    if result != 0:
        raise FingerprintException("Failed to open fingerprint session.", result)

    # Capture fingerprint
    identity = _WinbioIdentity()
    unit_id = c_ulong()
    sub_factor = DWORD()

    result = winbio.WinBioIdentify(session, ctypes.byref(unit_id), ctypes.byref(identity), ctypes.byref(sub_factor))
    if result != 0:
        winbio.WinBioCloseSession(session)
        raise FingerprintException("Fingerprint scan failed or not recognized.", result)

    # Close session
    winbio.WinBioCloseSession(session)

    # Generate a hash from fingerprint identity
    fingerprint_bytes = bytes(identity.Value[:])  # Extract template bytes
    fingerprint_hash = hashlib.sha256(fingerprint_bytes).hexdigest()

    return fingerprint_hash


def request_admin_get_fingerprint_result() -> FingerprintResult:
    """Client program to get the fingerprint hash from the fingerprint reader."""

    server_socket = socket.socket()
    server_socket.bind(("127.0.0.1", 0))  # port is 0 to get a random port
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.listen(1)

    result: bytes | None = None

    def wait_connection() -> None:
        nonlocal result, server_socket
        conn, _ = server_socket.accept()

        while True:
            try:
                data = conn.recv(1024)
                if data:
                    result = data
                    break
            except (ConnectionResetError, socket.timeout):
                break

        conn.close()
        server_socket.close()

    threading.Thread(target=wait_connection, daemon=True).start()

    exe_path = Path(sys.executable)
    if is_debug_enabled():
        exe_path = exe_path.parent / "python.exe"
    else:
        exe_path = exe_path.parent / "pythonw.exe"

    subprocess.check_output(
        [os.getcwd() + r"\admin.bat", os.getcwd(), str(exe_path), str(server_socket.getsockname()[1])],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    if result is None:
        return {
            "hash": "",
            "error": "Fingerprint scan canceled by user. Please try again.",
            "error_code": -1,
        }
    return json.loads(result)  # type: ignore[no-any-return]


def main() -> None:
    """Main function to get the fingerprint result and print it."""
    get_fingerprint_result()


if __name__ == "__main__":
    main()
