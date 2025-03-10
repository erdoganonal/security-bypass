"""Common enumerations and constants for authentication methods."""

from enum import Enum
from typing import Callable, Type, TypedDict

from handlers.authentication.base import AuthenticationInterface, AuthenticationResult
from handlers.authentication.face_recognition import AuthenticationFaceRecognition
from handlers.authentication.fingerprint import AuthenticationFingerprint
from handlers.authentication.password import AuthenticationPassword, get_password_result
from handlers.authentication.winbio.winbio_base import SupportedBiometricTypes, get_auth_result


class _AuthMethodProperties(TypedDict):
    auth_class: Type[AuthenticationInterface]
    get_auth_result: Callable[[], AuthenticationResult]
    admin_rights_required: bool


class AuthMethod(Enum):
    """Authentication method enumeration."""

    PASSWORD = "Password"
    FINGERPRINT = "Fingerprint"
    FACE_RECOGNITION = "FaceRecognition"

    def get_underlying_class(self) -> Type[AuthenticationInterface]:
        """Get the underlying class name."""
        return _METHOD_MAP[self]["auth_class"]

    @property
    def is_admin_rights_required(self) -> bool:
        """Check if admin rights are required."""
        return _METHOD_MAP[self]["admin_rights_required"]

    def get_auth_result(self) -> AuthenticationResult:
        """Get the authentication result."""
        return _METHOD_MAP[self]["get_auth_result"]()


_METHOD_MAP: dict[AuthMethod, _AuthMethodProperties] = {
    AuthMethod.PASSWORD: {
        "auth_class": AuthenticationPassword,
        "admin_rights_required": False,
        "get_auth_result": get_password_result,
    },
    AuthMethod.FINGERPRINT: {
        "auth_class": AuthenticationFingerprint,
        "admin_rights_required": True,
        "get_auth_result": lambda: get_auth_result(SupportedBiometricTypes.FINGERPRINT),
    },
    AuthMethod.FACE_RECOGNITION: {
        "auth_class": AuthenticationFaceRecognition,
        "admin_rights_required": True,
        "get_auth_result": lambda: get_auth_result(SupportedBiometricTypes.FACE_ID),
    },
}
