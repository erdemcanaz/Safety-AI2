from modules import picasso
import cv2
import numpy as np

import requests, base64
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

        "gaussian_blur_kernel_size": 31,

    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None

        self.start_date_dd_mm_yyyy:str = datetime.datetime.now().strftime("%d.%m.%Y")
        self.start_date_shift:str = (datetime.datetime.now().hour//8)
        self.end_date_dd_mm_yyyy:str = datetime.datetime.now().strftime("%d.%m.%Y")
        self.end_date_shift:str = (datetime.datetime.now().hour//8)

        self.first_data_index_to_display:int = 0

        self.violation_image_dict:Dict = None


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

            if self.violation_image_dict is None:
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
                    if self.fetched_data is not None:
                        report_page_index = (y - self.CONSTANTS["show_report_image_bboxs"][1])//65
                        report_index = self.first_data_index_to_display + report_page_index
                        if not report_index >= len(self.fetched_data):
                            report_uuid = self.fetched_data[report_index]["violation_uuid"]
                            print(f"Report Index: {report_index}, Report UUID: {report_uuid}")
                            self.violation_image_dict, status_code = active_user.request_violation_image_with_violation_uuid(violation_uuid=report_uuid)
            else: #Violation image dict is not None, should show the image and mouse click should be for closing the image
                self.violation_image_dict = None 

                if self.__is_xy_in_bbox(x, y, self.CONSTANTS["show_report_image_bboxs"]):
                    if self.fetched_data is not None:
                        report_page_index = (y - self.CONSTANTS["show_report_image_bboxs"][1])//65
                        report_index = self.first_data_index_to_display + report_page_index
                        if not report_index >= len(self.fetched_data):
                            report_uuid = self.fetched_data[report_index]["violation_uuid"]
                            print(f"Report Index: {report_index}, Report UUID: {report_uuid}")
                            self.violation_image_dict, status_code = active_user.request_violation_image_with_violation_uuid(violation_uuid=report_uuid)
                
                

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            if self.violation_image_dict is None:
                program_state[0] = 4
                program_state[1] = 0
                program_state[2] = 0    
            else:
                self.violation_image_dict = None
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

        if self.violation_image_dict is not None:
            camera_uuid = self.violation_image_dict.get("camera_uuid")
            violation_uuid = self.violation_image_dict.get("violation_uuid")
            camera_hr_name = self.violation_image_dict.get("camera_hr_name")
            date_time = self.violation_image_dict.get("date_time")        
            date_requested = self.violation_image_dict.get("date_requested")
            person_normalized_bboxes = self.violation_image_dict.get("person_normalized_bboxes")
            image_base_64 = self.violation_image_dict.get("image_base_64")

            image_bytes = base64.b64decode(image_base_64)
            np_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

            is_violation = False
            violation_types_found = []
            for person in person_normalized_bboxes:
                x1, y1, x2, y2, violation_type = person
                x1, y1, x2, y2 = int(x1*image.shape[1]), int(y1*image.shape[0]), int(x2*image.shape[1]), int(y2*image.shape[0])
                color = (0,0,169) if violation_type in ["hard_hat", "restricted_area"] else (169,96,0)
            
                roi = image[y1:y2, x1:x2]            
                blurred_roi = cv2.GaussianBlur(roi, (self.CONSTANTS["gaussian_blur_kernel_size"], self.CONSTANTS["gaussian_blur_kernel_size"]), 0)
                image[y1:y2, x1:x2] = blurred_roi
                
                if violation_type == "hard_hat":
                    picasso.draw_image_on_frame(image, image_name="red_hardhat_transp", x=x2+5, y=y1, width=30, height=30, maintain_aspect_ratio=False)
                    violation_types_found.append("hard_hat")
                elif violation_type == "restricted_area":
                    picasso.draw_image_on_frame(image, image_name="red_restricted_area_transp", x=x2+5, y=y1, width=30, height=30, maintain_aspect_ratio=False)
                    violation_types_found.append("restricted_area")
                
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                is_violation = True if violation_type in ["hard_hat", "restricted_area"] else is_violation
            
            violation_types_found = list(set(violation_types_found))

            cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA) # Resize image to 1280x720 so that text can be written on it properly

            # Define your font settings
            header_color = (0, 0, 0)  # Black for headers
            value_color = (255, 255, 255)   # White for values
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontsize = 0.4
            font_thickness = 1

            # Define the starting position
            start_x = 10
            start_y = 15
            line_spacing = 13

            # Define the max header length for alignment
            max_header_length = 20

            # Define the text elements
            texts = [
                ('Kamera UUID', camera_uuid),
                ('Ihlal UUID', violation_uuid),
                ('Gerceklesme Tarihi', date_time),
                ('Kamera Adi', camera_hr_name),
                ('Ihlal Turu', violation_types_found),
                ('Talep Eden Kisi', active_user.get_token_person_name()),
                ('Talep ettigi tarih', date_requested)
            ]

            # Draw each header and value with different colors
            for i, (header, value) in enumerate(texts):
                header_text = f"{header:<{max_header_length}}"
                header_position = (start_x, start_y + i * line_spacing)
                value_position = (start_x + 50, start_y + i * line_spacing)  # Adjust 200 based on your text size

                # Draw header
                cv2.putText(image, header_text, header_position, font, fontsize, header_color, font_thickness, cv2.LINE_AA)
                
                # Draw value
                cv2.putText(image,str(value), value_position, font, fontsize, value_color, font_thickness, cv2.LINE_AA)
            
            #
            picasso.draw_image_on_frame(ui_frame, image_name="violation_image_background", x=310, y=230, width=1316, height=785, maintain_aspect_ratio=False)
            picasso.draw_frame_on_frame(ui_frame, image, x=325, y=265, width=1280, height=720, maintain_aspect_ratio=False)
            
        cv2.imshow(cv2_window_name, ui_frame)



        



    
