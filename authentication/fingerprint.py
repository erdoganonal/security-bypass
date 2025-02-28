"""Fingerprint module for capturing fingerprint data and generating a consistent SHA-256 hash."""

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
from typing import TypedDict

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


def _get_fingerprint_result() -> FingerprintResult:
    """Captures fingerprint data and returns a consistent SHA-256 hash."""

    fingerprint_result: FingerprintResult = {
        "hash": "",
        "error": "",
        "error_code": 0,
    }

    try:
        fingerprint_result["hash"] = _get_fingerprint_hash()
    except FingerprintException as e:
        fingerprint_result["error"] = e.message
        fingerprint_result["error_code"] = e.error_code

    return fingerprint_result


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

    print("Place your finger on the scanner...")

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

    subprocess.check_output(
        [os.getcwd() + r"\admin.bat", os.getcwd(), sys.executable, str(server_socket.getsockname()[1])],
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
    print(get_fingerprint_result())


if __name__ == "__main__":
    main()
