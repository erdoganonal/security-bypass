"""interface for winbio recognition"""

import abc
import enum
import hashlib
import json
import subprocess
import sys
import threading
from ctypes import Structure, byref, c_ubyte, c_ulong, windll
from ctypes.wintypes import DWORD, HANDLE
from pathlib import Path
from typing import Type

from common.exceptions import WinBioError
from common.tools import is_user_admin
from handlers.authentication.base import AuthenticationResult
from handlers.authentication.winbio.winbio_types import (
    WINBIO_FLAG_DEFAULT,
    WINBIO_NO_TYPE_AVAILABLE,
    WINBIO_TYPE_FACIAL_FEATURES,
    WINBIO_TYPE_FINGERPRINT,
    WINBIO_TYPE_MULTIPLE,
)
from helpers.ui_helpers.background_authenticator import BackgroundAuthenticatorBase
from settings import CURRENT_DIR

WINBIO_USER_CANCELED = 1
WINBIO_ERROR_NOT_ADMIN = 2
WINBIO_ERROR_UNKNOWN_AUTH_METHOD = 3

# Load Windows Biometric Framework (WBF)
winbio = windll.Winbio


class SupportedBiometricTypes(enum.Enum):
    """list of supported biometric types."""

    FINGERPRINT = WINBIO_TYPE_FINGERPRINT
    FACE_ID = WINBIO_TYPE_FACIAL_FEATURES


class _WinbioIdentity(Structure):  # pylint: disable=too-few-public-methods
    """WinbioIdentity structure for biometric identity."""

    _fields_ = [("Type", DWORD), ("Value", c_ubyte * 78)]  # Windows stores biometric templates as 78 bytes


def dump_result(result: AuthenticationResult) -> str:
    """Dump the authentication result as a JSON string."""

    return json.dumps(result)


class WinBioInterface(abc.ABC):
    """Interface for winbio recognition"""

    def __init__(self) -> None:
        self._is_running = False
        self._authenticators: list[BackgroundAuthenticatorBase] = []
        self._result = self.get_winbio_result_dict()

    @property
    @abc.abstractmethod
    def winbio_id(self) -> SupportedBiometricTypes:
        """Get the winbio id."""

    @property
    @abc.abstractmethod
    def background_authenticator(self) -> Type[BackgroundAuthenticatorBase]:
        """Get the background authenticator."""

    def start_scan(self) -> AuthenticationResult:
        """Start the winbio scan."""

        winbio_bg_auth = self.background_authenticator()
        self._authenticators.append(winbio_bg_auth)

        threading.Thread(target=self._scan, daemon=True).start()
        winbio_bg_auth.show()

        return self._result

    @staticmethod
    def get_winbio_result_dict(
        hash_val: str = "",
        title: str = "Biometric scan canceled by user.",
        error: str = "Biometric scan canceled by user. Please try again.",
        error_code: int = WINBIO_USER_CANCELED,
    ) -> AuthenticationResult:
        """Get the default biometric result dict."""

        if hash_val:
            error_code = 0

        return {
            "hash": hash_val,
            "title": title,
            "error": error,
            "error_code": error_code,
        }

    def _scan(self) -> None:
        """Captures biometric data and returns a consistent SHA-256 hash."""

        if self._is_running:
            return

        self._is_running = True

        try:
            self._result["hash"] = get_hash(self.winbio_id)
            self._result["title"] = "Biometric scan completed successfully."
            self._result["error"] = ""
            self._result["error_code"] = 0
        except WinBioError as e:
            self._result["hash"] = ""
            self._result["title"] = e.message
            self._result["error"] = e.message
            self._result["error_code"] = e.error_code

        for authenticator_ui in self._authenticators:
            authenticator_ui.thread_quit()

        self._is_running = False
        self._authenticators.clear()


def get_hash(bio_type: SupportedBiometricTypes) -> str:
    """get the hash of the winbio"""

    # Open a biometric session
    session = HANDLE()
    result = winbio.WinBioOpenSession(
        bio_type.value,  # WinBio biometric type
        WINBIO_TYPE_MULTIPLE,  # Use the system pool
        WINBIO_NO_TYPE_AVAILABLE,  # No specific purpose
        None,  # No specific sensor list
        0,  # No sensor count
        WINBIO_FLAG_DEFAULT,  # Default settings
        byref(session),  # Store session handle
    )

    if result != 0:
        raise WinBioError("Biometric Session Error", f"Failed to open biometric session: {bio_type}", result)

    # Capture biometric data
    identity = _WinbioIdentity()
    unit_id = c_ulong()
    sub_factor = DWORD()

    result = winbio.WinBioIdentify(session, byref(unit_id), byref(identity), byref(sub_factor))
    if result != 0:
        winbio.WinBioCloseSession(session)
        raise WinBioError("Biometric Scan Error", f"Biometric scan[{bio_type.name}] failed or not recognized.", result)

    # Close session
    winbio.WinBioCloseSession(session)

    # Generate a hash from biometric identity
    biometric_bytes = bytes(identity.Value[:])  # Extract template bytes
    biometric_hash = hashlib.sha256(biometric_bytes).hexdigest()

    return biometric_hash


def get_auth_result(bio_type: SupportedBiometricTypes) -> AuthenticationResult:
    """Get the auth result from the biometric scanner."""

    exe_path = Path(sys.executable).absolute()

    try:
        output = subprocess.check_output(f"{exe_path} -m handlers.authentication.winbio {bio_type.name}", cwd=CURRENT_DIR.absolute())
    except subprocess.CalledProcessError as e:
        return json.loads(e.output)  # type: ignore[no-any-return]

    return json.loads(output)  # type: ignore[no-any-return]


def unknown_auth_method_result_main() -> None:
    """Main function to print the unknown authentication method result."""

    unknown_auth_method_result = WinBioInterface.get_winbio_result_dict(
        error="Unknown authentication method. Please select a valid authentication method.",
        error_code=WINBIO_ERROR_UNKNOWN_AUTH_METHOD,
    )

    print(dump_result(unknown_auth_method_result))
    sys.exit(WINBIO_ERROR_UNKNOWN_AUTH_METHOD)


def main(winbio_scanner: WinBioInterface) -> None:
    """Main function to get the biometric result and print it."""

    if is_user_admin():
        winbio_result = winbio_scanner.start_scan()
    else:
        winbio_result = winbio_scanner.get_winbio_result_dict()
        winbio_result["error"] = "Please run the application as an administrator."
        winbio_result["error_code"] = WINBIO_ERROR_NOT_ADMIN

    print(dump_result(winbio_result))
    sys.exit(winbio_result["error_code"])
