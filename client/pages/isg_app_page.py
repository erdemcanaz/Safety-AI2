from modules import picasso
import cv2
import numpy as np

import requests, pprint
from typing import Dict, List
import datetime, time, random, base64

class ISGApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "data_fetch_period_s": 5, # fetch data every 5 seconds       

        "image_bbox_0": (37, 145, 430, 368),
        "image_bbox_1": (475, 148, 868, 371),
        "image_bbox_2": (0, 0, 1920, 1080),
        "image_bbox_3": (0, 0, 1920, 1080),
        "image_bbox_4": (0, 0, 1920, 1080),
        "image_bbox_5": (0, 0, 1920, 1080),

    }

    def __init__(self):
        self.last_time_data_fetch = 0
        self.fetched_data:list = None
        pass

    def __return_six_data_from_fetched_data(self) -> List[Dict]:
        if self.fetched_data is None: return None

        return_list = []

        no_violation_detected_datas = []
        violation_detected_datas = []
        for data in self.fetched_data:
            for person_normalized_bbox in data.get("person_normalized_bboxes"):
                if person_normalized_bbox[4] != "":
                    violation_detected_datas.append(data)
                    break
            else:
                no_violation_detected_datas.append(data)

        if len(violation_detected_datas) >= 6:
            return_list = violation_detected_datas[:6]
        else:
            return_list = violation_detected_datas

            random.shuffle(no_violation_detected_datas)
            return_list.extend(no_violation_detected_datas[:min( len(no_violation_detected_datas), 6-len(violation_detected_datas) )])

        return return_list
    
    def __convert_data_to_frame(self, data:dict, width:int, height:int) -> np.ndarray:
        camera_uuid = data.get("camera_uuid")
        camera_name = data.get("camera_name")
        datetime_str = data.get("datetime")
        camera_image_b64 = data.get("image_base_64")
        person_normalized_bboxes = data.get("person_normalized_bboxes")

        image_bytes = base64.b64decode(camera_image_b64)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        image.resize((width, height))
        return image




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

        text = active_user.get_token_person_name()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]            
        x = 1910-text_size[0]
        y = text_size[1]+5
        cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (239, 237, 232), 2, cv2.LINE_AA)

        cv2.putText(ui_frame, today_shift+today_date, (387, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.rectangle(ui_frame, (314, 95), (314+int(560*percentage), 110), (169, 96, 0), -1)

        six_data_to_render = self.__return_six_data_from_fetched_data() 
        if six_data_to_render is not None:            
            for i, data in enumerate(six_data_to_render):
                if i != 0: continue

                x1, y1, x2, y2 = self.CONSTANTS[f"image_bbox_{i}"]
                width, height = x2-x1, y2-y1
    
                frame = self.__convert_data_to_frame(data)
                picasso.draw_frame_on_frame(ui_frame, frame, x, y, width, height, maintain_aspect_ratio=True)

                # for j, person_normalized_bbox in enumerate(data.get("person_normalized_bboxes")):
                #     x1, y1, x2, y2, violation = person_normalized_bbox
                #     x1, y1, x2, y2 = int(x1*width), int(y1*height), int(x2*width), int(y2*height)
                #     color = (0, 0, 255) if violation != "" else (0, 255, 0)
                #     cv2.rectangle(ui_frame, (x+x1, y+y1), (x+x2, y+y2), color, 2)
                #     cv2.putText(ui_frame, str(j+1), (x+x1, y+y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)
                #     cv2.putText(ui_frame, violation, (x+x1, y+y1-25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)

        cv2.imshow(cv2_window_name, ui_frame)

        



    
