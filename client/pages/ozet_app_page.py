from modules import picasso
import cv2
import numpy as np

import requests
from typing import Dict, List
import datetime, time

class OzetApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "camera_config_fetching_min_interval": 10, # fetch camera configs every 10 seconds

        "increase_camera_index_bbox": (75, 142, 317, 60),
        "decrease_camera_index_bbox": (75, 142 + 12*65, 317, 60),
        "camera_list_bbox": (77, 147 , 391, 981)
    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None

        self.first_camera_index_to_show = 0
        self.camera_configs = None
        self.last_time_camera_configs_fetched = 0
        pass

    def __get_cameras_to_list(self) -> List[Dict]:
        if self.camera_configs is None:
            return []        
        if self.first_camera_index_to_show >= len(self.camera_configs):
            self.first_camera_index_to_show = max(0, len(self.camera_configs) - 13)        
        return self.camera_configs[self.first_camera_index_to_show:self.first_camera_index_to_show+ 13]
    

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):
        
        # Fetch camera configs
        if self.camera_configs is None and (time.time() - self.last_time_camera_configs_fetched) > self.CONSTANTS["camera_config_fetching_min_interval"]:
            self.last_time_camera_configs_fetched = time.time()
            fetched_dict, status_code = active_user.request_camera_configs_dict()
            if status_code == 200:
                self.camera_configs = fetched_dict
                for camera_dict in self.camera_configs:
                    camera_dict["is_show_summary"] = False
        
        if mouse_input.get_last_leftclick_position() is not None:
            x, y = mouse_input.get_last_leftclick_position()
            mouse_input.clear_last_leftclick_position()        
            if self.__is_xy_in_bbox(x, y, self.CONSTANTS["decrease_camera_index_bbox"]):
                self.first_camera_index_to_show = max(0, self.first_camera_index_to_show-13)
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["increase_camera_index_bbox"]):
                self.first_camera_index_to_show = self.first_camera_index_to_show+13
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["camera_list_bbox"]):
                if self.camera_configs is not None:
                    clicked_camera_index = (y - self.CONSTANTS["camera_list_bbox"][1])//65
                    camera_index = self.first_camera_index_to_show + clicked_camera_index
                    if not camera_index >= len(self.camera_configs):
                        self.camera_configs[camera_index]["is_show_summary"] = not self.camera_configs[camera_index]["is_show_summary"]

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0          

        today_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        today_shift = "Vardiya-I" if datetime.datetime.now().hour < 8 else "Vardiya-II" if datetime.datetime.now().hour < 16 else"Vardiya-III "
        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="ozet_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  

        text = active_user.get_token_person_name()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]            
        x = 1910-text_size[0]
        y = text_size[1]+5
        cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (239, 237, 232), 2, cv2.LINE_AA)
        cv2.putText(ui_frame, "| "+today_date+" | "+today_shift, (337, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (228, 173, 0), 2, cv2.LINE_AA)                                                                          
        
        for camera_index, camera_dict in enumerate(self.__get_cameras_to_list()):
            x, y = 75, 142 + camera_index * 65
            picasso.draw_image_on_frame(ui_frame, image_name="camera_list_bar", x=x, y=y, width=317, height=60, maintain_aspect_ratio=True)
            cv2.putText(ui_frame, f"{self.first_camera_index_to_show+camera_index+1}", (x+5, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169,69,0), 2)

            listed_camera_icon_name = "eye_dark_blue" if camera_dict.get("is_show_summary") else "eye_light_blue"
            picasso.draw_image_on_frame(ui_frame, image_name=listed_camera_icon_name, x=x+45, y=y+23, width=35, height=35, maintain_aspect_ratio=True)            
            cv2.putText(ui_frame, f"{camera_dict.get('camera_ip_address')}", (x+100, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169,69,0), 2)
            
        
        
        cv2.imshow(cv2_window_name, ui_frame)

        



    
