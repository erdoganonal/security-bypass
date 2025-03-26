"""Face recognition authentication module."""

import os
from typing import Type

from common.exceptions import WinBioError
from handlers.authentication.base import AuthenticationInterface
from handlers.authentication.winbio.winbio_base import SupportedBiometricTypes, WinBioInterface, get_auth_result
from handlers.authentication.winbio.winbio_base import main as winbio_main
from helpers.ui_helpers.background_authenticator import BackgroundAuthenticatorBase, BgWindowData

#! Face recognition is not supported by windows yet.
#! https://learn.microsoft.com/en-us/windows/win32/secbiomet/winbio-biometric-type-constants
#! Only WINBIO_TYPE_FINGERPRINT is currently supported.


class AuthenticationFaceRecognition(AuthenticationInterface):
    """Face recognition authentication handler."""

    def get_master_key(self) -> bytes:
        result = get_auth_result(SupportedBiometricTypes.FACE_ID)

        if result["error_code"] == 0:
            return result["hash"].encode()

        raise WinBioError(result["title"], result["error"], result["error_code"])


class FaceRecognitionBGAuthenticator(BackgroundAuthenticatorBase):
    """Face recognition background authenticator UI."""

    def get_window_data(self) -> BgWindowData:
        return {
            "window_title": "Face Recognition Authenticator",
            "title": "Look at the camera",
            "info": "Ensure your face is clearly visible to the camera.\n\
Please use the same face used during encryption.",
            "icon_path": os.path.abspath("ui/resources/face_recognition.ico"),
        }


class FaceRecognitionScanner(WinBioInterface):
    """Scan the face in the background while the background authenticator is running."""

    @property
    def winbio_id(self) -> SupportedBiometricTypes:
        return SupportedBiometricTypes.FACE_ID

    @property
    def background_authenticator(self) -> Type[BackgroundAuthenticatorBase]:
        return FaceRecognitionBGAuthenticator


def main() -> None:
    """Start the face recognition scanner."""
    winbio_main(FaceRecognitionScanner())


if __name__ == "__main__":
    main()
