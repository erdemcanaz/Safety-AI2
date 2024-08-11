from modules import picasso
import cv2
import numpy as np

import requests
from typing import Dict, List
import datetime

class IhlalRaporlariApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "data_fetch_period_s": 5, # fetch data every 5 seconds       
        "start_date_shift_change_bbox": (752, 64, 826, 98),
        "end_date_shift_change_bbox": (1148, 64, 1222, 98),
    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None
        self.start_date_shift = 0
        self.end_date_shift = 0

        pass

    def __is_xy_in_bbox(self, x:int, y:int, bbox:tuple):
        x1, y1, x2, y2 = bbox
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return True
        return False 


    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):
        
        # Mouse input
        if mouse_input.get_last_leftclick_position() is not None:
            x, y = mouse_input.get_last_leftclick_position()
            mouse_input.clear_last_leftclick_position()
            if self.__is_xy_in_bbox(x, y, self.CONSTANTS["start_date_shift_change_bbox"]):
                self.start_date_shift = (self.start_date_shift + 1) % 3
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["end_date_shift_change_bbox"]):
                self.end_date_shift = (self.end_date_shift + 1) % 3

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0          

        today_date = datetime.datetime.now().strftime("%d.%m.%Y / %H:%M:%S / ")
        today_shift = "I" if datetime.datetime.now().hour < 8 else "II" if datetime.datetime.now().hour < 16 else "III"
        
        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="ihlal_raporlari_app_page", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  

        # put current user name
        text = active_user.get_token_person_name()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]            
        x = 1886-text_size[0]
        y = 1040
        cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (239, 237, 232), 2, cv2.LINE_AA)    
        # put start date and shift
        cv2.putText(ui_frame, today_date+today_shift, (1515, 89), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)
        # put start and end date shift
        cv2.putText(ui_frame, str(self.start_date_shift+1), (761, 89), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.putText(ui_frame, str(self.end_date_shift+1), (1155, 89), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)
                                                               
        cv2.imshow(cv2_window_name, ui_frame)

        



    
