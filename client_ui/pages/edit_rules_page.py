import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, base64
import numpy as np

class EditRulesPage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="edit_rules_page_template", default_resolution=(1920,1080))
        self.page_frame = None 
        
        self.all_camera_info_list = None # [{'username':'sdsa', 'password':'sdfsf', date_created': '2024-08-26 08:44:56', 'date_updated': '2024-08-26 08:44:56', 'camera_uuid': '92051d28-3402-46cd-952b-d2ba2782443e', 'camera_ip_address': '1.1.1.1', 'camera_region': 'Henüz Atanmadı', 'camera_description': 'Henüz Atanmadı', 'NVR_ip_address': '', 'stream_path': '/asdaf', 'camera_status': 'active'}, ...]
        
        self.selected_camera_info:dict = None # username, password, date_created, date_updated, camera_uuid, camera_ip_address, camera_region, camera_description, NVR_ip_address, stream_path, camera_status
        self.selected_camera_last_frame_info:dict = None #  camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected, last_frame_b64, decoded_last_frame
        self.frame_position = (1175, 278, 677, 682) # x,y,w,h
        self.selected_camera_rules_info = None
        self.selected_camera_active_rule_polygons = None # list[ list[ (x1n,y1n), ..] , ...]   
        self.new_rule_polygon = [] # list[ (x1n,y1n), ..]

        self.polygon_click_area = ui_items.ClickEventArea(
            identifier = "click_event_area_"+str(uuid.uuid4()),
            pos_n=(0.61197, 0.2574),
            size_n=(0.3526, 0.63148),
            click_event_area_render_configs={
                "click_event_area_style": "basic",
                "click_event_area_background_color": (0, 0, 0, 0),
                "click_event_area_border_color": (0, 0, 0, 0),
                "click_event_area_border_thickness": 0
            }
        )
        
        self.cameras_list_item = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.035, 0.15),
            size_n=(0.175, 0.70),
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

        self.rules_list_item = ui_items.BasicList(
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.25, 0.22),
            size_n=(0.32, 0.16),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":4, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[1,2,1,0.5],
                "list_background_color": [(225, 225, 225), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [0.5, 0.5],
                "list_item_text_thickness": [2, 2],
                "list_item_text_color": [(169, 96, 0), (255, 255, 255)],
                "list_item_background_color": [(238, 236, 125), (169, 96, 0)],
                "list_item_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_item_border_thickness": [2, 2],
                "padding_n" : 0.005,
                "scroll_bar_width_n": 0.03,
                "arrow_icon_height_n": 0.2,
            }
        )

        self.previous_page_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.035, 0.86),
            size_n=(0.175, 0.05),
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
            pos_n=(0.26, 0.83),
            size_n=(0.15, 0.04),
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

        self.create_button = ui_items.Button(
            identifier = "button_"+str(uuid.uuid4()),
            pos_n=(0.42, 0.83),
            size_n=(0.15, 0.04),
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
            pos_n=(0.71, 0.91),
            size_n=(0.15, 0.04),
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

        self.rule_department = ui_items.TextInput(
            identifier = "Kural Departmanı"+str(uuid.uuid4()),
            pos_n=(0.29, 0.50),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Kural Departmanı",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.rule_type = ui_items.TextInput(
            identifier = "Kural Çeşidi"+str(uuid.uuid4()),
            pos_n=(0.29, 0.56),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Kural Çeşidi",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.evaluation_method = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),

            pos_n=(0.29, 0.62),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Değerlendirme Yöntemi",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.threshold_value = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),

            pos_n=(0.29, 0.68),
            size_n=(0.275, 0.05),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Eşik Değeri",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [1.1, 1.1],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.polygon_click_area, self.cameras_list_item, self.rules_list_item, self.previous_page_button , self.clear_button, self.create_button, self.get_sample_image_button,
                              self.rule_department, self.rule_type, self.evaluation_method, self.threshold_value]
                              
        self.reset_page_frame_required_callbacks = []
        for item in self.page_ui_items:
            self.reset_page_frame_required_callbacks.extend(item.get_reset_page_frame_required_callbacks())
        
        # ========================== #
        self.reset_page_frame()

    def reset_page_frame(self):
        self.page_frame = self.background.get_background_frame()
        
        self.all_camera_info_list = self.api_dealer.fetch_all_camera_info()[2]['camera_info'] 
        formatted_cameras_for_list = [ {"COLUMN_0": camera['camera_ip_address'] if camera['camera_region'] == "" else camera['camera_region'], "camera_info":camera} for camera in self.all_camera_info_list]
        self.cameras_list_item.set_list_items(items = formatted_cameras_for_list)

        if self.selected_camera_info is not None:
            formatted_rules_for_list = [ {"COLUMN_0": rule['rule_department'], "COLUMN_1": rule['rule_type'], "COLUMN_2": rule['evaluation_method'], "COLUMN_3": str(rule['threshold_value']), "rule_info":rule} for rule in self.selected_camera_rules_info]
            self.rules_list_item.set_list_items(items = formatted_rules_for_list)

        # draw last frame 
        if self.selected_camera_last_frame_info is not None and self.selected_camera_last_frame_info["camera_uuid"] == self.selected_camera_info["camera_uuid"]:
            picasso.draw_frame_on_frame(self.page_frame, self.selected_camera_last_frame_info['decoded_last_frame'], x=self.frame_position[0], y=self.frame_position[1], width=self.frame_position[2], height=self.frame_position[3], maintain_aspect_ratio=False)

        # draw polygons
        #draw_polygon_on_frame( frame: np.ndarray = None, points: list = None, color: tuple = (0, 0, 255), thickness: int = 2, last_dot_color: tuple = (255, 0, 0), first_last_line_color: tuple = (0, 255, 0)):
        pixel_coordinates = [ [int(self.frame_position[0] + point[0]*self.frame_position[2]), int(self.frame_position[1] + point[1]*self.frame_position[3])] for point in self.new_rule_polygon]
        picasso.draw_polygon_on_frame(frame = self.page_frame, points = pixel_coordinates, color=(0, 0, 255), thickness=2, last_dot_color=(255, 0, 0), first_last_line_color=(0, 255, 0))
        
        # draw items
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
            elif callback == ["left_clicked_callback", self.clear_button.identifier, True]:
                self.rule_department.set_text("")
                self.rule_type.set_text("")
                self.evaluation_method.set_text("")
                self.threshold_value.set_text("")
                self.new_rule_polygon = []
                self.reset_page_frame()
                return
            elif callback == ["left_clicked_callback", self.create_button.identifier, True]:
                if self.selected_camera_info is None: return
                camera_uuid = self.selected_camera_info["camera_uuid"]
                rule_department = self.rule_department.get_text()
                rule_type = self.rule_type.get_text()
                evaluation_method = self.evaluation_method.get_text()
                threshold_value = self.threshold_value.get_text()
                rule_polygon = ",".join([str(point) for point in [item for sublist in self.new_rule_polygon for item in sublist]])
                result = self.api_dealer.create_rule_for_camera(camera_uuid=camera_uuid, rule_department=rule_department, rule_type=rule_type, evaluation_method=evaluation_method, threshold_value=float(threshold_value), rule_polygon=rule_polygon)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Kural eklendi"})
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})
                self.reset_page_frame()
                return
            elif callback == ["left_clicked_callback", self.get_sample_image_button.identifier, True]:
                if self.selected_camera_info is None: return
                camera_uuid = self.selected_camera_info["camera_uuid"]
                result = self.api_dealer.get_last_camera_frame_by_camera_uuid(camera_uuid=camera_uuid)
                if result[0]:
                    self.selected_camera_last_frame_info = result[2]["last_frame_info"]
                    if self.selected_camera_last_frame_info is None:
                        self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":"Henüz kamera görüntüsü yüklenmemiş"})
                    else:
                        self.selected_camera_last_frame_info['decoded_last_frame'] =  cv2.imdecode(np.frombuffer(base64.b64decode(self.selected_camera_last_frame_info['last_frame_b64']),np.uint8), cv2.IMREAD_COLOR)
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})
                self.reset_page_frame()
                return
            
            elif callback[0] == 'left_clicked_callback' and self.polygon_click_area.identifier == callback[1]:
                xn = round(callback[3][0],3)
                yn = round(callback[3][1],3)
                self.new_rule_polygon.append([xn, yn])
                # draw last frame 
                self.reset_page_frame()
            
            elif callback[0] == "item_clicked_callback" and callback[1] == self.cameras_list_item.identifier:
                self.new_rule_polygon = []
                selected_index = callback[3]
                self.selected_camera_info = self.all_camera_info_list[selected_index]
                result = self.api_dealer.fetch_rules_by_camera_uuid(camera_uuid=self.selected_camera_info['camera_uuid'])
                if result[2] is None:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":"Kamera için kural(lar) bulunamadı"})
                else:
                    self.selected_camera_rules_info = result[2]["rules"]                    
                    self.selected_camera_active_rule_polygons = []
                    for rule in self.selected_camera_rules_info:
                        parsed_rule = rule['rule_polygon'].split(",")
                        rule_polygon = [ [float(parsed_rule[i]), float(parsed_rule[i+1])] for i in range(0,len(parsed_rule),2)]
                        self.selected_camera_active_rule_polygons.append(rule["rule_polygon"])
                
                if self.selected_camera_info is not None:
                    camera_uuid = self.selected_camera_info["camera_uuid"]
                    result = self.api_dealer.get_last_camera_frame_by_camera_uuid(camera_uuid=camera_uuid)
                    if result[0]:
                        self.selected_camera_last_frame_info = result[2]["last_frame_info"]
                        if self.selected_camera_last_frame_info is None:
                            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":"Henüz kamera görüntüsü yüklenmemiş"})
                        else:
                            self.selected_camera_last_frame_info['decoded_last_frame'] =  cv2.imdecode(np.frombuffer(base64.b64decode(self.selected_camera_last_frame_info['last_frame_b64']),np.uint8), cv2.IMREAD_COLOR)
                    else:
                        self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})
                
                self.reset_page_frame()
                return
            elif callback[0] == "item_clicked_callback" and callback[1] == self.rules_list_item.identifier:
                selected_index = callback[3]
                selected_rule_info = self.selected_camera_rules_info[selected_index]
                self.rule_department.set_text(selected_rule_info["rule_department"])
                self.rule_type.set_text(selected_rule_info["rule_type"])
                self.evaluation_method.set_text(selected_rule_info["evaluation_method"])
                self.threshold_value.set_text(str(selected_rule_info["threshold_value"]))
                parsed_rule = selected_rule_info['rule_polygon'].split(",")
                self.new_rule_polygon = [ [float(parsed_rule[i]), float(parsed_rule[i+1])] for i in range(0,len(parsed_rule),2)]
                self.reset_page_frame()
                return
            elif callback[0] == "item_right_clicked_callback" and callback[1] == self.rules_list_item.identifier:
                selected_index = callback[3]
                selected_rule_info = self.selected_camera_rules_info[selected_index]
                result = self.api_dealer.delete_rule_by_rule_uuid(rule_uuid=selected_rule_info["rule_uuid"])
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Kural silindi"})
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})
                

            


        


                                        