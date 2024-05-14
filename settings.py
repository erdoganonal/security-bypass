"""General settings"""

from pathlib import Path

CONFIG_PATH = Path("~").expanduser() / ".security_bypass"
CREDENTIALS_FILE = CONFIG_PATH / ".credentials"

DFT_ENCODING = "utf-8"
MK_REQUEST_PARAM = "--mk-cli-request"
MK_ENV_NAME = "SECURITY_BYPASS_MK"

GUI = True

MIN_SLEEP_SECS_AFTER_KEY_SENT = 3
