"""base class for authentication handlers"""

import abc
import os
import typing

from common import exceptions
from settings import ENV_NAME_AUTH_KEY

if typing.TYPE_CHECKING:
    from handlers.authentication.methods import AuthMethod


class AuthenticationResult(typing.TypedDict):
    """Authentication result type."""

    hash: str
    title: str
    error: str
    error_code: int


class AuthenticationInterface(abc.ABC):
    """Base class for authentication handlers"""

    @abc.abstractmethod
    def get_master_key(self) -> bytes:
        """get the master key"""

    def reserved_method(self) -> None:
        """reserved method for future use"""


class AuthenticationController(AuthenticationInterface):
    """Base class for authentication handlers"""

    def __init__(self, auth_method: "AuthMethod") -> None:
        self._authentication_handler = auth_method.get_underlying_class()()

    def get_master_key(self) -> bytes:
        # check if the master key is set in the environment variable
        if key_from_env_var := os.getenv(ENV_NAME_AUTH_KEY):
            return key_from_env_var.encode()

        try:
            return self._authentication_handler.get_master_key()
        except KeyboardInterrupt as exc:
            raise exceptions.UserCancelledError() from exc
