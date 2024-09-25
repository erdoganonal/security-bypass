"""common.py - Common functions for the updater handlers."""

import subprocess
import sys
from functools import cache
from pathlib import Path

GLOBALS = {
    "verbose": False,
}

_REMOTE_RAW_URL_CACHE_PATH = Path(".updater_remote_raw_url_cache")


@cache
def get_remote_raw_url() -> str:
    """Get the raw URL of the remote repository."""

    if _REMOTE_RAW_URL_CACHE_PATH.exists():
        with open(_REMOTE_RAW_URL_CACHE_PATH, "r", encoding="utf-8") as cache_fd:
            return cache_fd.read()

    remote_url = subprocess.check_output("git remote get-url origin", text=True).strip()
    remote_name = subprocess.check_output("git remote", text=True).strip()
    default_branch = "main"
    for line in subprocess.check_output(f"git remote show {remote_name}", text=True).splitlines():
        if "HEAD branch" in line:
            default_branch = line.split(":")[1].strip()
            break

    *_, user, repo = remote_url.replace(".git", "").split("/")
    remote_raw_url = f"https://raw.github.com/{user}/{repo}/{default_branch}"
    with open(_REMOTE_RAW_URL_CACHE_PATH, "w", encoding="utf-8") as cache_fd:
        cache_fd.write(remote_raw_url)
    return remote_raw_url


def error(message: str = "") -> None:
    """Print the error message and exit the program."""
    print(f"Error: {message}")
    sys.exit(1)


def verbose(message: str = "") -> None:
    """Print the message if the verbose flag is set."""
    if GLOBALS["verbose"]:
        print(message)
