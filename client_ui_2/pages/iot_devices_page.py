import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, datetime,base64, numpy as np

class IoTDevicesPage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="iot_devices_page_template", default_resolution=(1920,1080))
        self.page_frame = None 
        self.fetched_violations = None
        self.last_shown_violation_frame_info = None
        
        self.iot_devices_rows_list = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.04, 0.19),
            size_n=(0.91, 0.74),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":12, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[1,0.6,2], # Device Name, Device ID, Device UUID
                "list_background_color": [(240, 240, 240), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [0.8, 0.8],
                "list_item_text_thickness": [2,2],
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

        self.create_iot_device_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.850, 0.057),
            size_n=(0.075, 0.036),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Cihaz Ekle",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )
        
        self.device_name_input = ui_items.TextInput(
            identifier = "start_date_input_"+str(uuid.uuid4()),
            pos_n=(0.286, 0.057),
            size_n=(0.145, 0.036),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Cihaz Adı",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale":[0.75, 0.75],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.device_id_input = ui_items.TextInput(
            identifier = "end_date_input_"+str(uuid.uuid4()),
            pos_n=(0.494, 0.057),
            size_n=(0.200, 0.036),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Cihaz ID",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [0.75, 0.75],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.iot_devices_rows_list, self.previous_page_button, self.device_name_input, self.device_id_input
                              , self.create_iot_device_button]
       
        self.reset_page_frame_required_callbacks = []
        for item in self.page_ui_items:
            self.reset_page_frame_required_callbacks.extend(item.get_reset_page_frame_required_callbacks())
        
        self.iot_device_rows = [] #device name, device id, device_uuid
        self.update_current_iot_devices()

        # ==========================
        self.reset_page_frame()

    def update_current_iot_devices(self):
        #fetch all iot devices
        fetch_iot_devices_result = self.api_dealer.fetch_all_iot_devices()
        if not fetch_iot_devices_result[0]:
            print("Error fetching iot devices:", fetch_iot_devices_result[1])
            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":fetch_iot_devices_result[1]})
            return
        iot_devices = fetch_iot_devices_result[2]
        self.user_authorization_rows = []
        for iot_device in iot_devices:
            self.user_authorization_rows.append({
                "COLUMN_0": iot_device['device_name'],
                "COLUMN_1": iot_device['device_id'],
                "COLUMN_2": iot_device['device_uuid']
            })
        
        self.iot_devices_rows_list.set_list_items(items = self.user_authorization_rows)        

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
            elif callback == ["left_clicked_callback", self.create_iot_device_button.identifier, True]:   
                # create iot device
                device_name = self.device_name_input.get_text()
                device_id = self.device_id_input.get_text()
                result = self.api_dealer.create_iot_device(device_name = device_name, device_id = device_id)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Cihaz başarıyla eklendi."})
                    self.update_current_iot_devices()
                    self.reset_page_frame()
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})

            elif callback[0] == "item_clicked_callback" and callback[1] == self.iot_devices_rows_list.identifier:
                # remove iot device
                selected_index = callback[3]
                clicked_row = self.user_authorization_rows[selected_index]

                device_uuid = clicked_row["COLUMN_2"]
                result = self.api_dealer.delete_iot_device(device_uuid = device_uuid)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Cihaz başarıyla silindi."})
                    self.update_current_iot_devices()
                    self.reset_page_frame()
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})
        
             
    
        


                                        