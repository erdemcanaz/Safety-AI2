import requests, base64
import json, pprint
import jwt
import numpy as np
import cv2

import PREFERENCES

class SafetyAIApiDealer():
    def __init__(self):
        self.SERVER_IP_ADDRESS = PREFERENCES.SERVER_IP_ADDRESS   
        self.USERNAME = PREFERENCES.SAFETY_AI_USER_INFO['username']
        self.PASSWORD = PREFERENCES.SAFETY_AI_USER_INFO['password']
        self.PERSONAL_FULLNAME = PREFERENCES.SAFETY_AI_USER_INFO['personal_fullname']
        self.JWT_TOKEN = None
        self.DECODED_TOKEN = None

    @staticmethod
    def encode_frame_for_url_body_b64_string(np_ndarray: np.ndarray = None):
        if np_ndarray is None or not isinstance(np_ndarray, np.ndarray):
            raise ValueError('Invalid np_ndarray provided')
        
        success, encoded_image = cv2.imencode('.jpg', np_ndarray)
        if not success:
            raise ValueError('Failed to encode image')
        base64_encoded_jpg_image_string = base64.b64encode(encoded_image.tobytes()).decode('utf-8')

        return base64_encoded_jpg_image_string
    
    def get_access_token(self, username:str =None, password:str = None ) -> bool: #AKA login        
        try:
            payload = {'username': self.USERNAME, 'password': self.PASSWORD}
            response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/token", data=payload, timeout=1)
            if response.status_code == 200:
                self.JWT_TOKEN = response.json()['access_token']
                self.DECODED_TOKEN = jwt.decode(self.JWT_TOKEN, options={"verify_signature": False}, algorithms=["HS256"])
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
    
    def fetch_all_camera_info(self):
        """
        Returns a list of all camera info.
        The list is in the following format if successful:
        [
            True,
            detail:str,
            [
                {
                    "camera_uuid": "d2040d78-cb94-4a3f-b9cf-b63bdbc2faa5",
                    "camera_ip_address": "1.1.1.1",
                    "camera_region": "string",
                    "camera_description": "string",
                    "username": "string",
                    "password": "string",
                    "stream_path": "string",
                    "camera_status": "active"
                },
                ...
            ]
        ]
        if not successful:
        [
            False,
            detail:str,
            []
        ]

        """

        def request_to_try():
            try:
                header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
                response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_camera_info", headers=header, timeout=1)
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data' 
                
                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']['all_camera_info']]
                else:
                    return [False, response_body['detail'], []]

            except Exception as e:
                return [False , str(e), []]
            

        result = request_to_try()
        if result[0]: return result            
        print(f"Refreshing token and retrying once more... {self.fetch_all_camera_info.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)
        return request_to_try()
    
    def fetch_all_rules(self):
        """
        """
        def request_to_try():
            try:
                header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}             
                response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_rules", headers=header, timeout=1)
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data'                     
                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']['all_rules']]
                else:
                    return [False, response_body['detail'], []]

            except Exception as e:
                return [False , str(e), []]

        result = request_to_try()
        if result[0]: return result            
        print(f"Refreshing token and retrying once more... {self.fetch_all_rules.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)
        return request_to_try()

    def update_last_camera_frame_as(self, camera_uuid:str=None, is_violation_detected:bool=None, is_person_detected:bool=None, frame:np.ndarray=None):
        """
        """
        def request_to_try():
            try:
                url_b64_frame = self.encode_frame_for_url_body_b64_string(frame)
                payload = {
                    'camera_uuid': camera_uuid,
                    'is_violation_detected': is_violation_detected,
                    'is_person_detected': is_person_detected,
                    'frame_b64_string': url_b64_frame
                }
                header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}             
                response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/update_last_camera_frame_as", headers=header, data = json.dumps(payload), timeout=1)
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data' 
                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']]
                else:
                    return [False, response_body['detail'], []]

            except Exception as e:
                return [False , str(e), []]

        result = request_to_try()
        if result[0]: return result            
        print(f"Refreshing token and retrying once more... {self.update_last_camera_frame_as.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)
        return request_to_try()

    def trigger_rule(self, rule_uuid:str=None):
        """
        """
        def request_to_try():
            try:
                payload = {
                    'rule_uuid': rule_uuid,
                }
                header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}             
                response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/trigger_rule", headers=header, data = json.dumps(payload), timeout=1)
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data' 
                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']]
                else:
                    return [False, response_body['detail'], []]

            except Exception as e:
                return [False , str(e), []]

        result = request_to_try()
        if result[0]: return result            
        print(f"Refreshing token and retrying once more... {self.trigger_rule.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)
        return request_to_try()

    def update_count(self, count_key:str=None, count_subkey:str=None, delta_count:float = None):
        """
        """
        def request_to_try():
            try:
                payload = {
                    'count_key': count_key,
                    'count_subkey': count_subkey,
                    'delta_count': delta_count
                }
                header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}             
                response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/update_count", headers=header, data = json.dumps(payload), timeout=1)
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data' 
                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']]
                else:
                    return [False, response_body['detail'], []]

            except Exception as e:
                return [False , str(e), []]

        result = request_to_try()
        if result[0]: return result            
        print(f"Refreshing token and retrying once more... {self.trigger_rule.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)
        return request_to_try()

