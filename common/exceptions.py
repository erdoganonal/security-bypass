"""Includes tool specific exceptions."""

import abc
from typing import NoReturn

from common.exit_codes import ExitCodes


class ToolError(Exception, abc.ABC):
    """Base class for all exceptions in this module."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    @property
    @abc.abstractmethod
    def get_error_code(self) -> ExitCodes:
        """Return the error code."""

    def exit(self) -> NoReturn:
        """Exit the program."""
        self.get_error_code.exit()


class ConfigError(ToolError, FileNotFoundError):
    """Raised when there is an issue with the configuration file."""


class ConfigFileNotFoundError(ConfigError):
    """Raised when the configuration file is not found."""

    @property
    def get_error_code(self) -> ExitCodes:
        return ExitCodes.CREDENTIAL_FILE_DOES_NOT_EXIST


class MasterKeyError(ToolError):
    """Raised when there is an issue with the master key."""


class WrongMasterKeyError(MasterKeyError):
    """Raised when the master key is wrong."""

    @property
    def get_error_code(self) -> ExitCodes:
        return ExitCodes.WRONG_MASTER_KEY


class WrongMasterKeyFormat(MasterKeyError):
    """Raised when the master key's type is wrong."""

    @property
    def get_error_code(self) -> ExitCodes:
        return ExitCodes.WRONG_MASTER_KEY_FORMAT


class EmptyMasterKeyError(MasterKeyError):
    """Raised when the master key is empty."""

    @property
    def get_error_code(self) -> ExitCodes:
        return ExitCodes.EMPTY_MASTER_KEY


class WinBioError(ToolError):
    """WinBio error class."""

    def __init__(self, message: str, error_code: int) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)

    @property
    def get_error_code(self) -> ExitCodes:
        return ExitCodes.WINBIO_ERROR


class UserCancelledError(ToolError, KeyboardInterrupt):
    """Raised when the user cancels the operation."""

    @property
    def get_error_code(self) -> ExitCodes:
        return ExitCodes.USER_CANCELLED
