import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, base64
import numpy as np

class UpdateCamerasPage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="update_cameras_page_template", default_resolution=(1920,1080))
        self.page_frame = None 
        self.last_camera_frame_info:dict = None #  camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected, last_frame_b64, decoded_last_frame

        self.cameras_list_item = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.035, 0.15),
            size_n=(0.200, 0.70),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":15, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[1],
                "list_background_color": [(225, 225, 225), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [1.1, 1.1],
                "list_item_text_thickness": [2, 2],
                "list_item_text_color": [(169, 96, 0), (255, 255, 255)],
                "list_item_background_color": [(238, 236, 125), (169, 96, 0)],
                "list_item_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_item_border_thickness": [2, 2],
                "padding_n" : 0.02,
                "scroll_bar_width_n": 0.05,
                "arrow_icon_height_n": 0.05,
            }
        )

        self.camera_info = self.api_dealer.fetch_all_camera_info()[2] 
        self.cameras = [ {"COLUMN_0": camera['camera_ip_address'] if camera['camera_region'] == "" else camera['camera_region'], "camera_info":camera} for camera in self.camera_info]
        self.cameras_list_item.set_list_items(items = self.cameras)

        self.previous_page_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.035, 0.86),
            size_n=(0.200, 0.05),
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

        self.clear_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.3, 0.9),
            size_n=(0.075, 0.030),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Temizle",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.update_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.38, 0.9),
            size_n=(0.075, 0.030),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Güncelle",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.create_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.46, 0.9),
            size_n=(0.075, 0.030),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Ekle",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.get_sample_image_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.54, 0.9),
            size_n=(0.075, 0.030),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Görüntü İste",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.delete_camera_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.62, 0.9),
            size_n=(0.075, 0.030),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Sil",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(167, 146, 255), (0, 0, 255)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.UUID_text_field = ui_items.TextField(
            identifier="text_field_"+str(uuid.uuid4()),
            pos_n=(0.3, 0.69),
            size_n=(0.275, 0.05),
            text_field_render_configs={   
                "text_field_style": "basic",   
                "text_field_default_text": "Kamera UUID", 
                "text_field_default_text_color": (200, 200, 200),
                "text_field_text_font_scale": [0.75, 0.75],
                "text_field_text_thickness": [2, 2],
                "text_field_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_field_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_field_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_field_border_thickness": [2, 2]
            }
        )

        self.IPV4_input = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),
            pos_n=(0.3, 0.75),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "IPv4",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.region_name = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),
            pos_n=(0.3, 0.81),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Bolge Adı",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.username_input = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),

            pos_n=(0.580, 0.69),
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

        self.password_input = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),

            pos_n=(0.580, 0.75),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Şifre",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.is_active_input = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),

            pos_n=(0.580, 0.81),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "active/inactive",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.cameras_list_item, self.previous_page_button , self.clear_button, self.update_button, self.create_button, self.get_sample_image_button,
                             self.region_name, self.UUID_text_field, self.IPV4_input, self.username_input, self.password_input, self.is_active_input, self.delete_camera_button]
                              
       
        self.reset_page_frame_required_callbacks = []
        for item in self.page_ui_items:
            self.reset_page_frame_required_callbacks.extend(item.get_reset_page_frame_required_callbacks())
        
        # ========================== #
        self.reset_page_frame()

    def reset_page_frame(self):
        self.page_frame = self.background.get_background_frame()
        
        self.camera_info = self.api_dealer.fetch_all_camera_info()[2]
        self.cameras = [ {"COLUMN_0": camera['camera_ip_address'] if camera['camera_region'] == "" else camera['camera_region'], "camera_info":camera} for camera in self.camera_info]
        self.cameras_list_item.set_list_items(items = self.cameras)

        # draw last frame 
        if self.last_camera_frame_info is not None and self.last_camera_frame_info["camera_uuid"] == self.UUID_text_field.get_text():
            picasso.draw_frame_on_frame(self.page_frame, self.last_camera_frame_info['decoded_last_frame'], x=607, y=92, width=1086, height=590, maintain_aspect_ratio=False)
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
            if callback[0] != "mouse_over_callback":
                print(callback)

            if callback == ["left_clicked_callback", self.previous_page_button.identifier, True]:
                program_state[0] = 2
                return
            elif callback == ["left_clicked_callback", self.clear_button.identifier, True]:
                self.UUID_text_field.set_text("")
                self.IPV4_input.set_text("")
                self.region_name.set_text("")
                self.username_input.set_text("")
                self.password_input.set_text("")
                self.is_active_input.set_text("")
                self.reset_page_frame()
                return
            elif callback == ["left_clicked_callback", self.create_button.identifier, True]:
                camera_ip_address = self.IPV4_input.get_text()
                camera_region = self.region_name.get_text()
                username = self.username_input.get_text()
                password = self.password_input.get_text()
                camera_status = self.is_active_input.get_text()
                result = self.api_dealer.create_camera_info(camera_ip_address=camera_ip_address, username=username, password=password, camera_region=camera_region if camera_region != "" else "", camera_status=camera_status)
                
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":3, "text":"Kamera eklendi"})
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":3, "text":result[1]})
                self.reset_page_frame()
                return
            elif callback == ["left_clicked_callback", self.update_button.identifier, True]:
                camera_uuid = self.UUID_text_field.get_text()
                attibutes = {
                    'camera_ip_address': self.IPV4_input.get_text(),
                    'camera_region': self.region_name.get_text(),
                    'username': self.username_input.get_text(),
                    'password': self.password_input.get_text(),
                    'camera_status': self.is_active_input.get_text()
                }               
                
                for attribute, value in attibutes.items():
                    result = self.api_dealer.update_camera_info_attribute(camera_uuid = camera_uuid, attribute=attribute, value=value)
                    if result[0]:
                        self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":f"{attribute} güncellendi"})
                    else:
                        self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})
                self.reset_page_frame()
            elif callback == ["left_clicked_callback", self.get_sample_image_button.identifier, True]:
                camera_uuid = self.UUID_text_field.get_text()
                result = self.api_dealer.get_last_camera_frame_by_camera_uuid(camera_uuid=camera_uuid)
                if result[0]:
                    self.last_camera_frame_info = result[2]["last_frame_info"]
                    if self.last_camera_frame_info is None:
                        self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":"Henüz kamera görüntüsü yüklenmemiş"})
                    else:
                        self.last_camera_frame_info['decoded_last_frame'] =  cv2.imdecode(np.frombuffer(base64.b64decode(self.last_camera_frame_info['last_frame_b64']),np.uint8), cv2.IMREAD_COLOR)
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})
                self.reset_page_frame()
                return
            elif callback == ["left_clicked_callback", self.delete_camera_button.identifier, True]:
                camera_uuid = self.UUID_text_field.get_text()
                result = self.api_dealer.delete_camera_info_by_uuid(camera_uuid=camera_uuid)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Kamera silindi"})
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})
                self.reset_page_frame()
                return
            elif callback[0] == "item_clicked_callback" and callback[1] == self.cameras_list_item.identifier:
                selected_index = callback[3]
                self.UUID_text_field.set_text(self.cameras[selected_index]["camera_info"]['camera_uuid'])
                self.IPV4_input.set_text(self.cameras[selected_index]["camera_info"]['camera_ip_address'])
                self.region_name.set_text(self.cameras[selected_index]["camera_info"]['camera_region'])
                self.username_input.set_text(self.cameras[selected_index]["camera_info"]['username'])
                self.password_input.set_text(self.cameras[selected_index]["camera_info"]['password'])
                self.is_active_input.set_text(self.cameras[selected_index]["camera_info"]['camera_status'])

                camera_uuid = self.UUID_text_field.get_text()
                result = self.api_dealer.get_last_camera_frame_by_camera_uuid(camera_uuid=camera_uuid)
                if result[0]:
                    self.last_camera_frame_info = result[2]["last_frame_info"]
                    if self.last_camera_frame_info is None:
                        self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":"Henüz kamera görüntüsü yüklenmemiş"})
                    else:
                        self.last_camera_frame_info['decoded_last_frame'] =  cv2.imdecode(np.frombuffer(base64.b64decode(self.last_camera_frame_info['last_frame_b64']),np.uint8), cv2.IMREAD_COLOR)
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})

                self.reset_page_frame()

                return

            


        


                                        