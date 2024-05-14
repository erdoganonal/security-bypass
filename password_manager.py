"""Helps you to manage the passwords"""

import sys
from getpass import getpass
from typing import Any, Callable, Dict

from config import ConfigManager
from config.config import WindowConfig
from config.config_key_manager import validate_and_get_mk
from settings import DFT_ENCODING


def main() -> None:
    """starts from here"""
    PasswordManager().loop()


class ContinueLoopError(Exception):
    """This is a fake error. When this error is raised the loop will continue"""


class PasswordManager:
    """Helper class for manage passwords"""

    def __init__(self) -> None:
        self._name_action_map: Dict[str, Callable[[], Any]] = {
            "Show Passwords": self.show_passwords,
            "Add New Passkey": self.add_new_pwd,
            "Delete a Passkey": self.delete_pwd,
            "List Passkey Titles": self.list_titles,
            "Delete Passkey Title": self.delete_title,
            "Change Master Key": self.change_mk,
        }

        self._idx_name_map = {str(idx): name for idx, name in enumerate(self._name_action_map, start=1)}
        self._is_active = False

        try:
            self._config_mgr = ConfigManager(key=validate_and_get_mk())
            self._config = self._config_mgr.get_config()
        except ValueError:
            print("Cannot load configurations. The Master Key is wrong.")
            sys.exit(1)
        except KeyError as err:
            print(err.args[0])
            sys.exit(1)

    def _get_user_input(self) -> None:
        print()
        for idx, name in self._idx_name_map.items():
            print(f"[{idx}] {name}")

        response = input("\nSelect an action: ")
        try:
            self._name_action_map[self._idx_name_map[response]]()
        except KeyError as err:
            print("Invalid action!")
            raise ContinueLoopError() from err

    def _loop(self) -> None:
        while self._is_active:
            try:
                self._get_user_input()
            except ContinueLoopError:
                pass

    def loop(self) -> None:
        """Start a user input loop until KeyboardInterrupt is received"""
        if self._is_active:
            return

        self._is_active = True
        try:
            self._loop()
        except KeyboardInterrupt:
            self._is_active = False

    def __save_config(self) -> None:
        self._config_mgr.save_config(self._config)

    def __get_title(self, list_titles: bool = True) -> WindowConfig:
        if list_titles:
            self.list_titles()

        title = input("Please select the title: ")
        try:
            return next(window for window in self._config.windows if window.window_title == title)
        except StopIteration as err:
            print("The Title does not exist!")
            raise ContinueLoopError() from err

    def _list_names(self, window: WindowConfig) -> None:
        print("Available passkey names listed below:")
        for name in window.passkey_data:
            print(f" - {name}")

    def __get_name(self, window: WindowConfig, list_names: bool = True) -> str:
        if list_names:
            self._list_names(window)

        name = input("Please select the name: ")
        if name in window.passkey_data:
            return name

        print("The name does not exist!")
        raise ContinueLoopError()

    def show_passwords(self) -> None:
        """Show the currently saved passwords"""
        print()
        print(self._config.to_user_str())

    def add_new_pwd(self) -> None:
        """Add a new password"""
        title = input("Please enter the title or title pattern: ")
        name = input("Please enter a name for your key: ")
        passkey = getpass("Please enter the new passkey: ")

        print(f"title: {title}\nname: {name}")
        print(passkey)
        if "y" != input("Is the parameters correct?[y/N]: "):
            self.add_new_pwd()
            return

        try:
            window = next(window for window in self._config.windows if window.window_title == title)
            window.passkey_data[name] = passkey
        except StopIteration:
            self._config.windows.append(WindowConfig(window_title=title, passkey_data={name: passkey}))

        self.__save_config()
        print("\nThe new passkey has been added successfully!")

    def delete_pwd(self) -> None:
        """Delete a passkey from the config file"""
        window = self.__get_title(list_titles=True)
        name = self.__get_name(window)

        del window.passkey_data[name]

        self.__save_config()
        print("\nThe passkey has been deleted!")

    def list_titles(self) -> None:
        """List all available title"""
        print("Available titles are listed below: ")
        for window in self._config.windows:
            print(f" - {window.window_title}")

    def delete_title(self) -> None:
        """Delete a title"""
        window = self.__get_title()
        if window.passkey_data:
            response = input("There is at least one passkey found. Are you sure to delete this title with it's content?[y/N]: ")
            if response != "y":
                raise ContinueLoopError()

        self._config.windows.remove(window)
        self.__save_config()
        print(f"The Title[{window.window_title}] has been deleted!")

    def change_mk(self) -> None:
        """Change the config file master key"""
        new_key = getpass("New Master Key: ").encode(encoding=DFT_ENCODING)
        self._config_mgr.change_master_key(new_key)


if __name__ == "__main__":
    main()
