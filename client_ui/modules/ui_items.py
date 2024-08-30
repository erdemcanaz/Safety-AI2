import time
import numpy as np
import cv2
import modules.picasso as picasso
from typing import Tuple, List

class Background():
    def __init__(self, background_name:str = None, default_resolution = (1920,1080)):
        self.background_name = background_name
        self.background_resolution = default_resolution

    def is_clickable(self):
        return False
    
    def is_writeable(self):
        return False
    
    def get_background_frame(self) -> np.ndarray:
        background_frame = np.ones((self.background_resolution[1], self.background_resolution[0], 3), np.uint8) * 255
        picasso.draw_image_on_frame(
            frame = background_frame, 
            image_name= self.background_name, 
            x = 0, 
            y= 0, 
            width = self.background_resolution[0],
            height = self.background_resolution[1],
            maintain_aspect_ratio = False
        )
        return background_frame
        
class Button():
    def __init__(self, identifier:str = "default-id",pos_n:Tuple[float, float] = None, size_n:Tuple[float, float] = None, button_render_configs:dict = None):
        self.identifier = identifier
        self.pos_n = pos_n
        self.size_n = size_n
        self.button_render_configs = button_render_configs
        self.is_mouse_over = False  
        
    def is_focusable(self):
        return False
    
    def is_clickable(self):
        return True
    
    def is_writeable(self):
        return False
    
    def is_left_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            return ["left_clicked_callback", self.identifier, True]
        else:
            return ["left_clicked_callback", self.identifier, False]
    
    def is_right_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            return ["right_clicked_callback", self.identifier, True]
        else:
            return ["right_clicked_callback", self.identifier, False]
        
    def is_mouse_over_callback(self, mouse_n:Tuple[float, float]):
        if self.pos_n[0] < mouse_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < mouse_n[1] < self.pos_n[1] + self.size_n[1]:
            self.is_mouse_over = True
            return ["mouse_over_callback", self.identifier, True, "over"]
        else:
            if self.is_mouse_over:
                self.is_mouse_over = False
                return ["mouse_over_callback", self.identifier, True, "not_over"]
            else:
                return ["mouse_over_callback", self.identifier, False, "not_over"]
            
    def get_reset_page_frame_required_callbacks(self):
        return []
    
    def get_redraw_required_callbacks(self):
        return [
            ["mouse_over_callback", self.identifier, True, "over"],
            ["mouse_over_callback", self.identifier, True, "not_over"]
        ]
    
    def draw(self, frame:np.ndarray=None):
        button_width = int(self.size_n[0]*frame.shape[1])
        button_height = int(self.size_n[1]*frame.shape[0])
        button_x = int(self.pos_n[0]*frame.shape[1])
        button_y = int(self.pos_n[1]*frame.shape[0])
            
        if self.button_render_configs.get('button_style', '')=="basic":
            # Basic button style
            # > Button text (when not over & over)
            # > Button text color (when not over & over)
            # > Button text font scale (when not over & over)
            # > Button text thickness (when not over & over)
            # > Button background color (when not over & over)
            # > Button border color (when not over & over)
            # > Button border thickness (when not over & over)
            button_text = self.button_render_configs['button_text']
            button_text_color = self.button_render_configs['button_text_color'][0 if not self.is_mouse_over else 1]
            button_text_font_scale = self.button_render_configs['button_text_font_scale'][0 if not self.is_mouse_over else 1]
            button_text_thickness = self.button_render_configs['button_text_thickness'][0 if not self.is_mouse_over else 1]
            button_background_color = self.button_render_configs['button_background_color'][0 if not self.is_mouse_over else 1]
            button_border_color = self.button_render_configs['button_border_color'][0 if not self.is_mouse_over else 1]
            button_border_thickness = self.button_render_configs['button_border_thickness'][0 if not self.is_mouse_over else 1]
            button_text_font_scale = self.button_render_configs['button_text_font_scale'][0 if not self.is_mouse_over else 1]

            # Draw button background
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), button_background_color, -1)
            # Draw button border
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), button_border_color, button_border_thickness)
            # Draw button text
            picasso.draw_text_on_frame(frame=frame, alignment='center', text = button_text, position=(button_x, button_y), area_size = (button_width, button_height), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=button_text_font_scale, text_color=button_text_color, thickness=button_text_thickness, padding=10)

