import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, datetime,base64, numpy as np

class LinkIoTAndRulePage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="link_iot_and_rule_page_template", default_resolution=(1920,1080))
        self.page_frame = None 
        self.fetched_violations = None
        self.last_shown_violation_frame_info = None
        
        self.iot_devices_rows_list = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.04, 0.175),
            size_n=(0.91, 0.20),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":6, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[1,0.6,2], # Device Name, Device ID, Device UUID
                "list_background_color": [(240, 240, 240), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [0.5, 0.5],
                "list_item_text_thickness": [1,1],
                "list_item_text_color": [(169, 96, 0), (255, 255, 255)],
                "list_item_background_color": [(238, 236, 125), (169, 96, 0)],
                "list_item_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_item_border_thickness": [2, 2],
                "padding_n" : 0.005,
                "scroll_bar_width_n": 0.01,
                "arrow_icon_height_n": 0.08,
            }
        )

        self.rules_rows_list = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.04, 0.45),
            size_n=(0.91, 0.20),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":6, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[1, 3 , 1, 1, 1, 6, 3], # Rule Department, Rule Type, Evaluation Method, Threshold Value, FOL Threshold Value, Rule UUID, Last Time Triggered
                "list_background_color": [(240, 240, 240), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [0.5, 0.5],
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

        self.relation_rows_list = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.04, 0.725),
            size_n=(0.91, 0.20),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":6, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[5,2,5,2,1,5], # Rule Department, Rule Type, Evaluation Method, Threshold Value, FOL Threshold Value, Rule UUID, Last Time Triggered
                "list_background_color": [(240, 240, 240), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [0.5, 0.5],
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

        self.match_iot_device_with_rule_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.850, 0.057),
            size_n=(0.075, 0.036),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Eşleştir",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )
        
        self.device_uuid_textfield = ui_items.TextField(
            identifier="text_field_"+str(uuid.uuid4()),
            pos_n=(0.275, 0.06),
            size_n=(0.150, 0.036),
            text_field_render_configs={   
                "text_field_style": "basic",   
                "text_field_default_text": "IoT Cihaz UUID", 
                "text_field_default_text_color": (200, 200, 200),
                "text_field_text_font_scale": [0.6, 0.6],
                "text_field_text_thickness": [2, 2],
                "text_field_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_field_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_field_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_field_border_thickness": [2, 2]
            }
        )
        
        self.rule_uuid_textfield = ui_items.TextField(
            identifier="text_field_"+str(uuid.uuid4()),
            pos_n=(0.500, 0.06),
            size_n=(0.150, 0.036),
            text_field_render_configs={   
                "text_field_style": "basic",   
                "text_field_default_text": "Kural UUID", 
                "text_field_default_text_color": (200, 200, 200),
                "text_field_text_font_scale": [0.6,0.6],
                "text_field_text_thickness": [2, 2],
                "text_field_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_field_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_field_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_field_border_thickness": [2, 2]
            }
        )

        self.which_action_textinput = ui_items.TextInput(
            identifier = "text_input_"+str(uuid.uuid4()),
            pos_n=(0.725, 0.06),
            size_n=(0.1, 0.036),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "Aksiyon",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [0.6, 0.6],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )
        self.page_ui_items = [self.iot_devices_rows_list, self.rules_rows_list, self.previous_page_button, self.device_uuid_textfield, self.rule_uuid_textfield
                              , self.match_iot_device_with_rule_button, self.relation_rows_list, self.which_action_textinput]
       
        self.reset_page_frame_required_callbacks = []
        for item in self.page_ui_items:
            self.reset_page_frame_required_callbacks.extend(item.get_reset_page_frame_required_callbacks())
        
        self.iot_device_rows = [] #device name, device id, device_uuid
        self.rules_rows = [] #rule_department, rule_type, evaluation_method, threshold_value, fol_threshold_value, rule_uuid, last_time_triggered
        self.relation_rows = [] # device_uuid, is_device_exists, rule_uuid , is_rule_exists which_action  
        self.update_iotdev_rules_and_relations()

        # ==========================
        self.reset_page_frame()

    def update_iotdev_rules_and_relations(self):
        #fetch all iot devices
        fetch_iot_devices_result = self.api_dealer.fetch_all_iot_devices()
        if not fetch_iot_devices_result[0]:
            print("Error fetching iot devices:", fetch_iot_devices_result[1])
            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":fetch_iot_devices_result[1]})
            return
        iot_devices = fetch_iot_devices_result[2]
        self.iot_device_rows = []
        for iot_device in iot_devices:
            self.iot_device_rows.append({
                "COLUMN_0": iot_device['device_name'],
                "COLUMN_1": iot_device['device_id'],
                "COLUMN_2": iot_device['device_uuid']
            })        

        #fetch all rules
        fetch_rules_result = self.api_dealer.fetch_all_rules() 
        if not fetch_rules_result[0]:
            print("Error fetching rules:", fetch_rules_result[1])
            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":fetch_rules_result[1]})
            return
        rules = fetch_rules_result[2]
        self.rules_rows = []
        for rule in rules:
            self.rules_rows.append({
                "COLUMN_0": rule['rule_department'],
                "COLUMN_1": rule['rule_type'],
                "COLUMN_2": rule['evaluation_method'],
                "COLUMN_3": f"{float(rule['threshold_value']):.2f}",
                "COLUMN_4": f"{float(rule['fol_threshold_value']):.2f}",
                "COLUMN_5": rule['rule_uuid'],
                "COLUMN_6": rule['last_time_triggered']

            })
        
        #fetch all relations
        fetch_relations_result = self.api_dealer.fetch_all_iot_device_and_rule_relations()
        if not fetch_relations_result[0]:
            print("Error fetching relations:", fetch_relations_result[1])
            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":fetch_relations_result[1]})
            return
        relations = fetch_relations_result[2]
        self.relation_rows = []
        for relation in relations:
            self.relation_rows.append({
                "COLUMN_0": relation['device_uuid'],
                "COLUMN_1": None, #is_device_exists
                "COLUMN_2": relation['rule_uuid'],
                "COLUMN_3": None, #is_rule_exists
                "COLUMN_4": relation['which_action'],
                "COLUMN_5": relation['relation_uuid']
            })

        for relation_row in self.relation_rows:
            relation_row["COLUMN_1"] = "Cihaz Aktif" if relation_row["COLUMN_0"] in [iot_device["COLUMN_2"] for iot_device in self.iot_device_rows] else "Cihaz Silinmiş"
            relation_row["COLUMN_3"] = "Kural Aktif" if relation_row["COLUMN_2"] in [rule["COLUMN_5"] for rule in self.rules_rows] else "Kural Silinmiş"

        #update lists
        self.iot_devices_rows_list.set_list_items(items = self.iot_device_rows)
        self.rules_rows_list.set_list_items(items = self.rules_rows)
        self.relation_rows_list.set_list_items(items = self.relation_rows)            

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
                program_state[0] = 2
                return
            elif callback == ["left_clicked_callback", self.match_iot_device_with_rule_button.identifier, True]:   
                # create iot device
                device_uuid = self.device_uuid_textfield.get_text()
                rule_uuid = self.rule_uuid_textfield.get_text()
                which_action = self.which_action_textinput.get_text()
                result = self.api_dealer.add_iot_device_and_rule_relation(device_uuid = device_uuid, rule_uuid = rule_uuid, which_action = which_action)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"İlişki başarıyla eklendi."})
                    self.update_iotdev_rules_and_relations()
                    self.reset_page_frame()
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})

            elif callback[0] == "item_clicked_callback" and callback[1] == self.iot_devices_rows_list.identifier:
                # Update IoT Device Text Field with the clicked item UUID
                selected_index = callback[3]
                clicked_row = self.iot_device_rows[selected_index]

                device_uuid = clicked_row["COLUMN_2"]
                self.device_uuid_textfield.set_text(device_uuid)
                self.reset_page_frame()

            elif callback[0] == "item_clicked_callback" and callback[1] == self.rules_rows_list.identifier:
                # Update Rule UUID Text Field with the clicked item UUID
                selected_index = callback[3]
                clicked_row = self.rules_rows[selected_index]

                rule_uuid = clicked_row["COLUMN_5"]
                self.rule_uuid_textfield.set_text(rule_uuid)
                self.reset_page_frame()
            
            elif callback[0] == "item_right_clicked_callback" and callback[1] == self.rules_rows_list.identifier:
                selected_index = callback[3]
                clicked_row = self.rules_rows[selected_index]   
                rule_uuid = clicked_row["COLUMN_5"]

                #trigger rule
                result = self.api_dealer.trigger_rule(rule_uuid)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"Kural tetiklendi."})
                    self.update_iotdev_rules_and_relations()
                    self.reset_page_frame()
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})

            elif callback[0] == "item_right_clicked_callback" and callback[1] == self.relation_rows_list.identifier:
                selected_index = callback[3]
                clicked_row = self.relation_rows[selected_index]   

                relation_uuid = clicked_row["COLUMN_5"]
                result = self.api_dealer.remove_iot_device_and_rule_relation(relation_uuid)
                if result[0]:
                    self.popup_dealer.append_popup({"background_color":(0,255,0), "created_at":time.time(), "duration":2, "text":"İlişki başarıyla silindi."})
                    self.update_iotdev_rules_and_relations()
                    self.reset_page_frame()
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[1]})



        
             
    
        


                                        