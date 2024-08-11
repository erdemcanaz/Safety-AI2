from modules import picasso
import cv2
import numpy as np

import requests
from typing import Dict, List

class WhichApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",      
    }

    def __init__(self):
        pass       
    
    def __is_xy_in_bbox(self, x:int, y:int, bbox:tuple):
        x1, y1, x2, y2 = bbox
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return True
        return False 

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):
        
        # Mouse input
        #TODO:

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC -> direct to login page
            active_user.set_username(new_username = "")
            active_user.set_password(new_password = "")
            program_state[0] = 1
            program_state[1] = 0
            program_state[2] = 0
          
        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="which_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        
        app_name_to_hr_name = {
            "ISG_APP": "ISG - UI",
            "KALITE_APP": "Kalite - UI",
            "GUVENLIK_APP": "Guvenlik - UI",
            "IHLAL_RAPORLARI_APP": "Ihlal Raporlari",
            "OZET_APP": "Ozet Sayfasi",
            "KURALLAR_APP": "Kurallar Sayfasi",
            "KAMERALAR_APP": "Kameralar Sayfasi",
            "IOT_CIHAZLAR_APP": "IoT Cihazlar",
            "TERCIHLER_APP": "Tercihler Sayfasi",
        }
        for app_no, app_name in enumerate(["ISG_APP","KALITE_APP","GUVENLIK_APP","IHLAL_RAPORLARI_APP","OZET_APP","KURALLAR_APP","KAMERALAR_APP","IOT_CIHAZLAR_APP","TERCIHLER_APP"]):        
            if app_name in active_user.get_token_allowed_tos():
                picasso.draw_image_on_frame(ui_frame, image_name="app_bar_dark_blue", x=212, y=288+app_no*75, width=589, height=63, maintain_aspect_ratio=True)
            else:
                picasso.draw_image_on_frame(ui_frame, image_name="app_bar_light_blue", x=212, y=288+app_no*75, width=589, height=63, maintain_aspect_ratio=True)

            # Place app names in the middle of the app bars
            text = app_name_to_hr_name[app_name]
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.25, 2)[0]            
            x = 212 + (589 - text_size[0]) // 2
            y = 288 + app_no * 75 + 45
            cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(ui_frame, f"{active_user.get_token_person_name()}", (410, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (169, 96, 0), 3, cv2.LINE_AA)

        cv2.imshow(cv2_window_name, ui_frame)

        
