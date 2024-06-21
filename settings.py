"""General settings"""

from pathlib import Path

CURRENT_DIR = Path(__file__).parent
CONFIG_PATH = Path("~").expanduser() / ".security_bypass"
CREDENTIALS_FILE = CONFIG_PATH / ".credentials"

WRAPPER_FILE = CURRENT_DIR / "security_bypass_wrapper.py"
TOOL_CONFIG_FILE = CONFIG_PATH / ".config.json"

DATA_DIR = CURRENT_DIR / "data"

SECURITY_BYPASS_ICON = DATA_DIR / "security_bypass.ico"

VERSION = "1.1.0"

DFT_ENCODING = "utf-8"
MK_REQUEST_PARAM = "--mk-cli-request"
MK_ENV_NAME = "SECURITY_BYPASS_MK"
DBG_ENV_NAME = "SECURITY_BYPASS_DEBUG"

GUI = True

MIN_SLEEP_SECS_AFTER_KEY_SENT = 3
MAX_KEY_SENT_ATTEMPTS = 10

ASK_PASSWORD_ON_LOCK = False

PYQT_UI = True

DEBUG = True

ABOUT_MESSAGE = """Password Manager - Security Bypass
Developed by Erdoğan Önal
"""

ABOUT_INFO = """This tool allows you to bypass the password windows by entering the passwords automatically.
All you have to do is define a few things like the title of the window that you want to bypass, \
and a string to search in the window. The rest is the password that you need to pass.

This tool is designed to make managing these inputs easy and efficient.
Please use responsibly and only for legitimate purposes.
"""
