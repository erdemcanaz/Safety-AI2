from modules import picasso, text_transformer
import cv2
import numpy as np

import requests
from typing import Dict, List

class KameralarApp():

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
        if mouse_input.get_last_leftclick_position() is not None:
            x, y = mouse_input.get_last_leftclick_position()
            mouse_input.clear_last_leftclick_position()         

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC -> direct to login page
            active_user.set_username(new_username = "")
            active_user.set_password(new_password = "")
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0
          
        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="kameralar_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        cv2.imshow(cv2_window_name, ui_frame)

        
