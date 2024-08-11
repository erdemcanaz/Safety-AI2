from modules import picasso
import cv2
import numpy as np

import requests, pprint
from typing import Dict, List
import datetime, time, random, base64, copy

class ISGApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "isg_data_fetch_period_s": 5, # fetch data every 5 seconds     
        "six_data_change_period_s": 2.5, # change the data every 10 seconds

        "main_image_bbox": (944, 84, 1854, 600),
        "image_bbox_0": (37, 145, 430, 368),
        "image_bbox_1": (475, 148, 868, 371),
        "image_bbox_2": (33, 444, 426, 666),
        "image_bbox_3": (475, 445, 868, 668),
        "image_bbox_4": (35, 740, 428, 962),
        "image_bbox_5": (475, 740, 868, 962),

    }

    def __init__(self):
        self.last_time_isg_data_fetch = 0
        self.fetched_data:list = None

        self.last_time_six_data_to_render_update = 0
        self.last_six_data_to_render = None           

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):    
        # Fetch ISG data
        if  (time.time() - self.last_time_isg_data_fetch) > self.CONSTANTS["isg_data_fetch_period_s"]:
            self.last_time_isg_data_fetch = time.time()
            fetched_list, status_code = active_user.request_ISG_ui_data()
            if status_code == 200:
                self.fetched_data = fetched_list
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ISG data fetched with status code: {status_code}")
       
        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0          

        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="ISG_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  

        # Draw user name
        text = active_user.get_token_person_name()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]            
        x = 1910-text_size[0]
        y = text_size[1]+5
        cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (239, 237, 232), 2, cv2.LINE_AA)

        # Draw date and shift
        today_date = datetime.datetime.now().strftime("%d.%m.%Y / %H:%M:%S")
        today_shift = "Vardiya-I " if datetime.datetime.now().hour < 8 else "Vardiya-II " if datetime.datetime.now().hour < 16 else "Vardiya-III "
        percentage = (datetime.datetime.now().hour%8) / 8
        cv2.putText(ui_frame, today_shift+today_date, (387, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.rectangle(ui_frame, (314, 95), (314+int(560*percentage), 110), (169, 96, 0), -1)


        cv2.imshow(cv2_window_name, ui_frame)

        



    