class TextField():

    def __init__(self, identifier:str = "default-id",pos_n:Tuple[float, float] = None, size_n:Tuple[float, float] = None, text_field_render_configs:dict = None):
        self.identifier = identifier
        self.pos_n = pos_n
        self.size_n = size_n
        self.text_field_render_configs = text_field_render_configs       
        self.text = ""

    def is_focusable(self):
        return False
    
    def is_clickable(self):
        return False
    
    def is_writeable(self):
        return True
    
    def is_left_clicked_callback(self, click_n:Tuple[float, float]):
        return ["left_clicked_callback", self.identifier, False]
    
    def is_right_clicked_callback(self, click_n:Tuple[float, float]):
        return ["right_clicked_callback", self.identifier, False]
    
    def is_mouse_over_callback(self, mouse_n:Tuple[float, float]):
        return ["mouse_over_callback", self.identifier, False]
    
    def is_key_pressed_callback(self, key:int):
        return ["key_pressed_callback", self.identifier, True]
    
    def get_reset_page_frame_required_callbacks(self):
        return []
    
    def get_redraw_required_callbacks(self):
        return []
    
    def set_text(self, text:str):
        self.text = text
    
    def get_text(self):
        return self.text
    
    def draw(self, frame:np.ndarray=None):

        if self.text_field_render_configs.get('text_field_style', '')=="basic":
            # Basic text field style
            # > Text field style (basic)
            # > Text field default text 
            # > Text field default text color
            # > Text field text color
            # > Text field text font scale
            # > Text field text thickness
            # > Text field background color
            # > Text field border color
            # > Text field border thickness

            text_field_default_text = self.text_field_render_configs['text_field_default_text']
            text_field_text_color = self.text_field_render_configs['text_field_text_color'][1]
            text_field_text_font_scale = self.text_field_render_configs['text_field_text_font_scale'][0]
            text_field_text_thickness = self.text_field_render_configs['text_field_text_thickness'][0]
            text_field_background_color = self.text_field_render_configs['text_field_background_color'][0]
            text_field_border_color = self.text_field_render_configs['text_field_border_color'][0]
            text_field_border_thickness = self.text_field_render_configs['text_field_border_thickness'][0]
            text_field_text_font_scale = self.text_field_render_configs['text_field_text_font_scale'][0]

            # Draw text field background
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), text_field_background_color, -1)
            # Draw text field border
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), text_field_border_color, text_field_border_thickness)
            # Draw text field text
            picasso.draw_text_on_frame(frame=frame, alignment='left', text = self.text if len(self.text)>0 else text_field_default_text, position=(int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), area_size = (int(self.size_n[0]*frame.shape[1]), int(self.size_n[1]*frame.shape[0])), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=text_field_text_font_scale, text_color=text_field_text_color, thickness=text_field_text_thickness, padding=10)

