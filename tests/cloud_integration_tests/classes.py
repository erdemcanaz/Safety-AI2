import cv2
import numpy as np
import random, uuid, base64, copy

class ViolationLog:
    COMMON_RESOLUTIONS = {
        "test_default": "960x540",   # quarter of 1920x1080
        "VGA": "640x480",            # 307,200 pixels, ~900 KB
        "480i": "720x480",           # 345,600 pixels, ~1 MB
        "480p": "720x480",           # 345,600 pixels, ~1 MB
        "576i": "720x576",           # 414,720 pixels, ~1.2 MB
        "SVGA": "800x600",           # 480,000 pixels, ~1.4 MB
        "HD": "1366x768",            # 1,049,088 pixels, ~3 MB
        "XGA": "1024x768",           # 786,432 pixels, ~2.3 MB
        "WXGA": "1280x800",          # 1,024,000 pixels, ~3 MB
        "720p": "1280x720",          # 921,600 pixels, ~2.6 MB
        "SXGA": "1280x1024",         # 1,310,720 pixels, ~3.7 MB
        "1080p": "1920x1080",        # 2,073,600 pixels, ~6 MB
        "QHD": "2560x1440",          # 3,686,400 pixels, ~10.5 MB
        "4K UHD": "3840x2160",       # 8,294,400 pixels, ~24 MB
        "5K": "5120x2880",           # 14,745,600 pixels, ~42 MB
        "8K UHD": "7680x4320"        # 33,177,600 pixels, ~95 MB
    }

    def __init__(self,):        
        self.violation_dict = {
            "RelatedShiftDate": None,   # (str) | %dd.%mm.%yyyy %hh:%mm:%ss | 15.08.2024 11:11:23 
            "DeviceTimestamp": None,    # (str) | %dd.%mm.%yyyy %hh:%mm:%ss | 15.08.2024 11:11:23     
            "RelatedShiftNo": None,     # (str) | one of ['0', '1', '2'] #NOTE ASK FOR CORRECTION
            "RegionName": None,         # (str) | any string 
            "ViolationType": None,      # (str) | one of 
            "ViolationScore": None,     # (str) | a number 0<= X <= 100
            "ViolationUID": None,       # (str) | An unix identifier (UUID4)
            "CameraUID": None,          # (str) | An unix identifier (UUID4)
            "Image": None,              # (str?)| base encoded image (preferably jpg but any format is accepted)
        }

    def set_as_default_correct_dict(self):
        default_resolution = ViolationLog.COMMON_RESOLUTIONS["test_default"].split("x")
        width, height = int(default_resolution[0]), int(default_resolution[1])
        random_frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        success, encoded_image = cv2.imencode('.jpg', random_frame)
        if not success:
            raise ValueError('Failed to encode image')       
        base64_encoded_jpg_image = base64.b64encode(encoded_image.tobytes()) 
        
        self.violation_dict = {
            "RelatedShiftDate": "15.08.2024 14:15:10",   # (str) | %dd.%mm.%yyyy %hh:%mm:%ss | 15.08.2024 11:11:23 
            "DeviceTimestamp": "15.08.2024 16:15:10",    # (str) | %dd.%mm.%yyyy %hh:%mm:%ss | 15.08.2024 11:11:23     
            "RelatedShiftNo": 3,     # (str) | one of ['0', '1', '2']
            "RegionName": "SHE-matters",         # (str) | any string 
            "ViolationType": "restricted_area_rule_statistics",      # (str) | one of 
            "ViolationScore": f"{random.randint(1,99)}",     # (str) | a number 0<= X <= 100
            "ViolationUID": str(uuid.uuid4()),       # (str) | An unix identifier (UUID4)
            "CameraUID": str(uuid.uuid4()),          # (str) | An unix identifier (UUID4)
            "Image": base64_encoded_jpg_image,              # (str?)| base encoded image (preferably jpg but any format is accepted)
        }

    def get_violation_log(self):
        return copy.deepcopy(self.violation_dict)
    
class PostRequest:
    def __init__(self):
        self.endpoint_url = input("End-point URL: ")
        self.headers = {
            "Content-Type": "application/json",
            "token": f"{input('Token value:')}"
        }

        self.body = {
            "SafetyData": [
               
            ]
        }
        
    def clear_body(self):
        self.body = {
            "SafetyData":[

            ]
        }

    def append_new_data(self, new_data:dict = None):
        self.body["SafetyData"].append(new_data)

    def get_endpoint_url(self):
        return self.endpoint_url