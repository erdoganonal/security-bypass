"""General settings"""

from pathlib import Path

CONFIG_PATH = Path("~").expanduser() / ".security_bypass"
CREDENTIALS_FILE = CONFIG_PATH / ".credentials"

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
