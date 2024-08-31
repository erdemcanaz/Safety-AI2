import os
from pathlib import Path
PREFERENCES_FILE_PATH = Path(__file__).resolve()

if os.name == "nt":  # For Windows (i.e development environment)
    SERVER_IP_ADDRESS = "192.168.0.26"
    PRINT_MOUSE_COORDINATES = True
    CLEAR_TERMINAL_COMMAND = "cls"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH/ "api_server" / "safety_ai.db"
    PRINT_MOUSE_COORDINATES = True
    SAFETY_AI_USER_INFO = {"username": "safety_ai", "password": "TEST_PASSWORD", "personal_fullname": "Safety AI Robot"}
elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = "172.17.27.12"
    PRINT_MOUSE_COORDINATES = False
    CLEAR_TERMINAL_COMMAND = "clear"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH.parent.parent / "safety_AI_volume" / "api_server" / "safety_ai.db"
    PRINT_MOUSE_COORDINATES = False
    SAFETY_AI_USER_INFO = {"username": "safety_ai", "password": "TEST_PASSWORD", "personal_fullname": "Safety AI Robot"}
else:
    raise Exception("Unknown operating system")

