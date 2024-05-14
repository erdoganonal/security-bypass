"""creates a zip file for self extracting executable"""

import fnmatch
import subprocess
from pathlib import Path
from typing import Generator, Iterable, TypeVar

from installer import Installer, InstallerData
from generate_all import main as generate_all

CURRENT_DIR = Path(__file__).parent
INSTALLER_DIR = CURRENT_DIR / "installer"

WRAPPER_FILE = CURRENT_DIR / "security_bypass_wrapper.py"

CONFIG_FILE = INSTALLER_DIR / "Config.txt"
INSTALLER_SCRIPT = INSTALLER_DIR / "install.bat"
ZIP_APP_FILENAME = CURRENT_DIR / "windows_security_bypass.zip"
EXE_APP_FILENAME = CURRENT_DIR / "windows_security_bypass_installer.exe"


_T = TypeVar("_T")

EXCLUDED_FILES = [
    __file__,
    "*.bat",
    "*.txt",
    "*.toml",
    "*.zip",
    "*.sfx",
]

EXCLUDED_FOLDERS = [
    ".vscode",
    ".gitignore",
    "tests",
]

ADDITIONAL = [
    WRAPPER_FILE,
    CURRENT_DIR / "requirements.txt",
    CURRENT_DIR / "generated" / "ui_generated_add_item_dialog.py",
    CURRENT_DIR / "generated" / "ui_generated_get_passkey_dialog.py",
    CURRENT_DIR / "generated" / "ui_generated_get_password_dialog.py",
    CURRENT_DIR / "generated" / "ui_generated_main.py",
]


def main() -> None:
    """starts from here"""
    generate_all()
    generate_wrapper_file()

    files = get_files_to_archive()
    Installer.create(
        InstallerData(name=EXE_APP_FILENAME, config_file=CONFIG_FILE, post_script=INSTALLER_SCRIPT, zip_file=ZIP_APP_FILENAME),
        _extended(files, ADDITIONAL),
    )


def _extended(*iterables: Iterable[_T]) -> Generator[_T, None, None]:
    for it in iterables:
        yield from it


def _is_excluded(path: Path) -> bool:
    for excluded_file in EXCLUDED_FILES:
        if fnmatch.fnmatch(path.name, excluded_file):
            return True

    return path.parts[0] in EXCLUDED_FOLDERS


def generate_wrapper_file() -> None:
    """generate the wrapper file"""

    content = '''"""wrapper for the main application to catch unhandled exceptions"""

try:
    from security_bypass import main

    main()
except Exception as e:
    with open("error.log", "a+", encoding="utf-8") as error_fd:
        error_fd.write(str(e))

    raise SystemExit(1) from e
'''

    with open(WRAPPER_FILE, "w", encoding="utf-8") as wrapper_fd:
        wrapper_fd.write(content)


def get_files_to_archive() -> Generator[Path, None, None]:
    """get list of all files to include in the zip file"""
    for item in subprocess.check_output("git ls-tree -r main --name-only", text=True).splitlines():
        path = Path(item)
        if _is_excluded(path):
            continue
        yield path


if __name__ == "__main__":
    try:
        main()
    finally:
        WRAPPER_FILE.unlink(missing_ok=True)
