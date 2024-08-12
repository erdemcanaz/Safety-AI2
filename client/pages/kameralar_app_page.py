from modules import picasso, text_transformer
import cv2
import numpy as np

import requests
from typing import Dict, List
import time,copy, uuid

class KameralarApp():

    CONSTANTS = {
        "allowed_keys": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?`~ ",      
        "clear_camera_configs_bbox": (364,143,436,194),
        "decrease_camera_index_button": (404, 208, 420, 238),
        "increase_camera_index_button": (405, 893, 421, 920),
        "fetch_image_button": (1456, 648, 1692, 682),
        "show_password_bbox": (1087, 882, 1131, 910),
        "clear_dummy_camera_dict_bbox": (696, 1017, 908, 1045),
        "update_camera_configs_bbox": (922, 1017, 1137, 1045),
        "create_camera_configs_bbox": (1149, 1017, 1364, 1045),
        "delete_camera_configs_bbox": (1392, 1017, 1611, 1045),

        "ip_address_bbox": (744, 744, 1132, 772),
        "uuid_bbox": (744, 779, 1132, 807),
        "is_alive_bbox": (744, 813, 1132, 841),
        "username_bbox": (744, 847, 1132, 875),
        "password_bbox": (744, 882, 1083, 910),
        "NVR_ip_bbox": (744, 916, 1132, 944),
        "camera_region_bbox": (744, 951, 1132, 979),

        "camera_list_bbox": (74, 211, 391, 922),

        "camera_config_fetching_min_interval": 5 # seconds

    }

    def __init__(self):
        self.last_time_camera_configs_fetched = 0
        self.first_camera_index_to_show = 0

        self.ORIGINAL_CAMERA_CONFIGS = None
        self.camera_configs = None

        self.show_password = False

        self.__reset_dummy_camera_dict()
        self.camera_fetched_frame = None
        self.camera_fetched_frame_ip  = ""

    def __reset_dummy_camera_dict(self):
        self.camera_fetched_frame = None
        self.camera_fetched_frame_ip  = ""

        self.dummy_camera_dict = {
            "is_alive": True,
            "camera_uuid": "",
            "camera_region": "",
            "camera_description": "",
            "NVR_ip": "",
            "username": "",
            "password": "",
            "camera_ip_address": "",
            "stream_path": "",
            "active_rules": []
        }      

    def __is_xy_in_bbox(self, x:int, y:int, bbox:tuple):
        x1, y1, x2, y2 = bbox
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return True
        return False 
    
    def __get_cameras_to_show(self) -> List[Dict]:
        if self.camera_configs is None:
            return []
        
        if self.first_camera_index_to_show >= len(self.camera_configs):
            self.first_camera_index_to_show = max(0, len(self.camera_configs) - 11)
        
        return self.camera_configs[self.first_camera_index_to_show:self.first_camera_index_to_show+11]
    
    def __check_if_camera_is_old_updated_or_new(self, camera_dict:Dict = None) -> str:
        keys_to_check = ["is_alive", "camera_uuid", "camera_region", "camera_description", "NVR_ip", "username", "password", "camera_ip_address", "stream_path", "active_rules"]
        
        for _camera_dict in self.ORIGINAL_CAMERA_CONFIGS:
            if _camera_dict.get("camera_ip_address") == camera_dict["camera_ip_address"]: # if camera is already in the list
                for key in keys_to_check:
                    if _camera_dict.get(key) != camera_dict.get(key):
                        return "updated"
                else:
                    return "old"
        else: # if camera is not in the list
            return "new"

    def do_page(self, program_state:List[int]=None, cv2_window_name:str = None,  ui_frame:np.ndarray = None, active_user:object = None, mouse_input:object = None): 
        # Mouse input
        if mouse_input.get_last_leftclick_position() is not None:
            x, y = mouse_input.get_last_leftclick_position()
            mouse_input.clear_last_leftclick_position()        
            if self.__is_xy_in_bbox(x, y, self.CONSTANTS["clear_camera_configs_bbox"]):
                self.camera_configs = None
                self.__reset_dummy_camera_dict()  
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["decrease_camera_index_button"]):
                self.first_camera_index_to_show = max(0, self.first_camera_index_to_show-11)
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["increase_camera_index_button"]):
                self.first_camera_index_to_show = self.first_camera_index_to_show+11
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["camera_list_bbox"]):
                    if self.camera_configs is not None:
                        report_page_index = (y - self.CONSTANTS["camera_list_bbox"][1])//65
                        report_index = self.first_camera_index_to_show + report_page_index
                        if not report_index >= len(self.camera_configs):
                            self.dummy_camera_dict = copy.deepcopy(self.camera_configs[report_index])  
                            fetched_frame, status_code = active_user.request_camera_frame(username=self.dummy_camera_dict["username"], password=self.dummy_camera_dict["password"], camera_ip_address=self.dummy_camera_dict["camera_ip_address"])
                            if status_code == 200:
                                self.camera_fetched_frame = fetched_frame
                                self.camera_fetched_frame_ip = self.dummy_camera_dict["camera_ip_address"]
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["fetch_image_button"]):
                fetched_frame, status_code = active_user.request_camera_frame(username=self.dummy_camera_dict["username"], password=self.dummy_camera_dict["password"], camera_ip_address=self.dummy_camera_dict["camera_ip_address"])
                if status_code == 200:
                    self.camera_fetched_frame = fetched_frame
                    self.camera_fetched_frame_ip = self.dummy_camera_dict["camera_ip_address"]
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["show_password_bbox"]):
                self.show_password = not self.show_password
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["clear_dummy_camera_dict_bbox"]):
                self.__reset_dummy_camera_dict()
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["update_camera_configs_bbox"]):
                for camera_dict in self.camera_configs:
                    if camera_dict.get("camera_ip_address") == self.dummy_camera_dict.get("camera_ip_address"):
                        _deep_copy_dummy_camera_dict = copy.deepcopy(self.dummy_camera_dict)
                        camera_dict["is_alive"] = _deep_copy_dummy_camera_dict.get("is_alive")
                        camera_dict["camera_region"] = _deep_copy_dummy_camera_dict.get("camera_region")
                        camera_dict["camera_description"] = _deep_copy_dummy_camera_dict.get("camera_description")
                        camera_dict["NVR_ip"] = _deep_copy_dummy_camera_dict.get("NVR_ip")
                        camera_dict["username"] = _deep_copy_dummy_camera_dict.get("username")
                        camera_dict["password"] = _deep_copy_dummy_camera_dict.get("password")
                        break
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["create_camera_configs_bbox"]):
                for camera_dict in self.camera_configs:
                    if camera_dict.get("camera_ip_address") == self.dummy_camera_dict.get("camera_ip_address"):
                        break
                else:
                    _deep_copy_dummy_camera_dict = copy.deepcopy(self.dummy_camera_dict)
                    _deep_copy_dummy_camera_dict["camera_uuid"] = uuid.uuid4()
                    _deep_copy_dummy_camera_dict["stream_path"] = "profile2/media.smp" # For this project, stream path is fixed
                    self.camera_configs.append(_deep_copy_dummy_camera_dict)
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["delete_camera_configs_bbox"]):
                for camera_dict in self.camera_configs:
                    if camera_dict.get("camera_ip_address") == self.dummy_camera_dict.get("camera_ip_address"):
                        print(f"len of camera_configs before: {len(self.camera_configs)}")
                        self.camera_configs.remove(camera_dict)
                        print(f"len of camera_configs after: {len(self.camera_configs)}")
                        break
                self.__reset_dummy_camera_dict()
            elif self.__is_xy_in_bbox(x, y, self.CONSTANTS["is_alive_bbox"]):
                self.dummy_camera_dict["is_alive"] = not self.dummy_camera_dict["is_alive"]

        if self.camera_configs is None and (time.time() - self.last_time_camera_configs_fetched) > self.CONSTANTS["camera_config_fetching_min_interval"]:
            self.last_time_camera_configs_fetched = time.time()
            fetched_dict, status_code = active_user.request_camera_configs_dict()
            if status_code == 200:
                self.camera_configs = fetched_dict
                self.ORIGINAL_CAMERA_CONFIGS = copy.deepcopy(fetched_dict)
            
        # Keyboard input
        pressed_key = cv2.waitKey(1) & 0xFF
        if pressed_key == 27: #ESC            
                program_state[0] = 4
                program_state[1] = 0
                program_state[2] = 0  
        elif mouse_input.get_last_mouse_position() is not None and self.__is_xy_in_bbox(mouse_input.get_last_mouse_position()[0], mouse_input.get_last_mouse_position()[1], self.CONSTANTS["ip_address_bbox"]):
            if pressed_key == 8: # Backspace
                self.dummy_camera_dict["camera_ip_address"] = self.dummy_camera_dict["camera_ip_address"][:-1]
            elif chr(pressed_key) in self.CONSTANTS["allowed_keys"]:
                self.dummy_camera_dict["camera_ip_address"] += text_transformer.translate_text_to_english(chr(pressed_key))
        elif mouse_input.get_last_mouse_position() is not None and self.__is_xy_in_bbox(mouse_input.get_last_mouse_position()[0], mouse_input.get_last_mouse_position()[1], self.CONSTANTS["username_bbox"]):
            if pressed_key == 8:
                self.dummy_camera_dict["username"] = self.dummy_camera_dict["username"][:-1]
            elif chr(pressed_key) in self.CONSTANTS["allowed_keys"]:
                self.dummy_camera_dict["username"] +=  text_transformer.translate_text_to_english(chr(pressed_key))
        elif mouse_input.get_last_mouse_position() is not None and self.__is_xy_in_bbox(mouse_input.get_last_mouse_position()[0], mouse_input.get_last_mouse_position()[1], self.CONSTANTS["password_bbox"]):
            if pressed_key == 8:
                self.dummy_camera_dict["password"] = self.dummy_camera_dict["password"][:-1]
            elif chr(pressed_key) in self.CONSTANTS["allowed_keys"]:
                self.dummy_camera_dict["password"] +=  text_transformer.translate_text_to_english(chr(pressed_key))
        elif mouse_input.get_last_mouse_position() is not None and self.__is_xy_in_bbox(mouse_input.get_last_mouse_position()[0], mouse_input.get_last_mouse_position()[1], self.CONSTANTS["NVR_ip_bbox"]):
            if pressed_key == 8:
                self.dummy_camera_dict["NVR_ip"] = self.dummy_camera_dict["NVR_ip"][:-1]
            elif chr(pressed_key) in self.CONSTANTS["allowed_keys"]:
                self.dummy_camera_dict["NVR_ip"] +=  text_transformer.translate_text_to_english(chr(pressed_key))
        elif mouse_input.get_last_mouse_position() is not None and self.__is_xy_in_bbox(mouse_input.get_last_mouse_position()[0], mouse_input.get_last_mouse_position()[1], self.CONSTANTS["camera_region_bbox"]):
            if pressed_key == 8:
                self.dummy_camera_dict["camera_region"] = self.dummy_camera_dict["camera_region"][:-1]
            elif chr(pressed_key) in self.CONSTANTS["allowed_keys"]:
                self.dummy_camera_dict["camera_region"] +=  text_transformer.translate_text_to_english(chr(pressed_key))

        # Draw UI
        
        for camera_index, camera_dict in enumerate(self.__get_cameras_to_show()):
            x, y = 75, 207 + camera_index * 65
            picasso.draw_image_on_frame(ui_frame, image_name="camera_list_bar", x=x, y=y, width=317, height=60, maintain_aspect_ratio=True)
            cv2.putText(ui_frame, f"{self.first_camera_index_to_show+camera_index+1}", (x+10, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169,69,0), 2)
            
            camera_status = self.__check_if_camera_is_old_updated_or_new(camera_dict)
            camera_status_image = "new_camera_icon" if camera_status == "new" else "updated_camera_icon" if camera_status == "updated" else "old_camera_icon"
            picasso.draw_image_on_frame(ui_frame, image_name=camera_status_image, x=x+45, y=y+15, width=30, height=30, maintain_aspect_ratio=True)            
            cv2.putText(ui_frame, f"{camera_dict.get('camera_ip_address')}", (x+90, y+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (169,69,0), 2)
            
        #put the camera configs to the dummy camera dict
        font_size = 0.6
        font_thickness = 1

        is_alive_text = "Aktif" if self.dummy_camera_dict.get("is_alive") else "Pasif"
        uuid_text = "Henüz belirlenmedi"
        if self.camera_configs is not None:
            for camera_dict in self.camera_configs:
                if camera_dict.get("camera_ip_address") == self.dummy_camera_dict.get("camera_ip_address"):
                    uuid_text = camera_dict.get("camera_uuid")
                    print(f"uuid_text: {uuid_text}, ip: {self.dummy_camera_dict.get('camera_ip_address')}")
                    break
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('camera_ip_address')}", (750, 765), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{uuid_text}", (750, 799), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), font_thickness)
        cv2.putText(ui_frame, f"{is_alive_text}", (750, 833), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), 2)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('username')}", (750, 867), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{len(self.dummy_camera_dict.get('password'))*'*' if not self.show_password else self.dummy_camera_dict.get('password')}", (750, 902), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('NVR_ip')}", (750, 936), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('camera_region')}", (750, 971), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        cv2.putText(ui_frame, f"{self.dummy_camera_dict.get('camera_description')}", (1181, 799), cv2.FONT_HERSHEY_SIMPLEX, font_size, (169,69,0), font_thickness)
        
        if self.camera_fetched_frame is not None:
            picasso.draw_frame_on_frame(ui_frame, frame_to_draw=self.camera_fetched_frame, x=603, y=85, width=1106, height=614, maintain_aspect_ratio=False)
            cv2.putText(ui_frame, f"{self.camera_fetched_frame_ip}", (630, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (169,96,0), 2)

        picasso.draw_image_on_frame(ui_frame, image_name="kameralar_app_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)  
        cv2.imshow(cv2_window_name, ui_frame)
