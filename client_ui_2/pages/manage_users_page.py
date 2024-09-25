import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, datetime,base64, numpy as np

class ManageUsersPage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="manage_users_page_template", default_resolution=(1920,1080))
        self.page_frame = None 
        self.fetched_violations = None
        self.last_shown_violation_frame_info = None
        
        self.authorization_rows_list = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.04, 0.19),
            size_n=(0.91, 0.74),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":25, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[0.6,0.6,1.25,0.6,1.25], # 'username', 'personal_fullname', 'user_uuid', 'authorization_name', 'authorization_uuid'
                "list_background_color": [(240, 240, 240), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [0.6, 0.6],
                "list_item_text_thickness": [1,1],
                "list_item_text_color": [(169, 96, 0), (255, 255, 255)],
                "list_item_background_color": [(238, 236, 125), (169, 96, 0)],
                "list_item_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_item_border_thickness": [2, 2],
                "padding_n" : 0.005,
                "scroll_bar_width_n": 0.01,
                "arrow_icon_height_n": 0.04,
            }
        )

        self.previous_page_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.04, 0.94),
            size_n=(0.075, 0.036),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Geri",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.create_authorization_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.850, 0.057),
            size_n=(0.075, 0.036),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Yetki Ekle",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )
        
        self.username_input = ui_items.TextInput(
            identifier = "start_date_input_"+str(uuid.uuid4()),
            pos_n=(0.289, 0.057),
            size_n=(0.100, 0.036),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Kullanici Adı",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale":[0.75, 0.75],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.authorization_name_input = ui_items.TextInput(
            identifier = "end_date_input_"+str(uuid.uuid4()),
            pos_n=(0.494, 0.057),
            size_n=(0.100, 0.036),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Yetki Adı",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [0.75, 0.75],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.authorization_rows_list, self.previous_page_button, self.username_input, self.authorization_name_input
                              , self.create_authorization_button]
       
        self.reset_page_frame_required_callbacks = []
        for item in self.page_ui_items:
            self.reset_page_frame_required_callbacks.extend(item.get_reset_page_frame_required_callbacks())
        
        self.user_authorization_rows = [] # username, personal_fullname, user_uuid, authorization_name, authorization_uuid
        self.update_current_users_and_authorizations()
        #fetch all users

        #fetch all user authorizations
        # ========================== #
        self.reset_page_frame()

    def update_current_users_and_authorizations(self):
        #fetch all users
        fetch_users_result = self.api_dealer.get_all_users()        
        if not fetch_users_result[0]:
            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":fetch_users_result[1]})
            return
        users = [] 

        for user in fetch_users_result[2]:
            users.append({'personal_fullname': user['personal_fullname'], "username": user['username'], "user_uuid": user['user_uuid']})

        #all authorizations
        fetch_authorizations_result = self.api_dealer.fetch_all_authorizations()

        if not fetch_authorizations_result[0]:
            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":fetch_authorizations_result[1]})
            return
        authorizations = []
        for authorization in fetch_authorizations_result[2]:
            authorizations.append({'user_uuid':authorization['user_uuid'], "authorization_name": authorization['authorization_name'], "authorization_uuid": authorization['authorization_uuid']})

        #match each user with their authorizations
        self.user_authorization_rows = [] # username, personal_fullname, user_uuid, authorization_name, authorization_uuid
        for user in users:
            # Create a mock authorization so that the user is shown in the list even if they have no authorizations
            self.user_authorization_rows.append({
                "COLUMN_0": user['username'],
                "COLUMN_1": user['personal_fullname'],
                "COLUMN_2": user['user_uuid'],
                "COLUMN_3": "USER_EXISTS",
                "COLUMN_4": "NO_UUID",
            })

            pprint.pprint(user)
            for authorization in authorizations:
                if authorization['user_uuid'] != user['user_uuid']:
                    continue
                
                self.user_authorization_rows.append({
                    "COLUMN_0": user['username'],
                    "COLUMN_1": user['personal_fullname'],
                    "COLUMN_2": user['user_uuid'],
                    "COLUMN_3": authorization['authorization_name'],
                    "COLUMN_4": authorization['authorization_uuid'],
                })

        self.authorization_rows_list.set_list_items(items = self.user_authorization_rows)

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
            if callback == ["left_clicked_callback", self.previous_page_button.identifier, True]:
                program_state[0] = 2
                return
            elif callback == ["left_clicked_callback", self.create_authorization_button.identifier, True]:   
                username = self.username_input.get_text()
                authorization_name = self.authorization_name_input.get_text()
                result = self.api_dealer.add_authorization(username = username, authorization_name = authorization_name )
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Yetkilendirme başarıyla eklendi."})
                    self.update_current_users_and_authorizations()
                    self.reset_page_frame()
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})

            elif callback[0] == "item_clicked_callback" and callback[1] == self.authorization_rows_list.identifier:
                #delete corresponding authorization
                selected_index = callback[3]
                clicked_row = self.user_authorization_rows[selected_index]

                authorization_uuid = clicked_row["COLUMN_4"]
                result = self.api_dealer.remove_authorization_by_uuid(authorization_uuid = authorization_uuid)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Yetkilendirme başarıyla silindi."})
                    self.update_current_users_and_authorizations()
                    self.reset_page_frame()
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})
        
             
    
        


                                        