"""get the list of files in the repository"""

import fnmatch
import subprocess
import sys
from pathlib import Path
from typing import Generator

from settings import WRAPPER_FILE
from updater.constants import UPDATER_FILE_NAME

EXCLUDED_FILES = [
    "*.txt",
    "*.toml",
    "*.zip",
    "*.sfx",
    ".gitignore",
    ".updater_options",
    "create_installer.py",
    "install.bat",
    WRAPPER_FILE.name,
    UPDATER_FILE_NAME,
]

EXCLUDED_FOLDERS = [
    ".github",
    ".vscode",
    "tests",
]

EXCEPTIONS = (Path("requirements.txt"),)


def _is_excluded(path: Path) -> bool:
    """check if the file is excluded"""
    if path in EXCEPTIONS:
        return False

    for excluded_file in EXCLUDED_FILES:
        if fnmatch.fnmatch(path.name, Path(excluded_file).name):
            return True

    return path.parts[0] in EXCLUDED_FOLDERS


def get_files() -> Generator[Path, None, None]:
    """get list of all files in the repository"""

    try:
        items = subprocess.check_output("git ls-tree -r HEAD --name-only", text=True).splitlines()
    except subprocess.CalledProcessError:
        sys.exit("Error: Not a git repository or no files in the repository.")
    except FileNotFoundError:
        sys.exit("Error: Git is not installed.")

    for item in items:
        path = Path(item)
        if _is_excluded(path):
            continue
        yield path
