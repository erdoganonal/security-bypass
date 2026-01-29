"""Main module for the authentication package."""

import os
import sys

from handlers.authentication import face_recognition, fingerprint
from handlers.authentication.winbio.winbio_base import SupportedBiometricTypes, unknown_auth_method_result_main

os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        unknown_auth_method_result_main()

    if sys.argv[1].upper() == SupportedBiometricTypes.FINGERPRINT.name:
        fingerprint.main()
    elif sys.argv[1].upper() == SupportedBiometricTypes.FACE_ID.name:
        face_recognition.main()
    else:
        unknown_auth_method_result_main()
