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

        "camera_config_fetching_min_interval": 5 # seconds

    }

    def __init__(self):
        self.last_time_camera_configs_fetched = 0
        self.first_camera_index_to_show = 0

        self.ORIGINAL_CAMERA_CONFIGS = None
        self.camera_configs = None

        self.writing_to_which_one = 0
        self.ipv4 = "" #0
        self.UUID = "" #1
        self.is_active = False 
        self.username = "" #2
        self.password = "" #3
        self.NVRip = "" #4 
        self.region_name = "" #5
        self.description = "" #6

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
            picasso.draw_image_on_frame(ui_frame, image_name="old_camera_icon", x=x+10, y=y+15, width=30, height=30, maintain_aspect_ratio=True)            
            cv2.putText(ui_frame, f"{camera_dict.get('camera_ip_address')}", (x+50, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169,69,0), 2)
            
        picasso.draw_image_on_frame(ui_frame, image_name="kameralar_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        cv2.imshow(cv2_window_name, ui_frame)

        
