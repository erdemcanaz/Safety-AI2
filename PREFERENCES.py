import os, psutil, platform, subprocess
if os.name == "nt": import win32api, win32file
from pathlib import Path
import psutil, datetime

def update_data_folder_and_DATA_FOLDER_PATH(is_external:bool = None, data_folder_path:Path = None, must_existing_data_subfolder_paths = None):
    if data_folder_path is None:
        raise ValueError("data_folder_path_external is None")
    
    if is_external:
        if not os.path.exists(data_folder_path):
            data_folder_path = None #reset data_folder_path_external
            return data_folder_path
    else:
        if not os.path.exists(data_folder_path):
            os.makedirs(data_folder_path, exist_ok=True)           
    
    for subfolder_key, subfolder_path in must_existing_data_subfolder_paths.items():
        if not os.path.exists(data_folder_path / subfolder_path):
           os.makedirs(data_folder_path / subfolder_path, exist_ok=True)
           with open(data_folder_path / subfolder_path / "created_at.txt", "w") as f:
               f.write(f"Created at: {datetime.datetime.now()}:\nData Folder Path: {data_folder_path}\nSubfolder Key: {subfolder_key}\nSubfolder Path: {subfolder_path}")
           
    return Path(data_folder_path)

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
SAFETY_AI_USER_INFO = {"username": "safety_ai", "password": "safety_ai_password", "personal_fullname": "Safety AI Robot"}    
MUST_EXISTING_DATA_SUBFOLDER_PATHS = { 
        #NOTE: NEVER EVER CHANGE THE KEY NAMES
        "logs": Path("safety_ai/logs"),
        "encrypted_images":  Path("safety_ai/encrypted_images"),
        "pdf_reports":  Path("safety_ai/pdf_reports"),
        "database_backups":  Path("safety_ai/database_backups"),
        "database":  Path("safety_ai/database"),
    }

if os.name == "nt":  # For Windows (i.e development environment)
    SERVER_IP_ADDRESS = "192.168.0.26"
    CLEAR_TERMINAL_COMMAND = "cls"
    PRINT_MOUSE_COORDINATES = True
    
    DATA_FOLDER_PATH_LOCAL = update_data_folder_and_DATA_FOLDER_PATH(is_external = False, data_folder_path= Path(__file__).parent.resolve() /'api_server_2' / 'local_ssd_data_folder', must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    DATA_FOLDER_PATH_EXTERNAL = update_data_folder_and_DATA_FOLDER_PATH(is_external = True, data_folder_path= Path("E:"), must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)

    print(f"DATA_FOLDER_PATH_LOCAL: {DATA_FOLDER_PATH_LOCAL}")
    SQL_DATABASE_FOLDER_PATH_LOCAL = DATA_FOLDER_PATH_LOCAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['database']
    SQL_DATABASE_FOLDER_PATH_EXTERNAL = DATA_FOLDER_PATH_EXTERNAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['database']

elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = "172.17.27.12"
    CLEAR_TERMINAL_COMMAND = "clear"
    PRINT_MOUSE_COORDINATES = False

    # This is the volume path inside the docker container connected to local SSD
    DATA_FOLDER_PATH_LOCAL = update_data_folder_and_DATA_FOLDER_PATH(is_external=False, data_folder_path= Path(__file__).parent.parent  / 'local_ssd_data_folder', must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    # This is the volume path inside the docker container connected to external SSD
    DATA_FOLDER_PATH_EXTERNAL = update_data_folder_and_DATA_FOLDER_PATH(is_external=True, data_folder_path= "/home/external_ssd_data_folder", must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)

    SQL_DATABASE_FOLDER_PATH_LOCAL = DATA_FOLDER_PATH_LOCAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['database']
    SQL_DATABASE_FOLDER_PATH_EXTERNAL = DATA_FOLDER_PATH_EXTERNAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['database']
else:
    raise Exception("Unknown operating system")

# Safety-AI related parameters
PERSON_BBOX_BLUR_KERNEL_SIZE = 31 # Odd number
POSE_MODEL_BBOX_THRESHOLD_CONFIDENCE = 0.50
FORKLIFT_MODEL_BBOX_THRESHOLD_CONFIDENCE = 0.50
HARDHAT_MODEL_BBOX_THRESHOLD_CONFIDENCE = 0.35

MAXIMUM_NUMBER_OF_STORED_FRAMES = 10 # The maximum number of previous frames that are stored for each camera. (RAM usage is proportional to this number)
MAXIMUM_NUMBER_OF_FETCHING_CAMERAS = 32 # The maximum number of camera stream fetchers that is fetching RTSP streams at the same time
CAMERA_UPDATE_INTERVAL_SECONDS = 900 # The interval in seconds for updating the camera information
CAMERA_RULES_UPDATE_INTERVAL_SECONDS = 20 # The interval in seconds for updating the camera rules

CAMERA_DECODING_RANDOMIZATION_RANGE = [0, 7.5] # The range of randomization for the decoding of the camera frames in seconds. Other frames are just grabbed and not decoded.

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

SHOW_FRAMES = {
    "combined_violation_frame": True,
    "show_all_frames": True,
}
