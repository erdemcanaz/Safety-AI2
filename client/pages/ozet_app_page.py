from modules import picasso
import cv2
import numpy as np

import requests
from typing import Dict, List
import datetime, time, random

class OzetApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "camera_config_fetching_min_interval": 10, # fetch camera configs every 10 seconds

        "decrease_camera_index_bbox": (400, 142 , 429, 176),
        "increase_camera_index_bbox": (400, 967 , 429, 1002),
        "decrease_summary_type_bbox": (457, 327 , 511, 365),
        "increase_summary_type_bbox": (1200, 327 , 1253, 365),
        "camera_list_bbox": (76, 147, 390 ,982)
    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None

        self.first_camera_index_to_show = 0
        self.camera_configs = None
        self.last_time_camera_configs_fetched = 0

        self.summary_types = ["Vardiya", "Gun", "Hafta", "Ay", "Tum Zamanlar"]
        self.summary_type_index = 0

        self.mock_shift_data = None
        pass

    def __get_cameras_to_list(self) -> List[Dict]:
        if self.camera_configs is None:
            return []        
        if self.first_camera_index_to_show >= len(self.camera_configs):
            self.first_camera_index_to_show = max(0, len(self.camera_configs) - 13)        
        return self.camera_configs[self.first_camera_index_to_show:self.first_camera_index_to_show+ 13]
    
    def __is_xy_in_bbox(self, x:int, y:int, bbox:tuple):
        x1, y1, x2, y2 = bbox
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return True
        return False   
    
    def __format_count_to_hr(self, number:int):
        if number < 1000:
            return str(number)
        elif number < 1000000:
            return f"{number/1000:.1f}K"
        else:
            return f"{number//1000000:.1f}M"
        
    def __plot_shift_summary(self, ui_frame:np.ndarray):
        #TODO: check if valid data is fetched
        if self.mock_shift_data is None or (time.time() - self.last_time_data_fetch) > 5:
            self.mock_shift_data = {}
            self.last_time_data_fetch = time.time()
            for i in range(8):
                self.mock_shift_data[f"entry_{i}"] = {
                    "hard_hat_approved": random.randint(0, 10000),
                    "hard_hat_rejected": random.randint(0, 10000),
                    "restricted_area_approved": random.randint(0, 10000),
                    "restricted_area_rejected": random.randint(0, 10000),
                }

        # plot timestamps
        hour_now = datetime.datetime.now().hour
        first_shift_hour = hour_now - hour_now%8
        for i in range(8):
            color = (154,108,15) if i %2 == 0 else (229,218,194)
            cv2.putText(ui_frame, f"{first_shift_hour+i:02d}:00", (554+i*160, 1000), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # plot bars data
        hard_hat_bar_top_coordinates = []
        restricted_area_bar_top_coordinates = []

        bar_height = 362
        period = 152
        bar_width = 30
        spacing = (160-2*bar_width)//3
        for i in range(8):
            shift_data = self.mock_shift_data[f"entry_{i}"]
            hard_hat_suces = shift_data["hard_hat_approved"]/(shift_data["hard_hat_rejected"]+shift_data["hard_hat_approved"]) if shift_data["hard_hat_rejected"]+shift_data["hard_hat_approved"] > 0 else 5
            restricted_area_suces = shift_data["restricted_area_approved"]/(shift_data["restricted_area_rejected"]+shift_data["restricted_area_approved"]) if shift_data["restricted_area_rejected"]+shift_data["restricted_area_approved"] > 0 else 5
            
            top_y = 608
            hard_hat_top_y = top_y + int(bar_height*(1-hard_hat_suces))
            restricted_area__top_y = top_y + int(bar_height*(1-restricted_area_suces))
            hard_hat_x = 554+spacing + i*period
            restricted_area_x = 554+2*spacing + bar_width + i*period

            cv2.rectangle(ui_frame, (hard_hat_x,hard_hat_top_y), (hard_hat_x+bar_width,969), (195, 184, 161), -1)
            cv2.putText(ui_frame, self.__format_count_to_hr(shift_data["hard_hat_approved"]), (hard_hat_x, hard_hat_top_y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (195, 184, 161), 2)
            cv2.rectangle(ui_frame, (restricted_area_x,restricted_area__top_y), (restricted_area_x+bar_width,969), (206, 168, 182), -1)
            cv2.putText(ui_frame, self.__format_count_to_hr(shift_data["restricted_area_approved"]), (restricted_area_x, restricted_area__top_y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (206, 168, 182), 2)
            
            cv2.circle(ui_frame, (hard_hat_x+bar_width//2, hard_hat_top_y), 10, (154, 108, 15), -1)
            cv2.circle(ui_frame, (restricted_area_x+bar_width//2, restricted_area__top_y), 10, (203, 110, 145), -1)

            hard_hat_bar_top_coordinates.append((hard_hat_x+bar_width//2, hard_hat_top_y))
            restricted_area_bar_top_coordinates.append((restricted_area_x+bar_width//2, restricted_area__top_y))

        picasso.plot_smooth_curve_on_frame(ui_frame, hard_hat_bar_top_coordinates, color=(154, 108, 15), thickness=3)
        picasso.plot_smooth_curve_on_frame(ui_frame, restricted_area_bar_top_coordinates, color=(203, 110, 145), thickness=3)
   
        
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
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["decrease_summary_type_bbox"]):
                self.summary_type_index = max(0, self.summary_type_index-1)
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["increase_summary_type_bbox"]):
                self.summary_type_index = min(len(self.summary_types)-1, self.summary_type_index+1)
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
        
        (text_width, text_height), baseline = cv2.getTextSize(self.summary_types[self.summary_type_index], cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)
        cv2.putText(ui_frame, f"{self.summary_types[self.summary_type_index]}", (514 + (686-text_width)//2, 357), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (228, 173, 0), 2, cv2.LINE_AA)
        cv2.putText(ui_frame, f"({self.summary_types[self.summary_type_index]})", (921, 551), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (228, 173, 0), 2, cv2.LINE_AA)
        
        if self.summary_types[self.summary_type_index] == "Vardiya":
            self.__plot_shift_summary(ui_frame)

        picasso.draw_image_on_frame(ui_frame, image_name="ozet_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        #put fetched frame to the window
        cv2.imshow(cv2_window_name, ui_frame)

        



    