class TextInput():
    def __init__(self, identifier:str = "default-id",pos_n:Tuple[float, float] = None, size_n:Tuple[float, float] = None, text_input_render_configs:dict = None):
        self.identifier = identifier
        self.pos_n = pos_n
        self.size_n = size_n
        self.text_input_render_configs = text_input_render_configs
        self.is_mouse_over = False
        self.is_focused = False # True if the text input is focused and ready to be written on
        self.text = ""

    def is_focusable(self):
        return True
    
    def is_clickable(self):
        return True
    
    def is_writeable(self):
        return True
    
    def release_focus(self):
        self.is_focused = False

    def is_left_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            self.is_focused = not self.is_focused
            return ["left_clicked_callback", self.identifier, True, "focus" if self.is_focused else "release_focus"]
        else:
            return ["left_clicked_callback", self.identifier, False]
        
    def is_right_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            return ["right_clicked_callback", self.identifier, True]
        else:
            return ["right_clicked_callback", self.identifier, False]
        
    def is_mouse_over_callback(self, mouse_n:Tuple[float, float]):
        if self.pos_n[0] < mouse_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < mouse_n[1] < self.pos_n[1] + self.size_n[1]:
            self.is_mouse_over = True
            return ["mouse_over_callback", self.identifier, True]
        else:
            self.is_mouse_over = False
            return ["mouse_over_callback", self.identifier, False]
        
    def is_key_pressed_callback(self, key:int):
        ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_@ " 
        if self.is_focused:
            if key==8: # Backspace
                self.text = self.text[:-1]
            elif chr(key) in ALLOWED_CHARS:
                self.text += chr(key)
            
            return ["key_pressed_callback", self.identifier, True]
        else:
            return ["key_pressed_callback", self.identifier, False]
    
    def get_reset_page_frame_required_callbacks(self):
        return []
    
    def get_redraw_required_callbacks(self):
        return [
            ["left_clicked_callback", self.identifier, True, 'focus'],
            ["left_clicked_callback", self.identifier, True, 'release_focus'],
            ["key_pressed_callback", self.identifier, True]
        ]
    
    def set_text(self, text):
        self.text = text
        
    def get_text(self):
        return self.text
    
    def draw(self, frame:np.ndarray=None):
        text_input_width = int(self.size_n[0]*frame.shape[1])
        text_input_height = int(self.size_n[1]*frame.shape[0])
        text_input_x = int(self.pos_n[0]*frame.shape[1])
        text_input_y = int(self.pos_n[1]*frame.shape[0])
            
        if self.text_input_render_configs.get('text_input_style', '')=="basic":
            # Basic text input style
            # > Text input style (basic)
            # > Text input default text 
            # > Text input default text color
            # > Text input text color (when not over & over)
            # > Text input text font scale (when not over & over)
            # > Text input text thickness (when not over & over)
            # > Text input background color (when not over & over)
            # > Text input border color (when not over & over)
            # > Text input border thickness (when not over & over)

            text_input_default_text = self.text_input_render_configs['text_input_default_text']
            text_input_default_text_color = self.text_input_render_configs['text_input_default_text_color']
            text_input_text_color = self.text_input_render_configs['text_input_text_color'][0 if not self.is_focused else 1]
            text_input_text_font_scale = self.text_input_render_configs['text_input_text_font_scale'][0 if not self.is_focused else 1]
            text_input_text_thickness = self.text_input_render_configs['text_input_text_thickness'][0 if not self.is_focused else 1]
            text_input_background_color = self.text_input_render_configs['text_input_background_color'][0 if not self.is_focused else 1]
            text_input_border_color = self.text_input_render_configs['text_input_border_color'][0 if not self.is_focused else 1]
            text_input_border_thickness = self.text_input_render_configs['text_input_border_thickness'][0 if not self.is_focused else 1]
            text_input_text_font_scale = self.text_input_render_configs['text_input_text_font_scale'][0 if not self.is_focused else 1]

            # Draw text input background
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), text_input_background_color, -1)
            # Draw text input border
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), text_input_border_color, text_input_border_thickness)
            # Draw text input text
            additional_char = "|" if self.is_focused and time.time()%1<0.5 else " "
            if self.text=="":
                picasso.draw_text_on_frame(frame=frame, alignment='left', text = text_input_default_text+additional_char, position=(text_input_x, text_input_y), area_size = (text_input_width, text_input_height), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=text_input_text_font_scale, text_color=text_input_default_text_color, thickness=text_input_text_thickness, padding=10)
            else:
                picasso.draw_text_on_frame(frame=frame, alignment='left', text = self.text+additional_char, position=(text_input_x, text_input_y), area_size = (text_input_width, text_input_height), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=text_input_text_font_scale, text_color=text_input_text_color, thickness=text_input_text_thickness, padding=10)

