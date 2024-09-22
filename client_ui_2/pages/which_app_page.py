import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid
import PREFERENCES

class WhichAppPage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="which_app_page_template", default_resolution=(1920,1080))
        self.page_frame = None 
        self.user_authorizations = self.api_dealer.get_authorizations()[2]

        self.app_list_item = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.110, 0.25),
            size_n=(0.275, 0.5),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":6, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[1],
                "list_background_color": [(225, 225, 225), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [1.1, 1.1],
                "list_item_text_thickness": [2, 2],
                "list_item_text_color": [(169, 96, 0), (255, 255, 255)],
                "list_item_background_color": [(225, 225, 225), (169, 96, 0)],
                "list_item_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_item_border_thickness": [2, 2],
                "padding_n" : 0.01,
                "scroll_bar_width_n": 0.05,
                "arrow_icon_height_n": 0.1,
            }
        )
        authorized_apps = [ {"COLUMN_0": app['authorization_name']} for app in self.user_authorizations if app['authorization_name'] in PREFERENCES.APPLICATION_AUTHORIZATIONS]
        self.app_list_item.set_list_items(items = authorized_apps)

        self.previous_page_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.110, 0.76),
            size_n=(0.275, 0.05),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Geri",
                "button_text_font_scale": [1, 1],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.app_list_item, self.previous_page_button]
       
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
            if callback == ["left_clicked_callback", self.previous_page_button.identifier, True]:
                program_state[0] = 0
                return
            
            elif callback[0]  == "item_clicked_callback" and callback[1] == self.app_list_item.identifier:                
                clicked_app = self.app_list_item.get_list_item_info(callback[3])['COLUMN_0']
                if clicked_app == 'UPDATE_CAMERAS':
                    program_state[0] = 3
                    return
                elif clicked_app == 'ISG_UI':
                    program_state[0] = 4
                    return
                elif clicked_app == "EDIT_RULES":
                    program_state[0] = 5
                    return
                elif clicked_app == "REPORTED_VIOLATIONS":
                    program_state[0] = 6
                    return
                
          

        


                                        