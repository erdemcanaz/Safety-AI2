import os
from pathlib import Path
PREFERENCES_FILE_PATH = Path(__file__).resolve()

# Definitions (Hardcoded)
DEFINED_CAMERA_STATUSES = ["active", "inactive"]
DEFINED_DEPARTMENTS = ["ISG", "KALITE", "GUVENLIK"]
DEFINED_AUTHORIZATIONS = [
            'MENAGE_USERS',
            'ISG_UI',
            'QUALITY_UI',
            'SECURITY_UI',
            'EDIT_RULES',
            'REPORTED_VIOLATIONS',
            'SUMMARY_PAGE',
            'UPDATE_CAMERAS',
            'IOT_DEVICES'
]

DEFINED_RULES = {
    "hardhat_violation": [
        "v1", # People are detected via pose detection. Then their head is centered with 320x320 image. Image is then resized to 640x640 and fed to the hardhat detection model.
    ],
    "restricted_area_violation": [
        "v1", # People are detected via pose detection. If their ankle is inside the restricted area, then it is a violation.
        "v2"  # People are detected via pose detection. If thier bbox-center is inside the restricted area, then it is a violation.
    ],
}

#============
SAFETY_AI_USER_INFO = {"username": "safety_ai", "password": "safety_ai_password", "personal_fullname": "Safety AI Robot"}
#TODO: set an interval for checking image integrity and remove images that are not in the database


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
PERSON_BBOX_BLUR_KERNEL_SIZE = 31 # Odd number
POSE_MODEL_BBOX_THRESHOLD_CONFIDENCE = 0.50
FORKLIFT_MODEL_BBOX_THRESHOLD_CONFIDENCE = 0.50
HARDHAT_MODEL_BBOX_THRESHOLD_CONFIDENCE = 0.35

MAXIMUM_NUMBER_OF_FETCHING_CAMERAS = 18 #24 is sufficient # The maximum number of camera stream fetchers that is fetching RTSP streams at the same time
CAMERA_UPDATE_INTERVAL_SECONDS = 900 # The interval in seconds for updating the camera information
CAMERA_RULES_UPDATE_INTERVAL_SECONDS = 20 # The interval in seconds for updating the camera rules

CAMERA_DECODING_RANDOMIZATION_RANGE = [0, 5] # The range of randomization for the decoding of the camera frames in seconds. Other frames are just grabbed and not decoded.

SAFETY_AI_VERBOSES = {
    'header_class_name_width': 20, # The width of the class name in the printed header
    "updating_camera_info": True,
    "camera_initialization": True,
    "CRUD_on_camera_info": True,
    "frame_fetching_starts": True,
    "frame_fetching_stops": True,
    "frame_decoded": False,
    "frame_decoding_failed": True,
    "error_raised_rtsp": True,
}

# Models module related parameters
MODELS_MODULE_VERBOSES = {
   "pose_detection_model_verbose": False,
   "hardhat_detection_model_verbose": False,
   "forklift_detection_model_verbose": False,
}

USED_MODELS = {
    "pose_detection_model_name": "yolov8x-pose", # yolov8n-pose, yolov8s-pose, yolov8m-pose, yolov8l-pose, yolov8x-pose
    "hardhat_detection_model_name": "hardhat_detector", # hardhat_detector
    "forklift_detection_model_name": "forklift_detector", # forklift_detector
}