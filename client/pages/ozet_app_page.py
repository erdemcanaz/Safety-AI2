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

        "hard_hat_rule_show_button_bbox": (1500, 573, 1652 ,602),
        "restricted_area_rule_show_button_bbox": (1660, 573, 1817 ,602),

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

        self.show_hard_hat_summary = True
        self.show_restricted_area_summary = True

        self.mock_data = None
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
        if self.mock_data is None or (time.time() - self.last_time_data_fetch) > 5:
            self.last_time_data_fetch = time.time()

            self.mock_data = {}
            self.mock_data["total_person_analyzed"] = random.randint(0, 1000000)
            self.mock_data["total_frame_analyzed"] = random.randint(0, 1000000)
            self.mock_data["total_hard_hat_approved"] = random.randint(0, 1000000)
            self.mock_data["total_hard_hat_rejected"] = random.randint(0, 1000000)
            self.mock_data["total_restricted_area_approved"] = random.randint(0, 1000000)
            self.mock_data["total_restricted_area_rejected"] = random.randint(0, 1000000)

            self.mock_data["shift_person_analyzed"] = random.randint(0, 10000)
            self.mock_data["shift_frame_analyzed"] = random.randint(0, 10000)

            for i in range(8):
                self.mock_data[f"entry_{i}"] = {
                    "hard_hat_approved": random.randint(0, 10000),
                    "hard_hat_rejected": random.randint(0, 10000),
                    "restricted_area_approved": random.randint(0, 10000),
                    "restricted_area_rejected": random.randint(0, 10000),
                }

        # plot text data for total
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_person_analyzed'])}", (554, 221), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_frame_analyzed'])}", (554, 272), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_hard_hat_approved'])}", (836, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_hard_hat_rejected'])}", (930, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = self.mock_data['total_hard_hat_approved']/(self.mock_data['total_hard_hat_rejected']+self.mock_data['total_hard_hat_approved']) if self.mock_data['total_hard_hat_rejected']+self.mock_data['total_hard_hat_approved'] > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (844, 256), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_restricted_area_approved'])}", (1119, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_restricted_area_rejected'])}", (1213, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = self.mock_data['total_restricted_area_approved']/(self.mock_data['total_restricted_area_rejected']+self.mock_data['total_restricted_area_approved']) if self.mock_data['total_restricted_area_rejected']+self.mock_data['total_restricted_area_approved'] > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (1129, 256), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        # plot text data for shift
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['shift_person_analyzed'])}", (554, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['shift_frame_analyzed'])}", (554, 451), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        total_hard_hat_approved = sum([self.mock_data[f"entry_{i}"]["hard_hat_approved"] for i in range(8)])
        total_hard_hat_rejected = sum([self.mock_data[f"entry_{i}"]["hard_hat_rejected"] for i in range(8)])
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_hard_hat_approved)}", (836, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_hard_hat_rejected)}", (930, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = total_hard_hat_approved/(total_hard_hat_rejected+total_hard_hat_approved) if total_hard_hat_rejected+total_hard_hat_approved > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (844, 436), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        total_restricted_area_approved = sum([self.mock_data[f"entry_{i}"]["restricted_area_approved"] for i in range(8)])
        total_restricted_area_rejected = sum([self.mock_data[f"entry_{i}"]["restricted_area_rejected"] for i in range(8)])
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_restricted_area_approved)}", (1119, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_restricted_area_rejected)}", (1213, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = total_restricted_area_approved/(total_restricted_area_rejected+total_restricted_area_approved) if total_restricted_area_rejected+total_restricted_area_approved > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (1129, 436), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        # plot timestamps
        period = 152
        hour_now = datetime.datetime.now().hour
        first_shift_hour = hour_now - hour_now%8
        for i in range(9):
            color = (154,108,15) if i %2 == 0 else (229,218,194)
            cv2.putText(ui_frame, f"{first_shift_hour+i:02d}:00", (554+i*period, 1000), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # plot bars data
        hard_hat_bar_top_coordinates = []
        restricted_area_bar_top_coordinates = []

        bar_height = 362
        bar_width = 30
        spacing = (160-2*bar_width)//3
        for i in range(8):
            shift_data = self.mock_data[f"entry_{i}"]
            hard_hat_suces = shift_data["hard_hat_approved"]/(shift_data["hard_hat_rejected"]+shift_data["hard_hat_approved"]) if shift_data["hard_hat_rejected"]+shift_data["hard_hat_approved"] > 0 else 5
            restricted_area_suces = shift_data["restricted_area_approved"]/(shift_data["restricted_area_rejected"]+shift_data["restricted_area_approved"]) if shift_data["restricted_area_rejected"]+shift_data["restricted_area_approved"] > 0 else 5
            
            top_y = 608
            hard_hat_top_y = top_y + int(bar_height*(1-hard_hat_suces))
            restricted_area__top_y = top_y + int(bar_height*(1-restricted_area_suces))
            hard_hat_x = 554+spacing + i*period
            restricted_area_x = 554+2*spacing + bar_width + i*period

            if self.show_hard_hat_summary: cv2.rectangle(ui_frame, (hard_hat_x,hard_hat_top_y), (hard_hat_x+bar_width,969), (195, 184, 161), -1)
            if self.show_hard_hat_summary:cv2.putText(ui_frame, self.__format_count_to_hr(shift_data["hard_hat_approved"]), (hard_hat_x, hard_hat_top_y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (195, 184, 161), 2)
            if self.show_restricted_area_summary: cv2.rectangle(ui_frame, (restricted_area_x,restricted_area__top_y), (restricted_area_x+bar_width,969), (206, 168, 182), -1)
            if self.show_restricted_area_summary: cv2.putText(ui_frame, self.__format_count_to_hr(shift_data["restricted_area_approved"]), (restricted_area_x, restricted_area__top_y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (206, 168, 182), 2)
            
            if self.show_hard_hat_summary: cv2.circle(ui_frame, (hard_hat_x+bar_width//2, hard_hat_top_y), 10, (154, 108, 15), -1)
            if self.show_restricted_area_summary: cv2.circle(ui_frame, (restricted_area_x+bar_width//2, restricted_area__top_y), 10, (203, 110, 145), -1)

            hard_hat_bar_top_coordinates.append((hard_hat_x+bar_width//2, hard_hat_top_y))
            restricted_area_bar_top_coordinates.append((restricted_area_x+bar_width//2, restricted_area__top_y))

        if self.show_hard_hat_summary: picasso.plot_smooth_curve_on_frame(ui_frame, hard_hat_bar_top_coordinates, color=(154, 108, 15), thickness=3)
        if self.show_restricted_area_summary: picasso.plot_smooth_curve_on_frame(ui_frame, restricted_area_bar_top_coordinates, color=(203, 110, 145), thickness=3)
   
    def __plot_day_summary(self, ui_frame:np.ndarray):
        #TODO: check if valid data is fetched
        if self.mock_data is None or (time.time() - self.last_time_data_fetch) > 5:
            self.last_time_data_fetch = time.time()

            self.mock_data = {}
            self.mock_data["total_person_analyzed"] = random.randint(0, 1000000)
            self.mock_data["total_frame_analyzed"] = random.randint(0, 1000000)
            self.mock_data["total_hard_hat_approved"] = random.randint(0, 1000000)
            self.mock_data["total_hard_hat_rejected"] = random.randint(0, 1000000)
            self.mock_data["total_restricted_area_approved"] = random.randint(0, 1000000)
            self.mock_data["total_restricted_area_rejected"] = random.randint(0, 1000000)

            self.mock_data["shift_person_analyzed"] = random.randint(0, 10000)
            self.mock_data["shift_frame_analyzed"] = random.randint(0, 10000)

            for i in range(24):
                self.mock_data[f"entry_{i}"] = {
                    "hard_hat_approved": random.randint(0, 10000),
                    "hard_hat_rejected": random.randint(0, 10000),
                    "restricted_area_approved": random.randint(0, 10000),
                    "restricted_area_rejected": random.randint(0, 10000),
                }

        # plot text data for total
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_person_analyzed'])}", (554, 221), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_frame_analyzed'])}", (554, 272), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_hard_hat_approved'])}", (836, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_hard_hat_rejected'])}", (930, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = self.mock_data['total_hard_hat_approved']/(self.mock_data['total_hard_hat_rejected']+self.mock_data['total_hard_hat_approved']) if self.mock_data['total_hard_hat_rejected']+self.mock_data['total_hard_hat_approved'] > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (844, 256), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_restricted_area_approved'])}", (1119, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['total_restricted_area_rejected'])}", (1213, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = self.mock_data['total_restricted_area_approved']/(self.mock_data['total_restricted_area_rejected']+self.mock_data['total_restricted_area_approved']) if self.mock_data['total_restricted_area_rejected']+self.mock_data['total_restricted_area_approved'] > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (1129, 256), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        # plot text data for shift
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['shift_person_analyzed'])}", (554, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(self.mock_data['shift_frame_analyzed'])}", (554, 451), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        total_hard_hat_approved = sum([self.mock_data[f"entry_{i}"]["hard_hat_approved"] for i in range(24)])
        total_hard_hat_rejected = sum([self.mock_data[f"entry_{i}"]["hard_hat_rejected"] for i in range(24)])
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_hard_hat_approved)}", (836, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_hard_hat_rejected)}", (930, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = total_hard_hat_approved/(total_hard_hat_rejected+total_hard_hat_approved) if total_hard_hat_rejected+total_hard_hat_approved > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (844, 436), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        total_restricted_area_approved = sum([self.mock_data[f"entry_{i}"]["restricted_area_approved"] for i in range(24)])
        total_restricted_area_rejected = sum([self.mock_data[f"entry_{i}"]["restricted_area_rejected"] for i in range(24)])
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_restricted_area_approved)}", (1119, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        cv2.putText(ui_frame, f"{self.__format_count_to_hr(total_restricted_area_rejected)}", (1213, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (154, 108, 15), 1)
        percentage = total_restricted_area_approved/(total_restricted_area_rejected+total_restricted_area_approved) if total_restricted_area_rejected+total_restricted_area_approved > 0 else 0
        cv2.putText(ui_frame, f"{percentage:.1%}", (1129, 436), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (154, 108, 15), 1)

        # plot timestamps
        period = 152
        for i in range(9):
            color = (154,108,15) if i %2 == 0 else (229,218,194)
            cv2.putText(ui_frame, f"{3*i:02d}:00", (554+i*period, 1000), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # plot bars data
        hard_hat_bar_top_coordinates = []
        restricted_area_bar_top_coordinates = []

        bar_height = 362
        bar_width = 10
        plot_shift = 10 #TODO: this is a quick fix, it should not be used however curve shifts somehow
        spacing = (period-6*bar_width)//7

        x_cursor = 554
        for i in range(8):
            for j in range(3):

                shift_data = self.mock_data[f"entry_{i*3+j}"]            
                hard_hat_suces = shift_data["hard_hat_approved"] / (shift_data["hard_hat_rejected"] + shift_data["hard_hat_approved"]) if shift_data["hard_hat_rejected"] + shift_data["hard_hat_approved"] > 0 else 5
                restricted_area_suces = shift_data["restricted_area_approved"] / (shift_data["restricted_area_rejected"] + shift_data["restricted_area_approved"]) if shift_data["restricted_area_rejected"] + shift_data["restricted_area_approved"] > 0 else 5
                
                top_y = 608
                hard_hat_top_y = top_y + int(bar_height * (1 - hard_hat_suces))
                restricted_area_top_y = top_y + int(bar_height * (1 - restricted_area_suces))
                                                
                x_cursor += spacing 
                # Draw the hard hat bar
                if self.show_hard_hat_summary:cv2.rectangle(ui_frame, (x_cursor, hard_hat_top_y), (x_cursor + bar_width, 969), (195, 184, 161), -1)
                if self.show_hard_hat_summary:cv2.circle(ui_frame, (x_cursor + bar_width // 2, hard_hat_top_y), 5, (154, 108, 15), -1)
                hard_hat_bar_top_coordinates.append((x_cursor + bar_width // 2, restricted_area_top_y))
                if self.show_hard_hat_summary:cv2.putText(ui_frame, self.__format_count_to_hr(shift_data["hard_hat_approved"]), (x_cursor, hard_hat_top_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (195, 184, 161), 1)
                x_cursor+=bar_width+spacing
                
                # Draw the restricted area bar
                if self.show_restricted_area_summary: cv2.rectangle(ui_frame, (x_cursor, restricted_area_top_y), (x_cursor + bar_width, 969), (206, 168, 182), -1)
                if self.show_restricted_area_summary: cv2.circle(ui_frame, (x_cursor + bar_width // 2, restricted_area_top_y), 5, (203, 110, 145), -1)
                restricted_area_bar_top_coordinates.append((x_cursor + bar_width // 2, hard_hat_top_y))
                if self.show_restricted_area_summary: cv2.putText(ui_frame, self.__format_count_to_hr(shift_data["restricted_area_approved"]), (x_cursor, restricted_area_top_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (206, 168, 182), 1)
                x_cursor+=bar_width               
            x_cursor += spacing

        if self.show_hard_hat_summary:  picasso.plot_smooth_curve_on_frame(ui_frame, hard_hat_bar_top_coordinates, color=(154, 108, 15), thickness=3)
        if self.show_restricted_area_summary: picasso.plot_smooth_curve_on_frame(ui_frame, restricted_area_bar_top_coordinates, color=(203, 110, 145), thickness=3)

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
                self.mock_data = None
                self.show_hard_hat_summary = True
                self.show_restricted_area_summary = True
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["increase_summary_type_bbox"]):
                self.summary_type_index = min(len(self.summary_types)-1, self.summary_type_index+1)
                self.mock_data = None
                self.show_hard_hat_summary = True
                self.show_restricted_area_summary = True
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["hard_hat_rule_show_button_bbox"]):
                self.show_hard_hat_summary = not self.show_hard_hat_summary
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["restricted_area_rule_show_button_bbox"]):
                self.show_restricted_area_summary = not self.show_restricted_area_summary
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
        elif self.summary_types[self.summary_type_index] == "Gun":
            self.__plot_day_summary(ui_frame)

        picasso.draw_image_on_frame(ui_frame, image_name="ozet_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        #put fetched frame to the window
        cv2.imshow(cv2_window_name, ui_frame)

        



    
