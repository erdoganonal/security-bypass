"""Helper functions for the updater."""

import enum
import hashlib
from functools import lru_cache as cache
from pathlib import Path
from typing import Callable, Dict, Generator, List

import requests


class NotifyType(enum.Enum):
    """Notification type."""

    DEBUG = enum.auto()
    INFO = enum.auto()
    QUESTION = enum.auto()
    ERROR = enum.auto()


def cli_user_notify_callback(message: str, kind: NotifyType) -> bool:
    """Default user notify callback function."""

    if kind in (NotifyType.DEBUG, NotifyType.INFO):
        print(message)
    elif kind == NotifyType.QUESTION:
        return input(f"{message} (y/N): ").strip() == "y"
    return True


class _NotificationManager:
    def __init__(self, user_notify_callback: Callable[[str, NotifyType], bool]) -> None:
        self.user_notify_callback = user_notify_callback

    @cache
    def notify(self, message: str, kind: NotifyType) -> bool:
        """Notify the user with the given message and kind."""
        return self.user_notify_callback(message, kind)

    def reserved(self) -> None:
        """Reserved for future use."""


class UpdateHelper:
    """Helper class for updating the application."""

    def __init__(
        self, raw_remote_url: str, hash_file_path: str, user_notify_callback: Callable[[str, NotifyType], bool] = cli_user_notify_callback
    ):
        self.raw_remote_url = raw_remote_url
        self.hash_file_path = hash_file_path
        self.user_notify_callback = user_notify_callback
        self._update_list: List[str] | None = None
        self._notification_manager = _NotificationManager(user_notify_callback)

    @staticmethod
    def md5(path: Path | str) -> str:
        """Generate the md5 hash of a file."""

        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def download_single_file(url: str, path: Path) -> None:
        """Download a single file from the given URL."""

        response = requests.get(url, stream=True, timeout=100)
        response.raise_for_status()  # Ensure we got an OK response

        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    @staticmethod
    def get_remote_hashes(hash_file_url: str) -> Dict[str, str]:
        """Return the hashes of the files on the remote server."""

        response = requests.get(hash_file_url, timeout=100)
        response.raise_for_status()  # Ensure we got an OK response

        hashes: List[str] = response.content.decode("utf-8").splitlines()

        hashes_dict = {}
        for hash_line in hashes[2:]:
            if not hash_line.strip():
                continue

            md5_hash, path = hash_line.strip().split(" ", 1)
            hashes_dict[path] = md5_hash

        return hashes_dict

    @classmethod
    def get_update_list(cls, hash_file_url: str) -> Generator[str, None, None]:
        """Return the list of files that need to be updated."""

        remote_hashes = cls.get_remote_hashes(hash_file_url)

        for path, remote_hash in remote_hashes.items():
            try:
                local_hash = cls.md5(path)
            except FileNotFoundError:
                # it is a new file
                yield path
                continue

            if local_hash != remote_hash:
                yield path

    def check_for_updates(self, max_retries: int = 5, report_error: bool = True) -> bool | None:
        """Check for updates and notify the user if there are any."""

        for _ in range(max_retries):
            try:
                return self._check_for_updates()
            except (requests.exceptions.RequestException,) as e:
                if report_error:
                    raise e
                self._notify_user("Failed to check for updates. Retrying...", NotifyType.ERROR)
                return False

        self._notify_user("Failed to update... Please try again later.", NotifyType.ERROR)
        return False

    def _notify_user(self, message: str, kind: NotifyType) -> bool:
        if self._update_list is None:
            return True
        return self.user_notify_callback(message, kind)

    def _check_for_updates(self) -> bool | None:
        self._notification_manager.notify("Checking for updates...", NotifyType.INFO)

        if self._update_list is None:
            self._update_list = list(self.get_update_list(f"{self.raw_remote_url}/{self.hash_file_path}"))

        if not self._update_list:
            self._notification_manager.notify("No updates available.", NotifyType.INFO)
            return None

        if not self._notification_manager.notify("An update available. Do you want to update?", NotifyType.QUESTION):
            # User does not want to update
            self._notification_manager.notify("Update skipped.", NotifyType.INFO)
            return None

        self._notification_manager.notify("Downloading the new files, please wait...", NotifyType.INFO)

        for file in self._update_list[:]:
            file_replaced = file.replace("\\", "/")
            self._notification_manager.notify(f"downloading: {self.raw_remote_url}/{file_replaced}", NotifyType.DEBUG)
            self.download_single_file(f"{self.raw_remote_url}/{file}", Path(file))

            self._update_list.remove(file)

        self._notification_manager.notify("Updates downloaded successfully. Restarting the app.", NotifyType.INFO)

        return True


def check_for_updates(
    raw_remote_url: str,
    hash_file_path: str,
    user_notify_callback: Callable[[str, NotifyType], bool] = cli_user_notify_callback,
    max_retries: int = 5,
    report_error: bool = True,
) -> bool | None:
    """Check for updates and notify the user if there are any."""

    updater = UpdateHelper(raw_remote_url, hash_file_path, user_notify_callback)
    return updater.check_for_updates(max_retries, report_error)
