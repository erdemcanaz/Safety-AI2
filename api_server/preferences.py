import os
from pathlib import Path
PREFERENCES_FILE_PATH = Path(__file__).resolve()

if os.name == "nt":  # For Windows
    SERVER_IP_ADDRESS = "192.168.0.26"
    PRINT_MOUSE_COORDINATES = True
    CLEAR_TERMINAL_COMMAND = "cls"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH.parent / "safety_ai.db"
elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = input("Server IP Address: ")
    PRINT_MOUSE_COORDINATES = False
    CLEAR_TERMINAL_COMMAND = "clear"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH.parent.parent.parent / "safety_ai_volume" / "api_server" / "safety_ai.db"

