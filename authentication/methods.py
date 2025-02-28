"""Common enumerations and constants."""

from enum import Enum


class AuthMethod(Enum):
    """Authentication method enumeration."""

    PASSWORD = "Password"
    FINGERPRINT = "Fingerprint"
