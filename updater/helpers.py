"""Helper functions for the updater."""

import enum
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, Generator, List

import requests


def restart() -> None:
    """restart the application"""

    python = sys.executable
    try:
        with subprocess.Popen(f"{python} {' '.join(sys.argv)}") as process:
            pass
    except KeyboardInterrupt:
        pass
    sys.exit(process.returncode)


def md5(path: Path | str) -> str:
    """Generate the md5 hash of a file."""

    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_single_file(url: str, path: Path) -> None:
    """Download a single file from the given URL."""

    response = requests.get(url, stream=True, timeout=100)
    response.raise_for_status()  # Ensure we got an OK response

    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


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


def get_update_list(hash_file_url: str) -> Generator[str, None, None]:
    """Return the list of files that need to be updated."""

    remote_hashes = get_remote_hashes(hash_file_url)

    for path, remote_hash in remote_hashes.items():
        try:
            local_hash = md5(path)
        except FileNotFoundError:
            # it is a new file
            yield path
            continue

        if local_hash != remote_hash:
            yield path


class NotifyType(enum.Enum):
    """Notification type."""

    DEBUG = enum.auto()
    INFO = enum.auto()
    QUESTION = enum.auto()


def cli_user_notify_callback(message: str, kind: NotifyType) -> bool:
    """Default user notify callback function."""

    if kind in (NotifyType.DEBUG, NotifyType.INFO):
        print(message)
    elif kind == NotifyType.QUESTION:
        return input(f"{message} (y/N): ").strip() == "y"
    return True


def check_for_updates(
    raw_remote_url: str,
    hash_file_path: str,
    user_notify_callback: Callable[[str, NotifyType], bool] = cli_user_notify_callback,
    complete_operation_callback: Callable[[], None] = restart,
) -> None:
    """Check for updates and notify the user if there are any."""

    user_notify_callback("Checking for updates...", NotifyType.INFO)

    update_list = list(get_update_list(f"{raw_remote_url}/{hash_file_path}"))
    if not update_list:
        user_notify_callback("No updates available.", NotifyType.INFO)
        return

    user_notify_callback("The following files need to be updated:\n" + "\n".join(update_list), NotifyType.DEBUG)

    if not user_notify_callback("Do you want to update?", NotifyType.QUESTION):
        # User does not want to update
        user_notify_callback("Update skipped.", NotifyType.INFO)
        return

    user_notify_callback("Downloading the new files, please wait...", NotifyType.INFO)

    for file in update_list:
        file = file.replace("\\", "/")
        user_notify_callback(f"downloading: {raw_remote_url}/{file}", NotifyType.DEBUG)
        download_single_file(f"{raw_remote_url}/{file}", Path(file))

    user_notify_callback("Updates downloaded successfully. Restarting the app.", NotifyType.INFO)

    complete_operation_callback()