class PasswordTextInput():
    def __init__(self, identifier:str = "default-id",pos_n:Tuple[float, float] = None, show_icon_percentage:float=0.1, size_n:Tuple[float, float] = None, password_text_input_render_configs:dict = None):
        self.identifier = identifier
        self.pos_n = pos_n
        self.show_icon_percentage = show_icon_percentage # Percentage of the text input width to show the eye icon
        self.size_n = size_n
        self.password_text_input_render_configs = password_text_input_render_configs
        self.is_mouse_over = False
        self.is_shown = False # True if the password is shown
        self.is_focused = False # True if the text input is focused and ready to be written on
        self.password = ""

    def is_focusable(self):
        return True
    
    def release_focus(self):
        self.is_focused = False
    
    def is_clickable(self):
        return True
    
    def is_writeable(self):
        return True
    
    def is_left_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            self.is_focused = not self.is_focused
            return ["left_clicked_callback", self.identifier, True, "focus" if self.is_focused else "release_focus"]
        elif self.pos_n[0] + self.size_n[0]< click_n[0] < self.pos_n[0] + self.size_n[0]*(1+self.show_icon_percentage)  and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            self.is_shown = not self.is_shown
            return ["left_clicked_callback", self.identifier, True, "show" if self.is_shown else "hide"]
        else:
            return ["left_clicked_callback", self.identifier, False]
        
    def is_right_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            return ["right_clicked_callback", self.identifier, True]
        else:
            return ["right_clicked_callback", self.identifier, False]
        
    def is_mouse_over_callback(self, mouse_n:Tuple[float, float]):
        if self.pos_n[0] < mouse_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < mouse_n[1] < self.pos_n[1] + self.size_n[1]:
            self.is_mouse_over = True
            return ["mouse_over_callback", self.identifier, True]
        else:
            self.is_mouse_over = False
            return ["mouse_over_callback", self.identifier, False]
        
    def is_key_pressed_callback(self, key:int):
        ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_@ " 
        if self.is_focused:
            if key==8:
                self.password = self.password[:-1]
            elif chr(key) in ALLOWED_CHARS:
                self.password += chr(key)
            return ["key_pressed_callback", self.identifier, True]
        else:
            return ["key_pressed_callback", self.identifier, False]
    
    def get_reset_page_frame_required_callbacks(self):
        return [
            ["left_clicked_callback", self.identifier, True, 'show'],
            ["left_clicked_callback", self.identifier, True, 'hide'],
        ]
    
    def get_redraw_required_callbacks(self):
        return [
            ["left_clicked_callback", self.identifier, True, 'focus'],
            ["left_clicked_callback", self.identifier, True, 'release_focus'],
        ]
    
    def get_text(self):
        return self.password
    
    def draw(self, frame:np.ndarray=None):
        password_text_input_width = int(self.size_n[0]*frame.shape[1])
        password_text_input_height = int(self.size_n[1]*frame.shape[0])
        password_text_input_x = int(self.pos_n[0]*frame.shape[1])
        password_text_input_y = int(self.pos_n[1]*frame.shape[0])
            
        if self.password_text_input_render_configs.get('password_text_input_style', '')=="basic":
            # Basic password text input style
            # > Password text input style (basic)
            # > Password text input default text 
            # > Password text input default text color
            # > Password text input text color (when not over & over)
            # > Password text input text font scale (when not over & over)
            # > Password text input text thickness (when not over & over)
            # > Password text input background color (when not over & over)
            # > Password text input border color (when not over & over)
            # > Password text input border thickness (when not over & over)

            password_text_input_default_text = self.password_text_input_render_configs['password_text_input_default_text']
            password_text_input_default_text_color = self.password_text_input_render_configs['password_text_input_default_text_color']
            password_text_input_text_color = self.password_text_input_render_configs['password_text_input_text_color'][0 if not self.is_focused else 1]
            password_text_input_text_font_scale = self.password_text_input_render_configs['password_text_input_text_font_scale'][0 if not self.is_focused else 1]
            password_text_input_text_thickness = self.password_text_input_render_configs['password_text_input_text_thickness'][0 if not self.is_focused else 1]
            password_text_input_background_color = self.password_text_input_render_configs['password_text_input_background_color'][0 if not self.is_focused else 1]
            password_text_input_border_color = self.password_text_input_render_configs['password_text_input_border_color'][0 if not self.is_focused else 1]
            password_text_input_border_thickness = self.password_text_input_render_configs['password_text_input_border_thickness'][0 if not self.is_focused else 1]
            password_text_input_text_font_scale = self.password_text_input_render_configs['password_text_input_text_font_scale'][0 if not self.is_focused else 1]

            # Draw password text input background
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), password_text_input_background_color, -1)
            # Draw password text input border
            cv2.rectangle(frame, (int(self.pos_n[0]*frame.shape[1]), int(self.pos_n[1]*frame.shape[0])), (int((self.pos_n[0]+self.size_n[0])*frame.shape[1]), int((self.pos_n[1]+self.size_n[1])*frame.shape[0])), password_text_input_border_color, password_text_input_border_thickness)
            # Draw password text input show icon

            show_icon_bbox = (int((self.pos_n[0] + self.size_n[0]*(1+self.show_icon_percentage/3)) * frame.shape[1]), int(self.pos_n[1] * frame.shape[0]), int((self.pos_n[0] + self.size_n[0] * (1 + self.show_icon_percentage)) * frame.shape[1]), int((self.pos_n[1] + self.size_n[1]) * frame.shape[0]))
            if self.is_shown:
                picasso.draw_image_on_frame(frame=frame, image_name='eye_dark_blue', x=show_icon_bbox[0], y=show_icon_bbox[1], width=show_icon_bbox[2]-show_icon_bbox[0], height=show_icon_bbox[3]-show_icon_bbox[1], maintain_aspect_ratio=False)
            else:
                picasso.draw_image_on_frame(frame=frame, image_name='eye_light_blue', x=show_icon_bbox[0], y=show_icon_bbox[1], width=show_icon_bbox[2]-show_icon_bbox[0], height=show_icon_bbox[3]-show_icon_bbox[1], maintain_aspect_ratio=False)
                
            # Draw password text input text
            additional_char = "|" if self.is_focused and time.time()%1<0.5 else " "
            if self.password=="":
                picasso.draw_text_on_frame(frame=frame, alignment='left', text = password_text_input_default_text+additional_char, position=(password_text_input_x, password_text_input_y), area_size = (password_text_input_width, password_text_input_height), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=password_text_input_text_font_scale, text_color=password_text_input_default_text_color, thickness=password_text_input_text_thickness, padding=10)
            else:
                text = self.password if self.is_shown else "*"*(len(self.password))
                picasso.draw_text_on_frame(frame=frame, alignment='left', text = text+additional_char, position=(password_text_input_x, password_text_input_y), area_size = (password_text_input_width, password_text_input_height), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=password_text_input_text_font_scale, text_color=password_text_input_text_color, thickness=password_text_input_text_thickness, padding=10)

