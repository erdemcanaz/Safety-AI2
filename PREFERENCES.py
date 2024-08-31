import os
from pathlib import Path
PREFERENCES_FILE_PATH = Path(__file__).resolve()

SAFETY_AI_USER_INFO = {"username": "safety_ai", "password": "safety_ai_password", "personal_fullname": "Safety AI Robot"}

if os.name == "nt":  # For Windows (i.e development environment)
    SERVER_IP_ADDRESS = "192.168.0.26"
    CLEAR_TERMINAL_COMMAND = "cls"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH.parent/ "api_server" / "safety_ai.db"
    PRINT_MOUSE_COORDINATES = True
    ENCRYPTED_IMAGE_FOLDER = PREFERENCES_FILE_PATH.parent.parent / "safety_AI_volume" / "api_server" / "encrypted_images"
    ENCRYPTED_IMAGE_FOLDER_SSD = None
elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = "172.17.27.12"
    CLEAR_TERMINAL_COMMAND = "clear"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH.parent.parent / "safety_AI_volume" / "api_server" / "safety_ai.db"
    PRINT_MOUSE_COORDINATES = False
    ENCRYPTED_IMAGE_FOLDER = PREFERENCES_FILE_PATH.parent.parent / "safety_AI_volume" / "api_server" / "encrypted_images"
    ENCRYPTED_IMAGE_FOLDER_SSD = None
else:
    raise Exception("Unknown operating system")

