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

# Safety-AI related parameters
CAMERA_UPDATE_INTERVAL_SECONDS = 900 # The interval in seconds for updating the camera information
CAMERA_RULES_UPDATE_INTERVAL_SECONDS = 20 # The interval in seconds for updating the camera rules

CAMERA_DECODING_RANDOMIZATION_RANGE = [0, 10] # The range of randomization for the decoding of the camera frames in seconds. Other frames are just grabbed and not decoded.
SAFETY_AI_VERBOSES = {
    'header_class_name_width': 20, # The width of the class name in the printed header
    "updating_camera_info": True,
    "camera_initialization": True,
    "CRUD_on_camera_info": True,
    "frame_fetching_starts": True,
    "frame_fetching_stops": True,
    "frame_decoded": True,
    "frame_decoding_failed": True,
    "error_raised_rtsp": True,
}

# Models module related parameters
MODELS_MODULE_VERBOSES = {
   "pose_detection_model_verbose": True,
}