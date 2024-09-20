import os, psutil, platform, subprocess
if os.name == "nt": import win32api, win32file
from pathlib import Path
import psutil, datetime, time

#check if year is less than 2024, raise error
if datetime.datetime.now().year < 2024:
    raise ValueError("System year is less than 2024, Please ensure the system date and time is correct, best way to connect device to the internet and it will likely to automatically update the date and time")

def update_data_folder(is_external:bool = None, data_folder_path:Path = None, must_existing_data_subfolder_paths = None):   
    if data_folder_path == None or not isinstance(data_folder_path, Path):
        raise ValueError("data_folder_path is None or not a Path object")
    
    if is_external:
        is_parent_folder_accessible = os.path.isdir(data_folder_path.parent) and os.access(data_folder_path.parent, os.R_OK | os.W_OK)
        is_folder_exists = os.path.isdir(data_folder_path)
        if is_parent_folder_accessible and not is_folder_exists:
            os.makedirs(data_folder_path, exist_ok=True)
        else:
            return # The external drive is not mounted to the container properly, thus can not create the data_folder_path and its subfolders
    else:
        is_parent_folder_accessible = os.path.isdir(data_folder_path.parent) and os.access(data_folder_path.parent, os.R_OK | os.W_OK)
        is_folder_exists = os.path.isdir(data_folder_path)
        print(f"[INFO] Checking if the folder '{data_folder_path}' is accessible")
        print(f"[INFO] is_parent_folder_accessible: {is_parent_folder_accessible}, is_folder_exists: {is_folder_exists}")
        print(f"[INFO] is_external: {is_external}, data_folder_path: {data_folder_path}, must_existing_data_subfolder_paths: {must_existing_data_subfolder_paths}")
        if is_parent_folder_accessible and not is_folder_exists:
            os.makedirs(data_folder_path, exist_ok=True)
        else:
            return            
    
    for subfolder_key, subfolder_path in must_existing_data_subfolder_paths.items():
        if not os.path.exists(data_folder_path / subfolder_path):
           os.makedirs(data_folder_path / subfolder_path, exist_ok=True)
           with open(data_folder_path / subfolder_path / "created_at.txt", "w") as f:
               f.write(f"Created at: {datetime.datetime.now()}:\nData Folder Path: {data_folder_path}\nSubfolder Key: {subfolder_key}\nSubfolder Path: {subfolder_path}")
           
    return Path(data_folder_path)

def check_if_folder_accesible(folder_path: Path = None):  
    print(f"[INFO] Checking if the folder '{folder_path}' is accessible")  
    if not isinstance(folder_path, Path):
        return False
    return os.path.isdir(folder_path) and os.access(folder_path, os.R_OK | os.W_OK)

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

        # safety_ai/ ==============================
        "logs": Path("safety_ai/logs"),
        "camera_module_logs": Path("safety_ai/logs/sql_module_logs"),
        "frame_evaluator_logs": Path("safety_ai/logs/frame_evaluator_module_logs"),
        "models_module_logs": Path("safety_ai/logs/models_module_logs"),
        "safety_ai_api_logs": Path("safety_ai/logs/safety_ai_api_dealer_module_logs"),
        
        "encrypted_images":  Path("safety_ai/encrypted_images"),
        "pdf_reports":  Path("safety_ai/pdf_reports"),
        "database_backups":  Path("safety_ai/database_backups"),
        "database":  Path("safety_ai/database"),

        # api_server_2/ ==============================
        "api_server_logs": Path("api_server_2/logs"),
        "sql_module_logs": Path("api_server_2/logs/sql_module_logs"),
        "fast_api_module_logs": Path("api_server_2/logs/fast_api_module_logs"),
        "server_requests_logs": Path("api_server_2/logs/server_requests_logs"),

    }

