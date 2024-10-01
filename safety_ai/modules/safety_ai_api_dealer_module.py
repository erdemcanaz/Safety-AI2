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

    # def fetch_all_camera_info(self):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        
    #     try:
    #         # Send a request to the server to fetch all camera info
    #         response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_camera_info", headers=header, timeout=1)            
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
            
    #         # If the response is 401 Unauthorized, refresh the token and retry once with the new token
    #         elif response.status_code == 401:
    #             self.__update_access_token()
    #             header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}  # Update the header with the new token                
    #             response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_camera_info", headers=header, timeout=1)
    #             if response.status_code == 200:
    #                 return [True, response.status_code, response.json()]
    #             else:
    #                 return [False, response.status_code, response.json()]
                
    #         # For other status codes, return the response as is
    #         else:
    #             return [False, response.status_code, response.json()]
        
    #     except Exception as e: # In case of an exception, return the exception details                        
    #         return [False, None, {"detail": str(e)}]

    # def fetch_all_rules(self):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:   
    #         response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_rules", headers=header, timeout=1)            
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
                        
    #         # If the response is 401 Unauthorized, refresh the token and retry once with the new token
    #         elif response.status_code == 401:
    #             self.__update_access_token()
    #             header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}  # Update the header with the new token                
    #             response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_rules", headers=header, timeout=1)  
    #             if response.status_code == 200:
    #                 return [True, response.status_code, response.json()]
    #             else:
    #                 return [False, response.status_code, response.json()]
                
    #         # For other status codes, return the response as is
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]

    # def update_count(self, camera_uuid:str=None, count_type:str = None, delta_count:int = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        
    #     try:
    #         payload = {'camera_uuid': camera_uuid, 'count_type': count_type, 'delta_count': delta_count}
    #         # Send a request to the server to update 'count_type' of 'camera_uuid' by 'delta_count'
    #         response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/update_count", headers=header, json=payload, timeout=1)            
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
            
    #         # If the response is 401 Unauthorized, refresh the token and retry once with the new token
    #         elif response.status_code == 401:
    #             self.__update_access_token()
    #             header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}  # Update the header with the new token                
    #             response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/update_count", headers=header, timeout=1)
    #             if response.status_code == 200:
    #                 return [True, response.status_code, response.json()]
    #             else:
    #                 return [False, response.status_code, response.json()]
                
    #         # For other status codes, return the response as is
    #         else:
    #             return [False, response.status_code, response.json()]        
            
    #     except Exception as e:        
    #         return [False, None, {"detail": str(e)}]                          

    # def update_shift_count(self, camera_uuid:str=None, shift_date_ddmmyyyy:str=None, shift_no:str=None, count_type:str = None, delta_count:int = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}

    #     try:
    #         payload = {'camera_uuid': camera_uuid, 'shift_date_ddmmyyyy': shift_date_ddmmyyyy, 'shift_no': shift_no, 'count_type': count_type, 'delta_count': delta_count}
    #         response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/update_shift_count", headers=header, json=payload, timeout=1)            
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
            
    #         # If the response is 401 Unauthorized, refresh the token and retry once with the new token
    #         elif response.status_code == 401:
    #             self.__update_access_token()
    #             header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}  # Update the header with the new token                
    #             response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/update_shift_count", headers=header, timeout=1)
    #             if response.status_code == 200:
    #                 return [True, response.status_code, response.json()]
    #             else:
    #                 return [False, response.status_code, response.json()]
                
    #         # For other status codes, return the response as is
    #         else:
    #             return [False, response.status_code, response.json()]        
            
    #     except Exception as e:        
    #         return [False, None, {"detail": str(e)}]

    # def create_reported_violation(self, camera_uuid:str=None, violation_frame:np.ndarray=None, violation_date_ddmmyyy_hhmmss:str=None, violation_type:str=None, violation_score:float=None, region_name:str=None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:
    #         # Convert the violation frame to a base64 string
    #         _, violation_frame_b64 = cv2.imencode('.jpg', violation_frame)  # Encode image as JPEG
    #         violation_frame_bytes = violation_frame_b64.tobytes()  # Convert to bytes
    #         violation_frame_b64 = base64.b64encode(violation_frame_bytes).decode('utf-8')  # Encode to base64 and convert to string
            
    #         payload = {'camera_uuid': camera_uuid, 'violation_frame_b64': violation_frame_b64, 'violation_date_ddmmyyy_hhmmss': violation_date_ddmmyyy_hhmmss, 'violation_type': violation_type, 'violation_score': violation_score, 'region_name': region_name}
    #         response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/create_reported_violation", headers=header, json=payload, timeout=1)            
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
            
    #         # If the response is 401 Unauthorized, refresh the token and retry once with the new token
    #         elif response.status_code == 401:
    #             self.__update_access_token()
    #             header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}  # Update the header with the new token                
    #             response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/create_reported_violation", headers=header, timeout=1)
    #             if response.status_code == 200:
    #                 return [True, response.status_code, response.json()]
    #             else:
    #                 return [False, response.status_code, response.json()]
                
    #         # For other status codes, return the response as is
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:        
    #         return [False, None, {"detail": str(e)}]
        
    # def update_camera_last_frame_api(self, camera_uuid:str=None, is_violation_detected:bool=None, is_person_detected:bool=None, frame:np.ndarray=None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:
    #         succes, frame_jpg = cv2.imencode('.jpg', frame)  # Encode image as JPEG
    #         base64_encoded_image = base64.b64encode(frame_jpg.tobytes()).decode('utf-8') # Encode to base64 and convert to string

    #         payload = {'camera_uuid': camera_uuid, 'is_violation_detected': is_violation_detected, 'is_person_detected': is_person_detected, 'base64_encoded_image': base64_encoded_image}
    #         response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/update_camera_last_frame", headers=header, json=payload, timeout=1)            
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
            
    #         # If the response is 401 Unauthorized, refresh the token and retry once with the new token
    #         elif response.status_code == 401:
    #             self.__update_access_token()
    #             header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}  # Update the header with the new token                
    #             response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/update_camera_last_frame", headers=header, timeout=1)
    #             if response.status_code == 200:
    #                 return [True, response.status_code, response.json()]
    #             else:
    #                 return [False, response.status_code, response.json()]
                
    #         # For other status codes, return the response as is
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:        
    #         return [False, None, {"detail": str(e)}]
                  

