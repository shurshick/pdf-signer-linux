import os

APP_VERSION = "1.1.0"
APP_NAME = "PDF Signer Linux"
APP_COPYRIGHT = "Copyright (c) 2026 shurshick"
APP_PROJECT_URL = "https://github.com/shurshick/pdf-signer-linux"
SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "pdfsigner")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
LOG_DIR = os.path.join(SETTINGS_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
