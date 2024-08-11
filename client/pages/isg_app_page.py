from modules import picasso
import cv2
import numpy as np

import requests, pprint
from typing import Dict, List
import datetime, time, random, base64

class ISGApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "data_fetch_period_s": 10, # fetch data every 5 seconds     
        "six_data_change_period_s": 3, # change the data every 10 seconds

        "main_image_bbox": (944, 84, 1854, 600),
        "image_bbox_0": (37, 145, 430, 368),
        "image_bbox_1": (475, 148, 868, 371),
        "image_bbox_2": (33, 444, 426, 666),
        "image_bbox_3": (475, 445, 868, 668),
        "image_bbox_4": (35, 740, 428, 962),
        "image_bbox_5": (475, 740, 868, 962),

    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None

        self.last_time_six_data_to_render_update = 0
        self.last_six_data_to_render = None
        pass

    def __return_six_data_from_fetched_data(self) -> List[Dict]:
        if self.fetched_data is None:
            return None

        violation_detected_datas = []
        no_violation_detected_datas = []

        # Separate data into violation and no-violation lists
        for data in self.fetched_data:
            for person_normalized_bbox in data.get("person_normalized_bboxes", []):
                if person_normalized_bbox[4] != "":  # Check if there's a violation
                    violation_detected_datas.append(data)
                    break  # Stop checking further bboxes once a violation is found
            else:
                no_violation_detected_datas.append(data)

        # Create the return list, starting with violations
        return_list = violation_detected_datas[:6]

        # If fewer than 6 violations, fill the rest with no-violation data
        if len(return_list) < 6:
            remaining_slots = 6 - len(return_list)
            random.shuffle(no_violation_detected_datas)
            return_list.extend(no_violation_detected_datas[:remaining_slots])

        return return_list
    
    def __convert_data_to_frame(self, data:dict) -> np.ndarray:
        camera_uuid = data.get("camera_uuid")
        camera_name = data.get("camera_name")
        datetime_str = data.get("datetime")
        camera_image_b64 = data.get("image_base_64")
        person_normalized_bboxes = data.get("person_normalized_bboxes")

        image_bytes = base64.b64decode(camera_image_b64)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        # Draw camera name and datetime

        cv2.putText(image, datetime_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)                
        is_violation_detected = False
        for person_normalized_bbox in person_normalized_bboxes:
            x1, y1, x2, y2, violation = person_normalized_bbox
            x1, y1, x2, y2 = int(x1 * image.shape[1]), int(y1 * image.shape[0]), int(x2 * image.shape[1]), int(y2 * image.shape[0])
            
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)
            
            if x1 < x2 and y1 < y2:
                roi = image[y1:y2, x1:x2]
                blurred_roi = cv2.GaussianBlur(roi, (31, 31), 0)  # Adjust the kernel size for desired blur
                image[y1:y2, x1:x2] = blurred_roi

                color = (0, 0, 255) if violation != "" else (0, 255, 0)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                if violation != "":
                    is_violation_detected = True
            else:
                pass
        
        region_name = camera_name if camera_name != "" else camera_uuid[:8]+"..."
        print(f"camera_name: {camera_name} | camera_uuid: {camera_uuid[:8]} | datetime: {datetime_str} | violation_detected: {is_violation_detected}")
        return image, region_name, is_violation_detected

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):
        
        if  (time.time() - self.last_time_data_fetch) > self.CONSTANTS["data_fetch_period_s"]:
            self.last_time_data_fetch = time.time()
            fetched_list, status_code = active_user.request_ISG_ui_data()
            if status_code == 200:
                self.fetched_data = fetched_list
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ISG data fetched with status code: {status_code}")
       
        # Mouse input

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0          


        today_date = datetime.datetime.now().strftime("%d.%m.%Y / %H:%M:%S")
        today_shift = "Vardiya-I " if datetime.datetime.now().hour < 8 else "Vardiya-II " if datetime.datetime.now().hour < 16 else "Vardiya-III "
        percentage = (datetime.datetime.now().hour%8) / 8
        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="ISG_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  

        # Draw user name
        text = active_user.get_token_person_name()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]            
        x = 1910-text_size[0]
        y = text_size[1]+5
        cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (239, 237, 232), 2, cv2.LINE_AA)

        # Draw date and shift
        cv2.putText(ui_frame, today_shift+today_date, (387, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.rectangle(ui_frame, (314, 95), (314+int(560*percentage), 110), (169, 96, 0), -1)


        if (time.time() - self.last_time_six_data_to_render_update) > self.CONSTANTS["six_data_change_period_s"]:
            self.last_time_six_data_to_render_update = time.time()
            self.last_six_data_to_render = self.__return_six_data_from_fetched_data() 

        if self.last_six_data_to_render is not None:            
            for i, data in enumerate(self.last_six_data_to_render):

                x1, y1, x2, y2 = self.CONSTANTS[f"image_bbox_{i}"]
                width, height = x2-x1, y2-y1
    
                frame, region_name, is_violation_detected = self.__convert_data_to_frame(data)
                print(f"Region: {region_name} | Violation: {is_violation_detected}")
                picasso.draw_frame_on_frame(ui_frame, frame, x1, y1, width, height, maintain_aspect_ratio=False)
                color = (0,0,169) if is_violation_detected else (169,96,0)
                if is_violation_detected: cv2.rectangle(ui_frame, (x1, y1), (x2, y2), color, 2)

                text_size = cv2.getTextSize(region_name, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]
                text_width, text_height = text_size
                text_x = x1 + (width - text_width) // 2  # Center the text horizontally
                text_y = y2 + 20  # Adjust y-coordinate as needed
                cv2.putText(ui_frame, region_name, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)

                if i == 0:
                    main_frame_x1, main_frame_y1, main_frame_x2, main_frame_y2 = self.CONSTANTS["main_image_bbox"]
                    picasso.draw_frame_on_frame(ui_frame, frame, main_frame_x1, main_frame_y1, main_frame_x2-main_frame_x1, main_frame_y2-main_frame_y1, maintain_aspect_ratio=False)
                    if is_violation_detected: cv2.rectangle(ui_frame,(main_frame_x1, main_frame_y1), (main_frame_x2, main_frame_y2), color, 2)
                    cv2.putText(ui_frame, region_name,(main_frame_x1+50,main_frame_y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)


        cv2.imshow(cv2_window_name, ui_frame)

        



    