class BasicList():
    def __init__(self, identifier:str = "default-id", pos_n:Tuple[float, float] = None, size_n:Tuple[float, float] = None, list_render_configs:dict = None):
        self.identifier = identifier
        self.pos_n = pos_n
        self.size_n = size_n
        self.list_render_configs = list_render_configs
        self.is_mouse_over = False
        self.selected_item_index = None        
        self.item_per_page = list_render_configs.get('item_per_page', 10)
        self.number_of_columns_per_item = len(list_render_configs['colum_slicing_ratios'])

        self.all_list_items = [] # will be updated later 
        self.first_data_index_to_display = 0

    def is_focusable(self):
        return False
    
    def is_clickable(self):
        return True
    
    def is_writeable(self):
        return False
    
    def release_focus(self):
        self.is_focused = False

    def get_reset_page_frame_required_callbacks(self):
        return [        
           
        ]
    
    def get_redraw_required_callbacks(self):
        return [      
            ["mouse_over_callback", self.identifier, True, "over"],
            ["mouse_over_callback", self.identifier, True, "not_over_but_in_list"],
            ["mouse_over_callback", self.identifier, True, "not_over"],
            ["arrow_up_clicked", self.identifier, True, "scroll_up"],
            ["arrow_down_clicked", self.identifier, True, "scroll_down"],
        ]
    
    def get_xyn_corresponding_item_index(self, xyn:Tuple[float,float])  -> int:
        clicked_item_page_index = int((xyn[1]-self.pos_n[1])//(self.size_n[1]/self.list_render_configs["item_per_page"]))
        item_index = self.first_data_index_to_display + clicked_item_page_index
        if item_index>=len(self.all_list_items): item_index = None
        return item_index
    
    def get_xyn_corresponding_column_index(self, xyn:Tuple[float,float])  -> int:
        column_widths = [int(self.size_n[0]*self.list_render_configs['colum_slicing_ratios'][i]) for i in range(self.number_of_columns_per_item)]
        column_index = 0
        for i, column_width in enumerate(column_widths):
            if self.pos_n[0] + sum(column_widths[:i]) < xyn[0] < self.pos_n[0] + sum(column_widths[:i+1]):
                column_index = i
                break
        return column_index

    def is_left_clicked_callback(self, click_n:Tuple[float, float]):
        arrow_up_bbox_n = (
            self.pos_n[0] + self.size_n[0],
            self.pos_n[1],
            self.pos_n[0] + self.size_n[0] + self.list_render_configs["padding_n"]+ self.list_render_configs['scroll_bar_width_n'],
            self.pos_n[1] + self.list_render_configs["arrow_icon_height_n"]
        )
        arrow_down_bbox_n = (
            self.pos_n[0] + self.size_n[0],
            self.pos_n[1] + self.size_n[1] - self.list_render_configs["arrow_icon_height_n"],
            self.pos_n[0] + self.size_n[0] + self.list_render_configs["padding_n"]+ self.list_render_configs['scroll_bar_width_n'],
            self.pos_n[1] + self.size_n[1]
        )

        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            corresponding_item_index = self.get_xyn_corresponding_item_index(click_n)
            if corresponding_item_index is not None:
                return ["item_clicked_callback", self.identifier, True, corresponding_item_index]           
            return ["left_clicked_callback", self.identifier, False]
        elif arrow_up_bbox_n[0] < click_n[0] < arrow_up_bbox_n[2] and arrow_up_bbox_n[1] < click_n[1] < arrow_up_bbox_n[3]:
            self.first_data_index_to_display -=self.list_render_configs['item_per_page']
            return ["arrow_up_clicked", self.identifier, True, "scroll_up"]
        elif arrow_down_bbox_n[0] < click_n[0] < arrow_down_bbox_n[2] and arrow_down_bbox_n[1] < click_n[1] < arrow_down_bbox_n[3]:
            self.first_data_index_to_display += self.list_render_configs['item_per_page']
            return ["arrow_down_clicked", self.identifier, True, "scroll_down"]
        else:
            return ["left_clicked_callback", self.identifier, False]
        
    def is_right_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            corresponding_item_index = self.get_xyn_corresponding_item_index(click_n)
            if corresponding_item_index is not None:
                return ["item_right_clicked_callback", self.identifier, True, corresponding_item_index]           
            return ["item_right_clicked_callback", self.identifier, False]
        else:
            return ["right_clicked_callback", self.identifier, False]
        
    def is_mouse_over_callback(self, mouse_n:Tuple[float, float]):
        if self.pos_n[0] < mouse_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < mouse_n[1] < self.pos_n[1] + self.size_n[1]:
            corresponding_item_index = self.get_xyn_corresponding_item_index(mouse_n)
            for item in self.all_list_items:
                item['is_over'] = False                
            if corresponding_item_index is None:
                return ["mouse_over_callback", self.identifier, True, "not_over_but_in_list"]          
            self.all_list_items[corresponding_item_index]['is_over'] = True
            return ["mouse_over_callback", self.identifier, True, "over"]
        else: # not over
            if any([item['is_over'] for item in self.all_list_items]):
                for item in self.all_list_items:
                    item['is_over'] = False
                return ["mouse_over_callback", self.identifier, True, "not_over"]
            return ["mouse_over_callback", self.identifier, False, "not_over"]
    
    def set_list_items(self, items:List[dict]):
        self.all_list_items = []
        for item in items:
            column_names = [column_name for column_name in item.keys() if "COLUMN_" in column_name]
            if len(column_names)!=self.number_of_columns_per_item:
                raise ValueError(f"Number of columns in the item is not equal to the number of columns per item in the list. Expected: {self.number_of_columns_per_item}, Found: {len(column_names)}")
            item.setdefault("is_over", False)
            self.all_list_items.append(item)

    def get_list_item_info(self, item_index:int):
        return self.all_list_items[item_index]
    
    def draw(self, frame:np.ndarray=None):        
        if self.first_data_index_to_display >= len(self.all_list_items):
            self.first_data_index_to_display = max(0, len(self.all_list_items)-self.list_render_configs["item_per_page"])
        elif self.first_data_index_to_display < 0:
            self.first_data_index_to_display = 0

        items_to_display = self.all_list_items[self.first_data_index_to_display:min(self.first_data_index_to_display+self.list_render_configs["item_per_page"], len(self.all_list_items))]      
        list_width = int(self.size_n[0]*frame.shape[1])
        list_height = int(self.size_n[1]*frame.shape[0])
        list_x = int(self.pos_n[0]*frame.shape[1])
        list_y = int(self.pos_n[1]*frame.shape[0])

        colum_slicing_ratios = self.list_render_configs.get('colum_slicing_ratios')
        colum_total = sum(colum_slicing_ratios)
        colum_widths = [int(list_width*ratio/colum_total) for ratio in colum_slicing_ratios]
            
        if self.list_render_configs.get('list_style', '')=="basic":
            # Basic list style
            # > List style (basic)
            # > Number of items to display
            # > Colum slicing ratios
            # > List background color (when not over & over)
            # > List border color (when not over & over)
            # > List item text color (when not over & over)
            # > List item text font scale (when not over & over)
            # > List item text thickness (when not over & over)
            # > List item background color (when not over & over)
            # > List item border color (when not over & over)
            # > List item border thickness (when not over & over)            
            list_background_color = self.list_render_configs['list_background_color'][0 if not self.is_mouse_over else 1]
            list_border_color = self.list_render_configs['list_border_color'][0 if not self.is_mouse_over else 1]
            list_border_thickness = self.list_render_configs['list_border_thickness'][0 if not self.is_mouse_over else 1]           

            # Draw list background
            cv2.rectangle(frame, (list_x, list_y), (list_x+list_width, list_y+list_height), list_background_color, -1)
            # Draw scroll bar

            padding = int(self.list_render_configs['padding_n']*self.size_n[0]*frame.shape[1])
            scroller_width = int(self.list_render_configs['scroll_bar_width_n']*self.size_n[0]*frame.shape[1])
            scroller_y_offset = int(self.list_render_configs['arrow_icon_height_n']*self.size_n[1]*frame.shape[0])

            bar_background_height = int(list_height - 2*scroller_y_offset)
            cv2.rectangle(frame, (list_x+ list_width+padding, list_y+scroller_y_offset), (list_x+list_width+padding+scroller_width, list_y+scroller_y_offset+bar_background_height), (225,225,225), -1)

            scroller_height = bar_background_height*(self.list_render_configs["item_per_page"]/max(len(self.all_list_items), self.list_render_configs["item_per_page"]))
            scroller_y0 = list_y + scroller_y_offset + (self.first_data_index_to_display/max(1,len(self.all_list_items)))*bar_background_height
            scroller_y1 = min( scroller_y0 + scroller_height, list_y+list_height-scroller_y_offset)            
            cv2.rectangle(frame, (list_x+ list_width+ padding, int(scroller_y0)), (list_x+list_width+ padding + scroller_width, int(scroller_y1)), (169, 96, 0), -1)
            
            picasso.draw_image_on_frame(frame=frame, image_name='arrow_up_icon', x=list_x+list_width+padding, y=list_y, width=scroller_width, height=scroller_y_offset, maintain_aspect_ratio=False)
            picasso.draw_image_on_frame(frame=frame, image_name='arrow_down_icon', x=list_x+list_width+padding, y=list_y+list_height-scroller_y_offset, width=scroller_width, height=scroller_y_offset, maintain_aspect_ratio=False)

            # Draw list items
            item_height = (list_height)//self.list_render_configs["item_per_page"]
            padding = int(self.list_render_configs["padding_precentage_per_item"]*item_height)
            item_topleft = (list_x, list_y)
            for i, item in enumerate(items_to_display):
                item_topleft_x = item_topleft[0]
                item_topleft_y = item_topleft[1]+i*item_height

                list_item_background_color = self.list_render_configs['list_item_background_color'][0 if not item["is_over"] else 1]
                list_item_text_color = self.list_render_configs['list_item_text_color'][0 if not item["is_over"] else 1]
                list_item_text_font_scale = self.list_render_configs['list_item_text_font_scale'][0 if not item["is_over"] else 1]
                list_item_text_thickness = self.list_render_configs['list_item_text_thickness'][0 if not item["is_over"] else 1]
                list_item_border_color = self.list_render_configs['list_item_border_color'][0 if not item["is_over"] else 1]
                list_item_border_thickness = self.list_render_configs['list_item_border_thickness'][0 if not item["is_over"] else 1]
                list_item_text_font_scale = self.list_render_configs['list_item_text_font_scale'][0 if not item["is_over"] else 1]

                for column_no, column_width in enumerate(colum_slicing_ratios):
                    cell_topleft_x = item_topleft_x+ sum(colum_widths[:column_no])
                    cell_topleft_y = item_topleft_y
                    cell_width = colum_widths[column_no]
                    cell_height = item_height
                    cv2.rectangle(frame, (cell_topleft_x, cell_topleft_y), (cell_topleft_x+cell_width, cell_topleft_y+cell_height), list_item_background_color, -1)
                    cv2.rectangle(frame, (cell_topleft_x, cell_topleft_y), (cell_topleft_x+cell_width, cell_topleft_y+cell_height), list_item_border_color, list_item_border_thickness)
                    cv2.line(frame, (cell_topleft_x+cell_width, cell_topleft_y), (cell_topleft_x+cell_width, cell_topleft_y+cell_height), list_item_border_color, list_item_border_thickness)
                    picasso.draw_text_on_frame(frame=frame, alignment='center', text = item[f"COLUMN_{column_no}"], position=(cell_topleft_x, cell_topleft_y), area_size = (cell_width, cell_height), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=list_item_text_font_scale, text_color=list_item_text_color, thickness=list_item_text_thickness, padding=10)

                    # cv2.rectangle(frame, (list_x, list_y+i*item_height), (list_x+colum_widths[column_no], list_y+(i+1)*item_height), list_item_background_color, -1)
                    # cv2.rectangle(frame, (list_x, list_y+i*item_height), (list_x+list_width, list_y+(i+1)*item_height), list_item_border_color, list_item_border_thickness)
                    # cv2.line(frame, (list_x+colum_widths[column_no], list_y+i*item_height), (list_x+colum_widths[column_no], list_y+(i+1)*item_height), list_item_border_color, list_item_border_thickness)
                    # picasso.draw_text_on_frame(frame=frame, alignment='center', text = item[f"COLUMN_{column_no}"], position=(list_x, list_y+i*list_height//self.list_render_configs["item_per_page"]), area_size = (list_width, list_height//self.list_render_configs["item_per_page"]), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=list_item_text_font_scale, text_color=list_item_text_color, thickness=list_item_text_thickness, padding=10)

class ClickEventArea():
    def __init__(self, identifier:str = "default-id", pos_n:Tuple[float, float] = None, size_n:Tuple[float, float] = None, click_event_area_render_configs:dict = None):
        self.identifier = identifier
        self.pos_n = pos_n
        self.size_n = size_n
        self.click_event_area_render_configs = click_event_area_render_configs
        self.is_mouse_over = False

    def is_focusable(self):
        return False
    
    def is_clickable(self):
        return True
    
    def is_writeable(self):
        return False
    
    def release_focus(self):
        self.is_focused = False

    def get_reset_page_frame_required_callbacks(self):
        return []
    
    def get_redraw_required_callbacks(self):
        return []
    
    def is_left_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            normalized_click = ((click_n[0]-self.pos_n[0])/self.size_n[0], (click_n[1]-self.pos_n[1])/self.size_n[1])
            return ["left_clicked_callback", self.identifier, True, normalized_click]
        else:
            return ["left_clicked_callback", self.identifier, False]
        
    def is_right_clicked_callback(self, click_n:Tuple[float, float]):
        if self.pos_n[0] < click_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < click_n[1] < self.pos_n[1] + self.size_n[1]:
            normalized_click = ((click_n[0]-self.pos_n[0])/self.size_n[0], (click_n[1]-self.pos_n[1])/self.size_n[1])
            return ["right_clicked_callback", self.identifier, True, normalized_click]
        else:
            return ["right_clicked_callback", self.identifier, False]
        
    def is_mouse_over_callback(self, mouse_n:Tuple[float, float]):
        if self.pos_n[0] < mouse_n[0] < self.pos_n[0] + self.size_n[0] and self.pos_n[1] < mouse_n[1] < self.pos_n[1] + self.size_n[1]:
            self.is_mouse_over = True
            return ["mouse_over_callback", self.identifier, True]
        else:
            self.is_mouse_over = False
            return ["mouse_over_callback", self.identifier, False]
        
    def draw(self, frame:np.ndarray=None):
        pass
        
