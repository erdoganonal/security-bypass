"""show a toast notification on Windows using the Windows Toaster library"""

import pathlib
import time
import winreg
from dataclasses import dataclass

from windows_toasts import (
    Toast,
    ToastActivatedEventArgs,
    ToastButton,
    ToastDismissalReason,
    ToastDismissedEventArgs,
    ToastDisplayImage,
    ToastDuration,
    ToastFailedEventArgs,
    ToastImagePosition,
    ToastInputTextBox,
)
from windows_toasts.toasters import InteractableWindowsToaster

from handlers.notification.base import MessageType, NotificationInterface
from handlers.notification.gui import NotificationGUI
from settings import ERROR_ICON, INFO_ICON, QUESTION_ICON, SECURITY_BYPASS_ICON, WARNING_ICON

TITLE = "Security Bypass"


class NotificationToast(NotificationInterface):
    """Show messages to the user with tray notifications"""

    def __init__(self, app_id: str | None = None, app_name: str | None = None, icon_path: pathlib.Path | None = None) -> None:
        self._app_id = app_id or "com.security_bypass"
        self._app_name = app_name or "Security Bypass"
        self._icon_path = icon_path or SECURITY_BYPASS_ICON

        self.self_register_hkey()

        self._gui_notification_handler = NotificationGUI()

    @staticmethod
    def register_hkey(app_id: str, app_name: str, icon_path: pathlib.Path | None = None) -> None:
        """Register the application in the registry"""

        if icon_path is not None:
            if not icon_path.exists():
                raise ValueError(f"Could not register the application: File {icon_path} does not exist")
            if icon_path.suffix != ".ico":
                raise ValueError(f"Could not register the application: File {icon_path} must be of type .ico")

        winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key_path = f"SOFTWARE\\Classes\\AppUserModelId\\{app_id}"
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path) as master_key:
            winreg.SetValueEx(master_key, "DisplayName", 0, winreg.REG_SZ, app_name)
            if icon_path is not None:
                winreg.SetValueEx(master_key, "IconUri", 0, winreg.REG_SZ, str(icon_path.resolve()))

    def self_register_hkey(self) -> None:
        """Register the application in the registry"""
        self.register_hkey(self._app_id, self._app_name, self._icon_path)

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        """Show a toast notification"""
        toaster = InteractableWindowsToaster(self._app_name, notifierAUMID=self._app_id)

        toast = Toast([title, message], duration=ToastDuration.Short)

        if msg_type in (MessageType.DEBUG, MessageType.INFO):
            icon = INFO_ICON
        elif msg_type == MessageType.WARNING:
            icon = WARNING_ICON
        elif msg_type in (MessageType.ERROR, MessageType.CRITICAL):
            icon = ERROR_ICON
        else:
            icon = SECURITY_BYPASS_ICON

        toast.images = [ToastDisplayImage.fromPath(icon, position=ToastImagePosition.AppLogo)]

        toaster.show_toast(toast)

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        """Ask the user a yes/no question"""

        toaster = InteractableWindowsToaster(self._app_name, notifierAUMID=self._app_id)

        toaster_callback = ToasterCallback(
            Toast([title, message], duration=ToastDuration.Long), action_ok_str="Yes", action_cancel_str="No"
        )
        toaster_callback.register()

        toaster.show_toast(toaster_callback.toast)
        toaster_callback.wait()

        return toaster_callback.result.response == toaster_callback.action_ok_str

    def user_input(self, message: str, title: str = "", hidden_text: bool = False) -> str | None:
        """Ask the user for input"""

        if hidden_text:
            return self._gui_notification_handler.user_input(message, title or TITLE, hidden_text)

        toaster = InteractableWindowsToaster(self._app_name, notifierAUMID=self._app_id)

        toaster_callback = ToasterCallback(
            Toast([title, message]), input_id="user_input", action_ok_str="Submit", action_cancel_str="Cancel"
        )
        toaster_callback.register()

        toaster.show_toast(toaster_callback.toast)
        toaster_callback.wait()

        return toaster_callback.result.response


class ToasterCallback:
    """Callback class for the toaster"""

    @dataclass
    class Result:
        """Result class for the toaster"""

        response: str | None = None
        reason: ToastDismissalReason | None = None
        completed: bool = False

    def __init__(self, toast: Toast, input_id: str | None = None, action_ok_str: str = "Yes", action_cancel_str: str = "No") -> None:
        self.action_ok_str = action_ok_str
        self.action_cancel_str = action_cancel_str
        self._input_id = input_id
        self.toast = toast

        self.result = self.Result()

    def register(self) -> None:
        """Register the toaster"""

        if self._input_id is not None:
            self.toast.AddInput(ToastInputTextBox(self._input_id))

        self.toast.AddAction(ToastButton(self.action_ok_str, self.action_ok_str))
        self.toast.AddAction(ToastButton(self.action_cancel_str, self.action_cancel_str))

        self.toast.images = [ToastDisplayImage.fromPath(QUESTION_ICON, position=ToastImagePosition.AppLogo)]

        self.toast.on_activated = self.activated
        self.toast.on_dismissed = self.dismissed
        self.toast.on_failed = self.failed

    def activated(self, args: ToastActivatedEventArgs) -> None:
        """Handle the activation of the toast"""
        ok = args.arguments == self.action_ok_str

        if ok:
            if self._input_id is None:
                self.result.response = self.action_ok_str
            elif args.inputs:
                self.result.response = args.inputs.get(self._input_id, None)
        else:
            self.result.response = None

        self.result.completed = True

    def dismissed(self, args: ToastDismissedEventArgs) -> None:
        """Handle the dismissal of the toast"""
        self.result.reason = args.reason
        self.result.completed = True

    def failed(self, _: ToastFailedEventArgs) -> None:
        """Handle the failure of the toast"""
        self.result.completed = True

    def wait(self) -> None:
        """Wait for the toaster to finish"""
        while not self.result.completed:
            time.sleep(0.1)
