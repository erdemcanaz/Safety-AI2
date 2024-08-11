from modules import picasso
import cv2
import numpy as np

import requests
from typing import Dict, List
import datetime

class OzetApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "data_fetch_period_s": 5, # fetch data every 5 seconds       
    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None
        pass

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):
        
        # Mouse input

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
        cv2.imshow(cv2_window_name, ui_frame)

        



    
