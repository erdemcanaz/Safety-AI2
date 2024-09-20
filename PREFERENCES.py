import os, psutil, platform, subprocess
if os.name == "nt": import win32api, win32file
from pathlib import Path
import psutil

class USBDriveDetector:
    def __init__(self):
        self.os_type = platform.system()
        self.is_docker = self.check_if_docker()
    
    def check_if_docker(self):
        """
        Check if the code is running inside a Docker container.
        """
        # Method 1: Check for /.dockerenv file
        if os.path.exists('/.dockerenv'):
            return True
        
        # Method 2: Check cgroup for 'docker'
        try:
            with open('/proc/1/cgroup', 'rt') as f:
                for line in f:
                    if 'docker' in line:
                        return True
        except Exception:
            pass
        
        return False

    def get_usb_drives(self):
        """
        Retrieve a list of connected USB drives based on the operating system and environment.
        """
        if self.is_docker:
            print("Running inside a Docker container.")
            return self.get_usb_drives_docker()
        else:
            print("Running on the host machine.")
            if self.os_type == 'Linux':
                return self.get_usb_drives_linux()
            elif self.os_type == 'Windows':
                return self.get_usb_drives_windows()
            else:
                raise NotImplementedError(f"Unsupported OS: {self.os_type}")
    
    def get_usb_drives_linux(self):
        """
        Detect USB drives on a Linux host.
        """
        external_drives = []
        partitions = psutil.disk_partitions(all=False)
        for partition in partitions:
            if '/media/' in partition.mountpoint or '/mnt/' in partition.mountpoint:
                device_path = partition.device
                try:
                    # Get UUID using blkid
                    result = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', device_path], capture_output=True, text=True)
                    uuid = result.stdout.strip()
                except Exception as e:
                    uuid = None
                external_drives.append({
                    'mountpoint': partition.mountpoint,
                    'device': device_path,
                    'uuid': uuid,
                    'fstype': partition.fstype,
                    'volume_abspath': os.path.abspath(partition.mountpoint)
                })
        return external_drives
    
    def get_usb_drives_windows(self):
        """
        Detect USB drives on a Windows host.
        """
        external_drives = []
        try:
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
            for drive in drives:
                drive_type = win32file.GetDriveType(drive)
                # DRIVE_REMOVABLE = 2
                if drive_type == win32file.DRIVE_REMOVABLE:
                    try:
                        # Get Volume Information
                        volume_info = win32api.GetVolumeInformation(drive)
                        volume_name = volume_info[0]
                        serial_number = volume_info[1]
                        # Use serial_number as a pseudo-UUID
                        uuid = f"{serial_number:08X}"
                    except Exception as e:
                        volume_name = None
                        uuid = None
                    external_drives.append({
                        'drive_letter': drive,
                        'volume_name': volume_name,
                        'uuid': uuid,
                        'volume_abspath': os.path.abspath(drive)
                    })
        except Exception as e:
            print(f"Error detecting USB drives on Windows: {e}")
        return external_drives
    
    def get_usb_drives_docker(self):
        """
        Detect USB drives within a Docker container.
        Assumes that external drives are mounted as volumes inside the container.
        """
        # Define potential mount points inside Docker
        # You can customize this list based on how you mount volumes in your Docker setup
        potential_mount_points = [
            '/home/external_data_folder',
        ]
        
        external_drives = []
        for mount_point in potential_mount_points:
            print(f"Checking mount point: {mount_point}")
            if os.path.ismount(mount_point):
                device_path = mount_point  # In Docker, device paths might not be directly accessible
                try:
                    # Attempt to retrieve UUID if possible
                    # This might not work inside Docker; adjust as necessary
                    result = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', mount_point], capture_output=True, text=True)
                    uuid = result.stdout.strip()
                except Exception:
                    uuid = None
                external_drives.append({
                    'mountpoint': mount_point,
                    'device': device_path,
                    'uuid': uuid,
                    'fstype': None,  # Filesystem type might not be easily retrievable inside Docker
                    'volume_abspath': os.path.abspath(mount_point)
                })
        
        if not external_drives:
            print("No external drives detected within Docker. Ensure that the drives are mounted as volumes.")
        
        return external_drives

    def find_drive_by_label(self, label_name):
        """
        Find a USB drive by its label name.
        """
        usb_drives = self.get_usb_drives()
        for drive in usb_drives:
            print(drive)
            # Depending on OS and environment, the label key may vary
            label = drive.get('volume_name') or drive.get('Volume Name') or drive.get('label')
            if label and label.lower() == label_name.lower():
                return drive
        return None

    def find_drive_by_uuid(self, uuid):
        """
        Find a USB drive by its UUID.
        """
        usb_drives = self.get_usb_drives()
        for drive in usb_drives:
            drive_uuid = drive.get('uuid')
            if drive_uuid and drive_uuid.lower() == uuid.lower():
                return drive
        return None
    
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
#TODO: set an interval for checking image integrity and remove images that are not in the database

DATA_FOLDER_PATH_EXTERNAL = None
detector = USBDriveDetector()
target_label = 'SAFETY_AI'  if os.name == "nt" else 'T7 Shield'
target_drive = detector.find_drive_by_label(target_label)
if target_drive:
    if detector.os_type == 'Linux' or detector.is_docker:
        DATA_FOLDER_PATH_EXTERNAL = target_drive.get('mountpoint') or target_drive.get('volume_abspath')
    elif detector.os_type == 'Windows':
        DATA_FOLDER_PATH_EXTERNAL = target_drive.get('drive_letter') or target_drive.get('volume_abspath')
    else:
        DATA_FOLDER_PATH_EXTERNAL = None
    print(f"DATA_FOLDER_PATH_EXTERNAL set to: {DATA_FOLDER_PATH_EXTERNAL}")
else:
    print(f"Drive with label '{target_label}' not found. Please ensure it is connected and mounted.")

if os.name == "nt":  # For Windows (i.e development environment)
    SERVER_IP_ADDRESS = "192.168.0.26"
    CLEAR_TERMINAL_COMMAND = "cls"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH.parent/ "api_server_2" / "safety_ai.db"
    PRINT_MOUSE_COORDINATES = True
    
    DATA_FOLDER_PATH_LOCAL = PREFERENCES_FILE_PATH.parent.parent / "safety_AI_volume" / "api_server" / "encrypted_images"
    DATA_FOLDER_PATH_EXTERNAL = DATA_FOLDER_PATH_EXTERNAL

elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = "172.17.27.12"
    CLEAR_TERMINAL_COMMAND = "clear"
    SQL_DATABASE_PATH = PREFERENCES_FILE_PATH.parent.parent / "safety_AI_volume" / "api_server" / "safety_ai.db"
    PRINT_MOUSE_COORDINATES = False
    DATA_FOLDER_PATH_LOCAL = PREFERENCES_FILE_PATH.parent.parent / "safety_AI_volume" / "api_server" / "encrypted_images"
    DATA_FOLDER_PATH_EXTERNAL = DATA_FOLDER_PATH_EXTERNAL
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
