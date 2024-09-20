import os, psutil, platform, subprocess
if os.name == "nt": import win32api, win32file
from pathlib import Path
import psutil, datetime, time

def update_data_folder(data_folder_path:Path = None, must_existing_data_subfolder_paths = None):      
    if data_folder_path == None or not isinstance(data_folder_path, Path):
        raise ValueError("data_folder_path is None or not a Path object")
    
    # Check if the data folder's parent folder is accessible and if data folder already exists
    is_parent_folder_accessible = os.path.isdir(data_folder_path.parent) and os.access(data_folder_path.parent, os.R_OK | os.W_OK)
    is_folder_exists = os.path.isdir(data_folder_path) 

    if is_parent_folder_accessible and is_folder_exists:
        pass        
    elif is_parent_folder_accessible and not is_folder_exists:
        os.makedirs(data_folder_path, exist_ok=True)
    else:
        #Since the parent folder is not accessible, the data_folder_path and subfolders can not be created
        return        
    
    for subfolder_key, subfolder_path in must_existing_data_subfolder_paths.items():
        if not os.path.exists(data_folder_path / subfolder_path):
           os.makedirs(data_folder_path / subfolder_path, exist_ok=True)
           with open(data_folder_path / subfolder_path / "created_at.txt", "w") as f:
               f.write(f"Created at: {datetime.datetime.now()}:\nData Folder Path: {data_folder_path}\nSubfolder Key: {subfolder_key}\nSubfolder Path: {subfolder_path}")
           
    return Path(data_folder_path)

def check_if_folder_accesible(folder_path: Path = None):  
    if not isinstance(folder_path, Path):
        return False
    return os.path.isdir(folder_path) and os.access(folder_path, os.R_OK | os.W_OK)

def calculate_folder_size_gb(folder_path: Path = None):
    if not isinstance(folder_path, Path):
        return 0
    return sum(f.stat().st_size for f in folder_path.glob('**/*') if f.is_file()) / (1024**3)

PREFERENCES_FILE_PATH = Path(__file__).resolve()
# Definitions (Hardcoded)
SQL_MANAGER_SECRET_KEY = b"G4ECs6lRrm6HXbtBdMwFoLA18iqF1mMT" # Used to encrypt-decrypt images. Note that this is an UTF8 encoded byte string. Will be changed in the future, developers should not use this key in production
MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_LOCAL = 250     # 250 GB
MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_EXTERNAL = 1500 # 1.5 TB
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
ADMIN_USER_INFO = {"username": "admin", "password": "admin_password", "personal_fullname": "Admin User"}
MUST_EXISTING_DATA_SUBFOLDER_PATHS = { 
        #NOTE: NEVER EVER CHANGE THE KEY NAMES

        # safety_ai/ ==============================
        "safety_ai_logs": Path("safety_ai/logs"),
        "safety_ai_test_logs": Path("safety_ai/logs/test_logs"),
        "safety_ai_camera_module_logs": Path("safety_ai/logs/sql_module_logs"),
        "safety_ai_frame_evaluator_logs": Path("safety_ai/logs/frame_evaluator_module_logs"),
        "safety_ai_models_module_logs": Path("safety_ai/logs/models_module_logs"),
        "safety_ai_safety_ai_api_logs": Path("safety_ai/logs/safety_ai_api_dealer_module_logs"),
        
        # api_server/ ==============================
        "api_server_logs": Path("api_server/logs"),
        "api_server_test_logs": Path("api_server/logs/test_logs"),
        "api_server_sql_module_logs": Path("api_server/logs/sql_module_logs"),
        "api_server_fast_api_module_logs": Path("api_server/logs/fast_api_module_logs"),
        "api_server_server_requests_logs": Path("api_server/logs/server_requests_logs"),
        "api_server_encrypted_images":  Path("api_server/encrypted_images"),
        "api_server_pdf_reports":  Path("api_server/pdf_reports"),
        "api_server_database_backups":  Path("api_server/database_backups"),
        "api_server_database":  Path("api_server/database"),

    }

