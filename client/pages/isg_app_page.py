from modules import picasso
import cv2
import numpy as np

import requests, pprint
from typing import Dict, List
import datetime, time, random, base64, copy

class ISGApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",
        "isg_data_fetch_period_s": 5, # fetch data every 5 seconds     
        "six_data_change_period_s": 2.5, # change the data every 10 seconds

        "main_image_bbox": (944, 84, 1854, 600),
        "image_bbox_0": (37, 145, 430, 368),
        "image_bbox_1": (475, 148, 868, 371),
        "image_bbox_2": (33, 444, 426, 666),
        "image_bbox_3": (475, 445, 868, 668),
        "image_bbox_4": (35, 740, 428, 962),
        "image_bbox_5": (475, 740, 868, 962),


        "person_count": (1132,788),
        "frame_count": (1600,788),
        "hard_hat_percentage": (1132, 945),
        "hard_hat_succes_count":(1071,903),
        "hard_hat_failure_count":(1071,946),
        "restricted_area_percentage": (1600,945),
        "restricted_area_succes_count":(1552,903),
        "restricted_area_failure_count":(1552,946),

    }

# dummy_dict = {
# "camera_uuid": uuid.uuid4(),
# "camera_hr_name" : random.choice(["A","B","C","D","E","F","G","H","I","J"]),
# "date_time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
# "people_analyzed" : random.randint(0,5000),
# "frame_analyzed" : random.randint(0,5000),
# "hard_hat_violation_counts" : [random.randint(0,5000),random.randint(0,5000)],
# "restricted_area_violation_counts" : [random.randint(0,5000),random.randint(0,5000)],            
# "person_normalized_bboxes" : [ [random.uniform(0,0.45), random.uniform(0,0.45), random.uniform(0.55,1), random.uniform(0.55,1), random.choice(["","","","", "hard_hat", "restricted_area"]),] for _ in range(random.randint(0,3))],


    def __init__(self):
        self.last_time_isg_data_fetch = 0
        self.fetched_data:list = []

        self.last_time_six_data_index_to_render_update = 0
        self.data_index_to_render = []    

    def __format_count_to_hr(self, number:int):
        if number < 1000:
            return str(number)
        elif number < 1000000:
            return f"{number/1000:.1f}K"
        else:
            return f"{number//1000000:.2f}M"
        
    def __update_six_data_index_to_render(self):        
        violation_data_indexes = []
        no_violation_but_person_data_indexes = []
        neither_violation_nor_person_data_indexes = []
        for data_index, data in enumerate(self.fetched_data):
            is_violation = False
            for person in data.get("person_normalized_bboxes"):
                if person[4] in ["hard_hat", "restricted_area"]:
                    is_violation = True
                    break
            if is_violation:
                violation_data_indexes.append(data_index)
            elif len(data.get("person_normalized_bboxes")) > 0:
                no_violation_but_person_data_indexes.append(data_index)
            else:
                neither_violation_nor_person_data_indexes.append(data_index)

        if len(violation_data_indexes) >= 6:
            self.data_index_to_render = random.sample(violation_data_indexes,6)
        elif len(violation_data_indexes) + len(no_violation_but_person_data_indexes) >= 6:
            self.data_index_to_render = violation_data_indexes + random.sample(no_violation_but_person_data_indexes, 6-len(violation_data_indexes))
        else:
            self.data_index_to_render = violation_data_indexes + no_violation_but_person_data_indexes + random.sample(neither_violation_nor_person_data_indexes, 6-len(violation_data_indexes)-len(no_violation_but_person_data_indexes))
    
    def __generate_frame_using_data(self, data:Dict=None):
        camera_uuid = data.get("camera_uuid")
        camera_hr_name = data.get("camera_hr_name")
        date_time = data.get("date_time")        
        person_normalized_bboxes = data.get("person_normalized_bboxes")
        image_base_64 = data.get("image_base_64")

        image_bytes = base64.b64decode(image_base_64)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        
        is_violation = False
        for person in person_normalized_bboxes:
            x1, y1, x2, y2, violation_type = person
            x1, y1, x2, y2 = int(x1*image.shape[1]), int(y1*image.shape[0]), int(x2*image.shape[1]), int(y2*image.shape[0])
            color = (169,96,0) if violation_type=="" else (0,0,169)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            is_violation = True if violation_type else False
        
        cv2.putText(image, date_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (169,96,0), 2, cv2.LINE_AA)

        camera_hr_name = camera_hr_name if camera_hr_name else camera_uuid[:8]+"..."
        return image, is_violation, camera_hr_name

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None):    
        # Fetch ISG data
        if  (time.time() - self.last_time_isg_data_fetch) > self.CONSTANTS["isg_data_fetch_period_s"]:
            self.last_time_isg_data_fetch = time.time()
            self.last_time_six_data_index_to_render_update = 0 # force update
            fetched_list, status_code = active_user.request_ISG_ui_data()
            if status_code == 200:
                self.fetched_data = fetched_list
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ISG data fetched with status code: {status_code}")
       
        if (time.time() - self.last_time_six_data_index_to_render_update) > self.CONSTANTS["six_data_change_period_s"]:
            self.last_time_six_data_index_to_render_update = time.time()
            self.__update_six_data_index_to_render()

        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC
            program_state[0] = 4
            program_state[1] = 0
            program_state[2] = 0          

        # Draw UI
        picasso.draw_image_on_frame(ui_frame, image_name="ISG_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  

        # Draw user name
        text = active_user.get_token_person_name()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]            
        x = 1910-text_size[0]
        y = text_size[1]+5
        cv2.putText(ui_frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (239, 237, 232), 2, cv2.LINE_AA)

        # Draw date and shift
        today_date = datetime.datetime.now().strftime("%d.%m.%Y / %H:%M:%S")
        today_shift = "Vardiya-I " if datetime.datetime.now().hour < 8 else "Vardiya-II " if datetime.datetime.now().hour < 16 else "Vardiya-III "
        percentage = (datetime.datetime.now().hour%8) / 8
        cv2.putText(ui_frame, today_shift+today_date, (387, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (169, 96, 0), 2, cv2.LINE_AA)
        cv2.rectangle(ui_frame, (314, 95), (314+int(560*percentage), 110), (169, 96, 0), -1)

        # Draw fetched data      
        for i, data_index in enumerate(self.data_index_to_render):         
            x1, y1, x2, y2 = self.CONSTANTS[f"image_bbox_{i}"]
            width, height = x2-x1, y2-y1
            image, is_violation, camera_hr_name = self.__generate_frame_using_data(self.fetched_data[data_index])
            picasso.draw_frame_on_frame(ui_frame, image, x1, y1, width, height, maintain_aspect_ratio=False)

            color = (0,0,169) if is_violation else (169,96,0)
            cv2.putText(ui_frame, camera_hr_name, (x1+10, y2+30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)
            if is_violation:
                cv2.rectangle(ui_frame, (x1, y1), (x2, y2), color, 5)

            if i == 0: # Main image
                x1, y1, x2, y2 = self.CONSTANTS["main_image_bbox"]
                width, height = x2-x1, y2-y1
                picasso.draw_frame_on_frame(ui_frame, image, x1, y1, width, height, maintain_aspect_ratio=False)
                cv2.putText(ui_frame, camera_hr_name, (x1+10, y2+30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)
                if is_violation:
                    cv2.rectangle(ui_frame, (x1, y1), (x2, y2), color, 5)

                color = (169,96,0)
                people_analyzed = self.__format_count_to_hr(self.fetched_data[data_index].get("people_analyzed"))
                frame_analyzed = self.__format_count_to_hr(self.fetched_data[data_index].get("frame_analyzed"))
                hard_hat_violation_counts = self.fetched_data[data_index].get("hard_hat_violation_counts")
                restricted_area_violation_counts = self.fetched_data[data_index].get("restricted_area_violation_counts")

                cv2.putText(ui_frame, f"   {people_analyzed}", self.CONSTANTS["person_count"], cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 2, cv2.LINE_AA)
                cv2.putText(ui_frame, f"   {frame_analyzed}", self.CONSTANTS["frame_count"], cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 2, cv2.LINE_AA)
                
                cv2.putText(ui_frame, f"   %{100*hard_hat_violation_counts[0]/(hard_hat_violation_counts[0]+hard_hat_violation_counts[1]):.1f}", self.CONSTANTS["hard_hat_percentage"], cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 2, cv2.LINE_AA)
                cv2.putText(ui_frame, f"{self.__format_count_to_hr(hard_hat_violation_counts[0])}", self.CONSTANTS["hard_hat_succes_count"], cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)
                cv2.putText(ui_frame, f"{self.__format_count_to_hr(hard_hat_violation_counts[1])}", self.CONSTANTS["hard_hat_failure_count"], cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)

                cv2.putText(ui_frame, f"   %{100*restricted_area_violation_counts[0]/(restricted_area_violation_counts[0]+restricted_area_violation_counts[1]):.1f}", self.CONSTANTS["restricted_area_percentage"], cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 2, cv2.LINE_AA)
                cv2.putText(ui_frame, f"{self.__format_count_to_hr(restricted_area_violation_counts[0])}", self.CONSTANTS["restricted_area_succes_count"], cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)
                cv2.putText(ui_frame, f"{self.__format_count_to_hr(restricted_area_violation_counts[1])}", self.CONSTANTS["restricted_area_failure_count"], cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)

        cv2.imshow(cv2_window_name, ui_frame)

        



    
