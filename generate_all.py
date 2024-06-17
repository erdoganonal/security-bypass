"""generates the pyqt files from *ui files"""

import os
import sys
from pathlib import Path

UI_PY_MAP = {
    "ui/password_manager.ui": "generated/ui_generated_main.py",
    "ui/add_item_dialog.ui": "generated/ui_generated_add_item_dialog.py",
    "ui/get_password_dialog.ui": "generated/ui_generated_get_password_dialog.py",
    "ui/get_passkey_dialog.ui": "generated/ui_generated_get_passkey_dialog.py",
    "ui/import_config_dialog.ui": "generated/ui_generated_import_config_dialog.py",
}

GENERATED = Path("generated")


def main() -> None:
    """starts from here"""

    GENERATED.mkdir(exist_ok=True)
    (GENERATED / "__init__.py").touch(exist_ok=True)

    for ui, py in UI_PY_MAP.items():
        exit_code = os.system(f"pyuic6.exe {ui} -o {py}")
        if exit_code != 0:
            sys.exit(f"failed to generate python file for: {ui}. exit code: {exit_code}")
    print("files are generated successfully.")

    adjust_for_static_analysis_tools()


def adjust_for_static_analysis_tools() -> None:
    """add suppression messages for static analysis"""
    for py in UI_PY_MAP.values():
        with open(py, "r", encoding="utf-8") as py_r_fd:
            lines = py_r_fd.readlines()

        lines.insert(0, "# pylint: disable=all\n")
        lines.insert(1, "# type: ignore\n")

        with open(py, "w", encoding="utf-8") as py_w_fd:
            py_w_fd.writelines(lines)


if __name__ == "__main__":
    main()
