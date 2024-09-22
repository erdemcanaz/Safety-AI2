import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time

class LoginPage:    
    def __init__(self, api_dealer:object,  popup_dealer:object = None,):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="login_page_template", default_resolution=(1920,1080))
        self.page_frame = None 

        # Create UI items
        self.username_textinput = ui_items.TextInput(
            identifier = "username_textinput",
            pos_n=(0.125, 0.4),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Kullanıcı Adı",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.password_textinput = ui_items.PasswordTextInput(
            identifier = "password_textinput",
            pos_n=(0.125, 0.46),
            size_n=(0.275, 0.05),
            show_icon_percentage = 0.2,
            password_text_input_render_configs={   
                "password_text_input_style": "basic",     
                "password_text_input_default_text": "Şifre",
                "password_text_input_default_text_color": (200, 200, 200),
                "password_text_input_text_font_scale": [1.1, 1.1],
                "password_text_input_text_thickness": [2, 2],
                "password_text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "password_text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "password_text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "password_text_input_border_thickness": [2, 2]
            }
        )

        self.login_button = ui_items.Button(
            identifier = "login_button",
            pos_n=(0.125, 0.625),
            size_n=(0.275, 0.05),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Giriş Yap",
                "button_text_font_scale": [1, 1],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.open_register_page_button = ui_items.Button(
            identifier = "open_register_page_button",
            pos_n=(0.125, 0.685),
            size_n=(0.275, 0.05),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Kayıt Ol",
                "button_text_font_scale": [1, 1],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.username_textinput, self.password_textinput, self.login_button, self.open_register_page_button]

        self.reset_page_frame_required_callbacks = []
        for item in self.page_ui_items:
            self.reset_page_frame_required_callbacks.extend(item.get_reset_page_frame_required_callbacks())
        
        # ========================== #
        self.reset_page_frame()

    def reset_page_frame(self):
        self.page_frame = self.background.get_background_frame()
        for ui_item in self.page_ui_items:
            ui_item.draw(self.page_frame)
        
    def get_ui_items(self):
        return self.page_ui_items
    
    def get_page_frame(self):
        return self.page_frame
    
    def apply_callbacks(self, redraw_items:bool = False, program_state:List=[1,0,0], callback_results:List=[], released_focus_identifiers:List=[]):
        # Update the page frame ========================================
        for result in callback_results:
            if result in self.reset_page_frame_required_callbacks:
                self.reset_page_frame()    
                break    
        else: # If no reset required, apply other callbacks              
            for item in self.page_ui_items:             
                for callback in item.get_redraw_required_callbacks():
                    if redraw_items or callback in callback_results or item.identifier in released_focus_identifiers:
                        item.draw(self.page_frame)
                        break

        # Apply the callbacks ==========================================
        for callback in callback_results:
            if callback == ["left_clicked_callback", self.login_button.identifier, True]:
                username = self.username_textinput.get_text()
                password = self.password_textinput.get_text()     
                result = self.api_dealer.get_access_token(username=username, plain_password=password)
                #[True/False, response.status_code, response.json()]
                if result[0]:
                    program_state[0] = 2 # Go to the which app page
                    self.popup_dealer.append_popup(
                        {
                            "background_color": (0, 255, 0),
                            "created_at": time.time(),
                            "duration": 2,
                            "text": "Giriş Yapıldı"
                        }
                    )             
                else:
                    self.popup_dealer.append_popup(
                        {
                            "background_color": (0, 0, 255),
                            "created_at": time.time(),
                            "duration": 3,
                            "text": str(result[2]["detail"])
                        }
                    )                                  

            elif callback == ["left_clicked_callback", self.open_register_page_button.identifier, True]:
                program_state[0] = 1
                return

        


                                            


    

        