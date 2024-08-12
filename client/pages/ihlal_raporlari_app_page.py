from modules import picasso
import cv2
import numpy as np

import requests
from typing import Dict, List
import datetime
from modules import picasso, text_transformer

class IhlalRaporlariApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "allowed_date_keys": "1234567890.",
        "data_fetch_period_s": 5, # fetch data every 5 seconds  
        "start_date_text_field_bbox": (554, 64, 745, 100), 
        "start_date_shift_change_bbox": (752, 64, 826, 98),
        "end_date_text_field_bbox": (951, 64, 1140, 100),
        "end_date_shift_change_bbox": (1148, 64, 1222, 98),
        "request_ihlal_raporlari_data_button": (1358,63, 1446,100),
        "assign_this_shift": (1464, 64, 1504, 100),

        "show_report_image_bboxs": (1700,223,1835,989),
        "decrease_data_index_button": (1860, 186, 1877, 214),
        "increase_data_index_button": (1861, 976, 1877, 1005),
        "scroll_bar_bbox": (1862, 215, 1880, 974),

    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None

        self.start_date_dd_mm_yyyy:str = datetime.datetime.now().strftime("%d.%m.%Y")
        self.start_date_shift:str = (datetime.datetime.now().hour//8)
        self.end_date_dd_mm_yyyy:str = datetime.datetime.now().strftime("%d.%m.%Y")
        self.end_date_shift:str = (datetime.datetime.now().hour//8)

        self.first_data_index_to_display:int = 0

    def __is_xy_in_bbox(self, x:int, y:int, bbox:tuple):
        x1, y1, x2, y2 = bbox
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return True
        return False 

    def __check_date_format_dd_mm_yyyy(self, date:str):
        if len(date) != 10: # dd.mm.yyyy
            return False
        if date[2] != "." or date[5] != ".":
            return False
        if not date[0:2].isdigit() or not date[3:5].isdigit() or not date[6:].isdigit():
            return False
        return True
    
    def __get_reports_to_display(self):
        if self.fetched_data is None:
            self.first_data_index_to_display = 0
            return []
        
        if self.first_data_index_to_display >= len(self.fetched_data):
            self.first_data_index_to_display = max(0, len(self.fetched_data)-12)

        return self.fetched_data[self.first_data_index_to_display:min(self.first_data_index_to_display+12, len(self.fetched_data))]
     

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):
        
        # Mouse input
        if mouse_input.get_last_leftclick_position() is not None:
            x, y = mouse_input.get_last_leftclick_position()
            mouse_input.clear_last_leftclick_position()
            if self.__is_xy_in_bbox(x, y, self.CONSTANTS["start_date_shift_change_bbox"]):
                self.start_date_shift = (self.start_date_shift + 1) % 3
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["end_date_shift_change_bbox"]):
                self.end_date_shift = (self.end_date_shift + 1) % 3
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["request_ihlal_raporlari_data_button"]):
                if not self.__check_date_format_dd_mm_yyyy(self.start_date_dd_mm_yyyy) or not self.__check_date_format_dd_mm_yyyy(self.end_date_dd_mm_yyyy):
                    self.start_date_dd_mm_yyyy = ""
                    self.end_date_dd_mm_yyyy = ""              
                else:
                    self.first_data_index_to_display = 0
                    _start_date = self.start_date_dd_mm_yyyy+","+str(self.start_date_shift)
                    _end_date = self.end_date_dd_mm_yyyy+","+str(self.end_date_shift)
                    fetched_list, status_code = active_user.request_ihlal_raporlari_data(start_date = _start_date, end_date = _end_date)
                    if status_code == 200:
                        self.fetched_data = fetched_list
                    else: # Unauthorized -> USER NOT AUTHORIZED page
                        program_state[0] = 5
                        program_state[1] = 0
                        program_state[2] = 0

                    print(f"İhlal raporlari data is fetched with status code: {status_code}")
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["assign_this_shift"]):
                self.start_date_dd_mm_yyyy = datetime.datetime.now().strftime("%d.%m.%Y")
                self.start_date_shift = (datetime.datetime.now().hour//8)
                self.end_date_dd_mm_yyyy = datetime.datetime.now().strftime("%d.%m.%Y")
                self.end_date_shift = (datetime.datetime.now().hour//8)
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["decrease_data_index_button"]):
                self.first_data_index_to_display = max(0, self.first_data_index_to_display-12)
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["increase_data_index_button"]):
                self.first_data_index_to_display = self.first_data_index_to_display+12
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["scroll_bar_bbox"]) and self.fetched_data is not None:
                scroll_bar_height = self.CONSTANTS["scroll_bar_bbox"][3] - self.CONSTANTS["scroll_bar_bbox"][1]
                percentage = (y - self.CONSTANTS["scroll_bar_bbox"][1])/scroll_bar_height                
                index = int(percentage*len(self.fetched_data))
                while index % 12 != 0:
                    index -= 1
                self.first_data_index_to_display = index    
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["show_report_image_bboxs"]):
                report_page_index = (y - self.CONSTANTS["show_report_image_bboxs"][1])//65
                report_index = self.first_data_index_to_display + report_page_index
                report_uuid = self.__get_reports_to_display()[report_index]["violation_uuid"]
                print(f"Report Index: {report_index}, Report UUID: {report_uuid}")

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0    
        elif mouse_input.get_last_mouse_position() is not None and self.__is_xy_in_bbox(mouse_input.get_last_mouse_position()[0], mouse_input.get_last_mouse_position()[1], self.CONSTANTS["start_date_text_field_bbox"]): 
            if chr(pressed_key) in self.CONSTANTS["allowed_date_keys"]:
                self.start_date_dd_mm_yyyy += chr(pressed_key)
            elif pressed_key == 8:
                self.start_date_dd_mm_yyyy = self.start_date_dd_mm_yyyy[:-1]
        elif mouse_input.get_last_mouse_position() is not None and self.__is_xy_in_bbox(mouse_input.get_last_mouse_position()[0], mouse_input.get_last_mouse_position()[1], self.CONSTANTS["end_date_text_field_bbox"]):
            if chr(pressed_key) in self.CONSTANTS["allowed_date_keys"]:
                self.end_date_dd_mm_yyyy += chr(pressed_key)
            elif pressed_key == 8:
                self.end_date_dd_mm_yyyy = self.end_date_dd_mm_yyyy[:-1]

        today_date = datetime.datetime.now().strftime("%d.%m.%Y / %H:%M:%S / ")
        today_shift = "I" if datetime.datetime.now().hour < 8 else "II" if datetime.datetime.now().hour < 16 else "III"
        
        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="ihlal_raporlari_app_page", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  

        # put current user name
        text = active_user.get_token_person_name()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]            
        x = 1886-text_size[0]
        y = 1040
        cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (239, 237, 232), 2, cv2.LINE_AA)    
        # put start date and shift
        cv2.putText(ui_frame, today_date+today_shift, (1515, 89), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)
        # put start and end date shift
        cv2.putText(ui_frame, self.start_date_dd_mm_yyyy, (564, 93), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.putText(ui_frame, str(self.start_date_shift+1), (761, 89), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.putText(ui_frame, str(self.end_date_dd_mm_yyyy), (960, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.putText(ui_frame, str(self.end_date_shift+1), (1155, 89), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169, 96, 0), 2, cv2.LINE_AA)

        # Draw reports
        reports_to_draw = self.__get_reports_to_display()
        text_color = (0,0,0)
        text_thickness:int = 1
        for report_no, report in enumerate(reports_to_draw):
            y = 220 + report_no*65
            picasso.draw_image_on_frame(ui_frame, image_name="ihlal_row_light_blue" if report_no%2==0 else "ihlal_row_dark_blue", x=77, y=y, width=1763, height=58, maintain_aspect_ratio=True)
            cv2.putText(ui_frame, str(self.first_data_index_to_display+report_no+1), (88, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, text_thickness, cv2.LINE_AA)
            cv2.putText(ui_frame, report["violation_date"], (202, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, text_thickness, cv2.LINE_AA)
            cv2.putText(ui_frame, text_transformer.translate_text_to_english(report["region_name"]), (506, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, text_thickness, cv2.LINE_AA)
            cv2.putText(ui_frame, text_transformer.translate_text_to_english(report["violation_type"]), (872, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, text_thickness, cv2.LINE_AA)
            cv2.putText(ui_frame, text_transformer.translate_text_to_english(report["violation_score"]), (1116, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, text_thickness, cv2.LINE_AA)
            cv2.putText(ui_frame, text_transformer.translate_text_to_english(report["camera_uuid"][:8]+"..."), (1285, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, text_thickness, cv2.LINE_AA)
            cv2.putText(ui_frame, text_transformer.translate_text_to_english(report["violation_uuid"][:8]+"..."), (1504, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, text_thickness, cv2.LINE_AA)
        if self.fetched_data is not None:
            cv2.putText(ui_frame, f"{len(self.fetched_data)}", (88, 1020), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (136,136,136), text_thickness, cv2.LINE_AA)

            percentage = (self.first_data_index_to_display/len(self.fetched_data))
            scroll_bar_height = self.CONSTANTS["scroll_bar_bbox"][3] - self.CONSTANTS["scroll_bar_bbox"][1]
            bar_height_percentage = max((12/len(self.fetched_data)), 1)
            bar_height = min(int(scroll_bar_height*bar_height_percentage),10)

            bar_mid_y = int(self.CONSTANTS["scroll_bar_bbox"][1] + int(scroll_bar_height*percentage))
            bar_bottom_y = max(int(bar_mid_y - bar_height//2), self.CONSTANTS["scroll_bar_bbox"][1])
            bar_top_y = min(int(bar_mid_y + bar_height//2), self.CONSTANTS["scroll_bar_bbox"][3])
            cv2.rectangle(ui_frame, (self.CONSTANTS["scroll_bar_bbox"][0]-6, bar_bottom_y), (self.CONSTANTS["scroll_bar_bbox"][2]+5, bar_top_y), (169,96,0), -1)

       
        cv2.imshow(cv2_window_name, ui_frame)

        



    
