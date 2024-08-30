import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, datetime,base64, numpy as np

class ReportedViolationsPage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="reported_violations_page_template", default_resolution=(1920,1080))
        self.page_frame = None 
        self.fetched_violations = None
        self.last_shown_violation_frame_info = None
        
        self.reported_violations_list_ui_item = ui_items.BasicList( 
            identifier = 'list_'+str(uuid.uuid4()),
            pos_n=(0.04, 0.19),
            size_n=(0.91, 0.74),
            list_render_configs = {
                "list_style": "basic",
                "item_per_page":25, 
                "padding_precentage_per_item": 0.05,
                "colum_slicing_ratios":[0.25,1.25,1,1,1,1,1],
                "list_background_color": [(240, 240, 240), (169, 96, 0)],
                "list_border_color": [(255, 255, 255), (255, 255, 255)],
                "list_border_thickness": [2, 2],
                "list_item_text_font_scale": [0.75, 0.75],
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

        self.assign_today_as_dates_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.648, 0.057),
            size_n=(0.075, 0.036),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Bugün",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.fetch_reported_violations_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.876, 0.057),
            size_n=(0.075, 0.036),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Getir",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )
        
        self.start_date_input = ui_items.TextInput(
            identifier = "start_date_input_"+str(uuid.uuid4()),
            pos_n=(0.289, 0.057),
            size_n=(0.100, 0.036),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "gün.ay.yıl",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale":[0.75, 0.75],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.end_date_input = ui_items.TextInput(
            identifier = "end_date_input_"+str(uuid.uuid4()),
            pos_n=(0.494, 0.057),
            size_n=(0.100, 0.036),
            text_input_render_configs={   
                "text_input_style": "basic",     
                "text_input_default_text": "gün.ay.yıl",
                "text_input_default_text_color": (200, 200, 200),
                "text_input_text_font_scale": [0.75, 0.75],
                "text_input_text_thickness": [2, 2],
                "text_input_text_color": [(169, 96, 0), (255, 255, 255)],
                "text_input_background_color": [(225, 225, 225), (169, 96, 0)],
                "text_input_border_color": [(255, 255, 255), (255, 255, 255)],
                "text_input_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.reported_violations_list_ui_item, self.previous_page_button, self.start_date_input, self.end_date_input
                              , self.assign_today_as_dates_button, self.fetch_reported_violations_button]
       
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
                program_state[0] = 2
                return
            elif callback == ["left_clicked_callback", self.assign_today_as_dates_button.identifier, True]:   
                print("assign_today_as_dates_button")
                today = datetime.datetime.now().strftime("%d.%m.%Y")    
                self.start_date_input.set_text(today)
                self.end_date_input.set_text(today)
            elif callback == ["left_clicked_callback", self.fetch_reported_violations_button.identifier, True]:   
                start_date = self.start_date_input.get_text()
                end_date = self.end_date_input.get_text()
                result = self.api_dealer.fetch_reported_violations_between_dates(start_date_ddmmyyyy= start_date, end_date_ddmmyyyy = end_date)
                if result[0]:
                    pprint.pprint(result[2]['reported_violations'])
                    self.fetched_violations = result[2]['reported_violations'] # camera_uuid, image_uuid, region_name, violation_date, violation_score, violation_type, violation_uuid
                    formatted_violations = []
                    for ind, violation in enumerate(self.fetched_violations):                        
                        formatted_violations.append({
                            "COLUMN_0": str(ind+1),
                            "COLUMN_1": violation["violation_date"],
                            "COLUMN_2": violation["region_name"],
                            "COLUMN_3": violation["violation_type"],
                            "COLUMN_4": str(violation["violation_score"]),
                            "COLUMN_5": violation["camera_uuid"],
                            "COLUMN_6": violation["violation_uuid"],
                            "violation_info": violation
                        })
                    self.reported_violations_list_ui_item.set_list_items(formatted_violations)
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})

            elif callback[0] == "item_clicked_callback" and callback[1] == self.reported_violations_list_ui_item.identifier:
                selected_index = callback[3]
                image_uuid = self.fetched_violations[selected_index]["image_uuid"]
                result = self.api_dealer.get_encrypted_image_by_uuid(image_uuid)
                if result[0]:
                    self.last_shown_violation_frame_info = result[2]["image_info"]
                    if self.last_shown_violation_frame_info is None:
                        self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":"Görüntü bulunamadı."})
                    else:
                        self.last_shown_violation_frame_info['image'] =  cv2.imdecode(np.frombuffer(base64.b64decode(self.last_shown_violation_frame_info['image_b64']),np.uint8), cv2.IMREAD_COLOR)
                        resized_image = cv2.resize(self.last_shown_violation_frame_info['image'], (640, 480), interpolation = cv2.INTER_AREA)

                        cv2.namedWindow("Violation Image", cv2.WINDOW_NORMAL)
                        cv2.setWindowProperty("Violation Image", cv2.WND_PROP_TOPMOST, 1)
                        cv2.imshow("Violation Image", resized_image)
                else:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})
                self.reset_page_frame()
             

        


                                        