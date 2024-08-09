from modules import picasso
import cv2
import numpy as np

import requests
from typing import Dict, List

class LoginPage():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "username_bbox": (222, 481, 800, 550),
        "username_text_bleft": (300, 527),
        "password_bbox": (222, 605, 800,670),
        "password_text_bleft": (300, 650),
        "show_password_bbox": (814, 605, 883, 670),

        "login": (222,690,800,752)
    }
    def __init__(self):
        self.username_text_field = ""
        self.password_text_field = ""
        self.show_password = False

        self.secondary_mode = 0
    
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
            if self.__is_xy_in_bbox(x, y, self.CONSTANTS["username_bbox"]):
                self.secondary_mode = 1 # username clicked
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["password_bbox"]):
                self.secondary_mode = 2 # password clicked
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["show_password_bbox"]):
                self.show_password = not self.show_password
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["login"]):
                status_code = None
                try:
                    is_authenticated, status_code = active_user.get_acces_token()
                    print(f"User {active_user.get_username()} is authenticated -> {is_authenticated} -> {status_code}")
                except Exception as e:
                    print(f"Error: {e}")       
                
                print(f"Status code: {status_code}")
                if status_code is None: # server is not reachable
                    program_state[0] = 2
                    program_state[1] = 0
                    program_state[2] = 0    
                elif status_code != 200: # user not found
                    active_user.set_username(new_username = "")
                    active_user.set_password(new_password = "")   
                
                    program_state[0] = 3
                    program_state[1] = 0
                    program_state[2] = 0   
                elif status_code == 200: # user authenticated, direct to which app page
                    program_state[0] = 4
                    program_state[1] = 0
                    program_state[2] = 0

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            program_state[0] = 0
            program_state[1] = 0
            program_state[2] = 0
        elif pressed_key == 8: #BACKSPACE
            if self.secondary_mode == 1 and len(active_user.get_username())>0: #username
                active_user.set_username(new_username = active_user.get_username()[:-1])
            elif self.secondary_mode == 2 and len(active_user.get_password())>0:
                active_user.set_password(new_password = active_user.get_password()[:-1])                
        elif chr(pressed_key) in self.CONSTANTS["allowed_keys"]:
            if self.secondary_mode == 1:
                active_user.set_username(new_username = active_user.get_username() + chr(pressed_key))
            elif self.secondary_mode == 2:
                active_user.set_password(new_password = active_user.get_password() + chr(pressed_key))      

        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="login_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        cv2.putText(ui_frame, active_user.get_username(), (self.CONSTANTS["username_text_bleft"][0], self.CONSTANTS["username_text_bleft"][1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (170,95,0), 2, cv2.LINE_AA)
        
        if self.show_password:
            cv2.putText(ui_frame, active_user.get_password(), (self.CONSTANTS["password_text_bleft"][0], self.CONSTANTS["password_text_bleft"][1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (170,95,0), 2, cv2.LINE_AA)
            picasso.draw_image_on_frame(ui_frame, image_name="anil_right_looking", x=self.CONSTANTS["show_password_bbox"][0], y=self.CONSTANTS["show_password_bbox"][1], width=100, height=100, maintain_aspect_ratio=True)
        else:
            cv2.putText(ui_frame, "*"*len(active_user.get_password()), (self.CONSTANTS["password_text_bleft"][0], self.CONSTANTS["password_text_bleft"][1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (170,95,0), 2, cv2.LINE_AA)
            picasso.draw_image_on_frame(ui_frame, image_name="anil_left_looking", x=self.CONSTANTS["show_password_bbox"][0], y=self.CONSTANTS["show_password_bbox"][1], width=100, height=100, maintain_aspect_ratio=True)
        cv2.imshow(cv2_window_name, ui_frame)

        



    
