from modules import picasso, text_transformer
import cv2
import numpy as np

import requests
from typing import Dict, List
import time,copy

class KameralarApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",      
        "clear_camera_configs_bbox": (364,143,436,194),
        "decrease_camera_index_button": (404, 208, 420, 238),
        "increase_camera_index_button": (405, 893, 421, 920),

        "camera_list_bbox": (74, 211, 391, 922),

        "camera_config_fetching_min_interval": 5 # seconds

    }

    def __init__(self):
        self.last_time_camera_configs_fetched = 0
        self.first_camera_index_to_show = 0

        self.ORIGINAL_CAMERA_CONFIGS = None
        self.camera_configs = None

        self.reset_dummy_camera_dict()

    def reset_dummy_camera_dict(self):
        self.dummy_camera_dict = {
            "is_alive": True,
            "camera_uuid": "94edc97e-1c91-49da-8004-f4a1b7ef1360",
            "camera_region": "",
            "camera_description": "",
            "NVR_ip": "172.16.0.23",
            "username": "admin",
            "password": "Besan.23",
            "camera_ip_address": "172.16.14.13",
            "stream_path": "profile2/media.smp",
            "active_rules": []
        }      


    def __is_xy_in_bbox(self, x:int, y:int, bbox:tuple):
        x1, y1, x2, y2 = bbox
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return True
        return False 
    
    def __get_cameras_to_show(self) -> List[Dict]:
        if self.camera_configs is None:
            return []
        
        if self.first_camera_index_to_show >= len(self.camera_configs):
            self.first_camera_index_to_show = max(0, len(self.camera_configs) - 11)
        
        return self.camera_configs[self.first_camera_index_to_show:self.first_camera_index_to_show+11]
    
    def __check_if_camera_is_old_updated_or_new(self, camera_dict:Dict = None) -> str:
        keys_to_check = ["is_alive", "camera_uuid", "camera_region", "camera_description", "NVRip", "username", "password", "camera_ip_address", "stream_path", "active_rules"]
        
        for _camera_dict in self.ORIGINAL_CAMERA_CONFIGS:
            if _camera_dict.get("camera_ip_address") == camera_dict["camera_ip_address"]: # if camera is already in the list
                for key in keys_to_check:
                    if _camera_dict.get(key) != camera_dict.get(key):
                        return "updated"
                else:
                    return "old"
        else: # if camera is not in the list
            return "new"

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None): 
        # Mouse input
        if mouse_input.get_last_leftclick_position() is not None:
            x, y = mouse_input.get_last_leftclick_position()
            mouse_input.clear_last_leftclick_position()        
            if self.__is_xy_in_bbox(x, y, self.CONSTANTS["clear_camera_configs_bbox"]):
                self.camera_configs = None  
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["decrease_camera_index_button"]):
                self.first_camera_index_to_show = max(0, self.first_camera_index_to_show-11)
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["increase_camera_index_button"]):
                self.first_camera_index_to_show = self.first_camera_index_to_show+11
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["camera_list_bbox"]):
                    if self.fetched_data is not None:
                        report_page_index = (y - self.CONSTANTS["camera_list_bbox"][1])//65
                        report_index = self.first_camera_index_to_show + report_page_index
                        if not report_index >= len(self.camera_configs):
                            self.dummy_camera_dict = self.camera_configs[report_index]                            

        if self.camera_configs is None and (time.time() - self.last_time_camera_configs_fetched) > self.CONSTANTS["camera_config_fetching_min_interval"]:
            self.last_time_camera_configs_fetched = time.time()
            fetched_dict, status_code = active_user.request_camera_configs_dict()
            if status_code == 200:
                self.camera_configs = fetched_dict
                self.ORIGINAL_CAMERA_CONFIGS = copy.deepcopy(fetched_dict)
            
        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC -> direct to login page
            active_user.set_username(new_username = "")
            active_user.set_password(new_password = "")
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0
          
        # Draw UI
        for camera_index, camera_dict in enumerate(self.__get_cameras_to_show()):
            x, y = 75, 207 + camera_index * 65
            picasso.draw_image_on_frame(ui_frame, image_name="camera_list_bar", x=x, y=y, width=317, height=60, maintain_aspect_ratio=True)
            cv2.putText(ui_frame, f"{self.first_camera_index_to_show+camera_index+1}", (x+10, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169,69,0), 2)
            
            camera_status = self.__check_if_camera_is_old_updated_or_new(camera_dict)
            camera_status_image = "new_camera_icon" if camera_status == "new" else "updated_camera_icon" if camera_status == "updated" else "old_camera_icon"
            picasso.draw_image_on_frame(ui_frame, image_name=camera_status_image, x=x+45, y=y+15, width=30, height=30, maintain_aspect_ratio=True)            
            cv2.putText(ui_frame, f"{camera_dict.get('camera_ip_address')}", (x+90, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169,69,0), 2)
            
        #put the camera configs to the dummy camera dict
        font_size = 0.5
        font_thickness = 1

        is_alive_text = "Aktif" if self.dummy_camera_dict.get("is_alive") else "Pasif"
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('camera_ip_address')}", (750, 775), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('camera_uuid')}", (750, 809), cv2.FONT_HERSHEY_SIMPLEX, font_size, (180,180,180), font_thickness)
        cv2.putText(ui_frame, f"{is_alive_text}", (750, 843), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), 2)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('username')}", (750, 877), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('password')}", (750, 912), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('NVR_ip')}", (750, 946), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('camera_region')}", (750, 981), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('camera_description')}", (1181, 809), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)

        picasso.draw_image_on_frame(ui_frame, image_name="kameralar_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        cv2.imshow(cv2_window_name, ui_frame)

        