if os.name == "nt":  # For Windows (i.e development environment)
    print("[INFO] Windows OS detected")
    SERVER_IP_ADDRESS = "192.168.0.26"
    CLEAR_TERMINAL_COMMAND = "cls"
    PRINT_MOUSE_COORDINATES = True
    
    # ENSURE THAT THE LOCAL SSD and EXTERNAL USB IS MOUNTED TO THE CONTAINER PROPERLY
    DATA_FOLDER_PATH_LOCAL = Path(__file__).parent.resolve() /'api_server' / 'local_ssd_data_folder'
    DATA_FOLDER_PATH_EXTERNAL = Path("E:")
    print(f"[INFO] The local data folder path is hardcoded to:'{DATA_FOLDER_PATH_LOCAL}'")
    print(f"[INFO] The external data folder path is hardcoded to: '{DATA_FOLDER_PATH_EXTERNAL}'")

    print(f"[INFO] Checking if the data folder paths are accessible")
    is_local_available = check_if_folder_accesible(DATA_FOLDER_PATH_LOCAL)
    is_external_available = check_if_folder_accesible(DATA_FOLDER_PATH_EXTERNAL)
    print(f"\tThe local path '{DATA_FOLDER_PATH_LOCAL}' : {'is available' if is_local_available else 'is not available'}")
    print(f"\tThe external path '{DATA_FOLDER_PATH_EXTERNAL}' : {'is available' if is_external_available else 'is not available'}")

    if not is_local_available:
        raise Exception(f"Local data folder path '{DATA_FOLDER_PATH_LOCAL}' is not accessible")
    if not is_external_available:
        raise Exception(f"External data folder path '{DATA_FOLDER_PATH_EXTERNAL}' is not accessible Please ensure the external drive is connected to 'E:' drive")

    print(f"[INFO] Ensuring the data folder's subfolders are created")
    update_data_folder( data_folder_path= DATA_FOLDER_PATH_LOCAL , must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    update_data_folder( data_folder_path= DATA_FOLDER_PATH_EXTERNAL, must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)

    SQL_DATABASE_FOLDER_PATH_LOCAL = DATA_FOLDER_PATH_LOCAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['api_server_database']  # NOTE: Technically, database folder should be in the external SSD, but local SSD is more reliable since external SSD can be disconnected. Thus no such option is provided for external SSD.
elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    #NOTE: assumes that the script runs on docker container
    SERVER_IP_ADDRESS = "172.17.27.12"
    CLEAR_TERMINAL_COMMAND = "clear"
    PRINT_MOUSE_COORDINATES = False

    # ENSURE THAT THE LOCAL SSD and EXTERNAL SSD IS MOUNTED TO THE CONTAINER PROPERLY
    DATA_FOLDER_PATH_LOCAL = Path('/home') / 'local_ssd_data_folder'
    DATA_FOLDER_PATH_EXTERNAL = Path('/home') / 'external_ssd_data_folder'
    print(f"[INFO] The local data folder path is hardcoded to:'{DATA_FOLDER_PATH_LOCAL}'")
    print(f"[INFO] The external data folder path is hardcoded to: '{DATA_FOLDER_PATH_EXTERNAL}'")

    print(f"[INFO] Checking if the data folder paths are accessible")
    is_local_available = check_if_folder_accesible(DATA_FOLDER_PATH_LOCAL)
    is_external_available = check_if_folder_accesible(DATA_FOLDER_PATH_EXTERNAL)
    print(f"\tThe local path '{DATA_FOLDER_PATH_LOCAL}' : {'is available' if is_local_available else 'is not available'}")
    print(f"\tThe external path '{DATA_FOLDER_PATH_EXTERNAL}' : {'is available' if is_external_available else 'is not available'}")

    if not is_local_available:
        raise Exception(f"Local data folder path '{DATA_FOLDER_PATH_LOCAL}' is not accessible")
    if not is_external_available:
        raise Exception(f"External data folder path '{DATA_FOLDER_PATH_EXTERNAL}' is not accessible Please ensure the external drive is connected to 'E:' drive")

    print(f"[INFO] Ensuring the data folder's subfolders are created")    
    update_data_folder( data_folder_path= DATA_FOLDER_PATH_LOCAL , must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
    update_data_folder( data_folder_path= DATA_FOLDER_PATH_EXTERNAL, must_existing_data_subfolder_paths=MUST_EXISTING_DATA_SUBFOLDER_PATHS)
   
    SQL_DATABASE_FOLDER_PATH_LOCAL = DATA_FOLDER_PATH_LOCAL / MUST_EXISTING_DATA_SUBFOLDER_PATHS['api_server_database']  # NOTE: Technically, database folder should be in the external SSD, but local SSD is more reliable since external SSD can be disconnected. Thus no such option is provided for external SSD.

    # NOTE: When the external volume is disconnected, inside the Docker container, the directory 
    # /home/external_ssd_data_folder is still present as a bind mount. However, its contents are 
    # now inaccessible because the underlying host directory is no longer mounted.
    # DO: always call 'def check_if_folder_accesible(folder_path: Path = None)->bool' to check if the folder is accessible 
    # before reading or writing to it.
else:
    raise Exception("Not supported operating system")

# Check if the data folder size is higher than the allowed limit
local_data_folder_size = calculate_folder_size_gb(DATA_FOLDER_PATH_LOCAL)
external_data_folder_size = calculate_folder_size_gb(DATA_FOLDER_PATH_EXTERNAL)
if local_data_folder_size > MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_LOCAL:
    raise Exception(f"Local data folder size is {local_data_folder_size} GB which is greater than the allowed limit of {MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_LOCAL} GB")
if external_data_folder_size > MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_EXTERNAL:
    raise Exception(f"External data folder size is {external_data_folder_size} GB which is greater than the allowed limit of {MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_EXTERNAL} GB")

print(f"[INFO] %{100*local_data_folder_size/MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_LOCAL:.2f} of the allowed | Size of the local data folder: {local_data_folder_size:.2f} GB")
print(f"[INFO] %{100*external_data_folder_size/MAX_SIZE_ALLOWED_GB_DATA_FOLDER_PATH_EXTERNAL:.2f} of the allowed | Size of the external data folder: {external_data_folder_size:.2f} GB")

# Check if year is less than 2024, if so raise an error
if datetime.datetime.now().year < 2024:
    raise ValueError("System year is less than 2024, Please ensure the system date and time is correct, best way to connect device to the internet and it will likely to automatically update the date and time")

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

print(f"[INFO] The preferences file is loaded successfully")
time.sleep(0.5) # Wait so that the user can read the printed information