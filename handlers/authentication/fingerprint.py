"""Fingerprint authentication module."""

import os
from typing import Type

from common.exceptions import WinBioError
from handlers.authentication.base import AuthenticationInterface
from handlers.authentication.winbio.winbio_base import SupportedBiometricTypes, WinBioInterface, get_auth_result
from handlers.authentication.winbio.winbio_base import main as winbio_main
from helpers.ui_helpers.background_authenticator import BackgroundAuthenticatorBase, BgWindowData


class AuthenticationFingerprint(AuthenticationInterface):
    """Fingerprint authentication handler."""

    def get_master_key(self) -> bytes:
        result = get_auth_result(SupportedBiometricTypes.FINGERPRINT)

        if result["error_code"] == 0:
            return result["hash"].encode()

        raise WinBioError(result["error"], result["error_code"])


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


class FingerprintScanner(WinBioInterface):
    """Scan the fingerprint in the background while the background authenticator is running."""

    @property
    def winbio_id(self) -> SupportedBiometricTypes:
        return SupportedBiometricTypes.FINGERPRINT

    @property
    def background_authenticator(self) -> Type[BackgroundAuthenticatorBase]:
        return FingerprintBGAuthenticator


def main() -> None:
    """Start the fingerprint scanner."""
    winbio_main(FingerprintScanner())


if __name__ == "__main__":
    main()