if os.name == "nt":  # For Windows (i.e development environment)
    print("[INFO] Windows OS detected")
    SERVER_IP_ADDRESS = "192.168.0.26"
    CLEAR_TERMINAL_COMMAND = "cls"
    PRINT_MOUSE_COORDINATES = True
    
    # ENSURE THAT THE LOCAL SSD and EXTERNAL USB IS MOUNTED TO THE CONTAINER PROPERLY
    DATA_FOLDER_PATH_LOCAL = Path(__file__).parent.resolve() /'api_server_2' / 'local_ssd_data_folder'
    DATA_FOLDER_PATH_EXTERNAL = Path("E:")
    print(f"[INFO] The local data folder path is set to:'{DATA_FOLDER_PATH_LOCAL}'")
    print(f"[INFO] The external data folder path is set to: '{DATA_FOLDER_PATH_EXTERNAL}'")

    update_data_folder(is_external = False, data_folder_path= DATA_FOLDER_PATH_LOCAL , must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    update_data_folder(is_external = True, data_folder_path= DATA_FOLDER_PATH_EXTERNAL, must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    is_local_available = check_if_folder_accesible(DATA_FOLDER_PATH_LOCAL)
    is_external_available = check_if_folder_accesible(DATA_FOLDER_PATH_EXTERNAL)
    print(f"[INFO] The local path '{DATA_FOLDER_PATH_LOCAL}' : {'is available' if is_local_available else 'is not available'}")
    print(f"[INFO] The external path '{DATA_FOLDER_PATH_EXTERNAL}' : {'is available' if is_external_available else 'is not available'}")

    if not is_local_available:
        raise Exception(f"Local data folder path '{DATA_FOLDER_PATH_LOCAL}' is not accessible")
    if not is_external_available:
        raise Exception(f"External data folder path '{DATA_FOLDER_PATH_EXTERNAL}' is not accessible Please ensure the external drive is connected to 'E:' drive")
                        
    SQL_DATABASE_FOLDER_PATH_LOCAL = DATA_FOLDER_PATH_LOCAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['database']  # NOTE: Technically, database folder should be in the external SSD, but local SSD is more reliable since external SSD can be disconnected. Thus no such option is provided for external SSD.

elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = "172.17.27.12"
    CLEAR_TERMINAL_COMMAND = "clear"
    PRINT_MOUSE_COORDINATES = False

    # ENSURE THAT THE LOCAL SSD and EXTERNAL SSD IS MOUNTED TO THE CONTAINER PROPERLY
    DATA_FOLDER_PATH_LOCAL = Path('home') / 'local_ssd_data_folder'
    DATA_FOLDER_PATH_EXTERNAL = Path('home') / 'external_ssd_data_folder'
    print(f"[INFO] The local data folder path is set to:'{DATA_FOLDER_PATH_LOCAL}'")
    print(f"[INFO] The external data folder path is set to: '{DATA_FOLDER_PATH_EXTERNAL}'")

    update_data_folder(is_external = False, data_folder_path= DATA_FOLDER_PATH_LOCAL , must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    update_data_folder(is_external = True, data_folder_path= DATA_FOLDER_PATH_EXTERNAL, must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    is_local_available = check_if_folder_accesible(DATA_FOLDER_PATH_LOCAL)
    is_external_available = check_if_folder_accesible(DATA_FOLDER_PATH_EXTERNAL)
    print(f"[INFO] The local path '{DATA_FOLDER_PATH_LOCAL}' : {'is available' if is_local_available else 'is not available'}")
    print(f"[INFO] The external path '{DATA_FOLDER_PATH_EXTERNAL}' : {'is available' if is_external_available else 'is not available'}")

    if not is_local_available:
        raise Exception(f"Local data folder path '{DATA_FOLDER_PATH_LOCAL}' is not accessible")
    if not is_external_available:
        raise Exception(f"External data folder path '{DATA_FOLDER_PATH_EXTERNAL}' is not accessible Please ensure the external drive is connected to 'E:' drive")
                        
    SQL_DATABASE_FOLDER_PATH_LOCAL = DATA_FOLDER_PATH_LOCAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['database']  # NOTE: Technically, database folder should be in the external SSD, but local SSD is more reliable since external SSD can be disconnected. Thus no such option is provided for external SSD.

    # NOTE: When the external volume is disconnected, inside the Docker container, the directory 
    # /home/external_ssd_data_folder is still present as a bind mount. However, its contents are 
    # now inaccessible because the underlying host directory is no longer mounted.
    # DO: always call 'def check_if_folder_accesible(folder_path: Path = None)->bool' to check if the folder is accessible 
    # before reading or writing to it.
    
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
