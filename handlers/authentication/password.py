"""password based authentication handler"""

from common import exceptions
from handlers.authentication.base import AuthenticationInterface, AuthenticationResult
from handlers.notification.base import NotificationController
from helpers.ui_helpers.pm.dialogs.password import PasswordDialog
from package_builder.registry import PBId, PBRegistry

PASSWORD_ERROR_USER_CANCELED = -1


class AuthenticationPassword(AuthenticationInterface):
    """Password based authentication handler"""

    def get_master_key(self) -> bytes:
        """get the master key"""

        notification = PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController)
        key = notification.user_input("Please enter the Master Key", "Enter your master key", hidden_text=True)

        if key is None:
            raise exceptions.EmptyMasterKeyError("Master key is empty")
        return key.encode()


def get_password_result() -> AuthenticationResult:
    """ask user to enter the password"""

    passwd = PasswordDialog().get()
    if passwd is None:
        return {"hash": "", "error": "Password entry canceled by user. Please try again", "error_code": PASSWORD_ERROR_USER_CANCELED}
    return {"hash": passwd, "error": "", "error_code": 0}
