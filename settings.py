"""General settings"""

from pathlib import Path

CURRENT_DIR = Path(__file__).parent
CONFIG_PATH = Path("~").expanduser() / ".security_bypass_dev"
CREDENTIALS_FILE = CONFIG_PATH / ".credentials"

WRAPPER_FILE = CURRENT_DIR / "security_bypass_wrapper.py"
USER_PREFERENCES_FILE = CONFIG_PATH / ".config.json"

DATA_DIR = CURRENT_DIR / "data"

SECURITY_BYPASS_ICON = DATA_DIR / "security_bypass.ico"

VERSION = "1.1.0"

DFT_ENCODING = "utf-8"
ENV_NAME_AUTH_KEY = "SECURITY_BYPASS_AUTHENTICATION_KEY"
ENV_NAME_DEBUG = "SECURITY_BYPASS_DEBUG"
ENV_NAME_SKIP_UPDATE = "SECURITY_BYPASS_SKIP_UPDATE"

MIN_SLEEP_SECS_AFTER_KEY_SENT = 3
MAX_KEY_SENT_ATTEMPTS = 10

ASK_PASSWORD_ON_LOCK = False

DEBUG = True

RAW_REMOTE_URL = "https://raw.github.com/erdoganonal/security-bypass/windowless_authentication_temp"
UPDATER_HASH_FILE = ".updater.hashes"

ABOUT_MESSAGE = """Password Manager - Security Bypass
Developed by Erdoğan Önal
"""

ABOUT_INFO = """This tool allows you to bypass the password windows by entering the passwords automatically.
All you have to do is define a few things like the title of the window that you want to bypass, \
and a string to search in the window. The rest is the password that you need to pass.

This tool is designed to make managing these inputs easy and efficient.
Please use responsibly and only for legitimate purposes.
"""
