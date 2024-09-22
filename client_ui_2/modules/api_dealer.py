#NOTE: honestly, using decorators for retrying the request is way better than the current implementation.
# But I am too lazy to change it now.

import requests
import json, pprint
import jwt
import time
import functools

class ApiDealer():
    def __init__(self, server_ip_address):
        self.SERVER_IP_ADDRESS = server_ip_address   
        self.USERNAME = None
        self.PERSONAL_FULLNAME = None
        self.PASSWORD = None
        self.JWT_TOKEN = None
        self.DECODED_TOKEN = None

    def get_access_token(self, username: str = None, plain_password: str = None) -> bool: #AKA login
        # Ensure that both username and password are provided
        try:
            payload = {'username': username, 'password': plain_password}
            response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/token", data=payload, timeout=1)
            if response.status_code == 200:
                self.JWT_TOKEN = response.json()['access_token']
                self.DECODED_TOKEN = jwt.decode(self.JWT_TOKEN, options={"verify_signature": False}, algorithms=["HS256"])
                self.USERNAME = username
                self.PASSWORD = plain_password
                self.PERSONAL_FULLNAME = self.DECODED_TOKEN['personal_fullname']
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]

    def get_authorizations(self):
        """
        Returns a list of authorizations that the user has.
        The list is in the following format if successful:
        [
            True,
            detail:str,
            [{'authorization_uuid': '5b9...', 'authorization_name': 'ADMIN_PRIVILEGES'}, ...]
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
                payload = {'user_uuid': self.DECODED_TOKEN['user_uuid']}
                response = requests.post(
                    f"http://{self.SERVER_IP_ADDRESS}/fetch_user_authorizations_by_user_uuid", 
                    headers = header, 
                    timeout = 2, 
                    json = payload
                )          
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data' 
                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']['user_authorizations']]
                else:
                    return [False, response_body['detail'], []]
            except Exception as e:
                return [False , str(e), []]
                    
        result = request_to_try()
        if result[0]: return result
        print(f"Refreshing token and retrying once more... {self.get_authorizations.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)
        return request_to_try()

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
    
    def create_camera_info(self, camera_ip_address:str = None, username:str = None, password:str = None, camera_status:str = None, camera_region:str = None):
        
        """
            Returns a list of all camera info.
            The list is in the following format if successful:
            [
                True,
                detail:str,
                {
                    'camera_uuid': '6b19ab80-0337-49b7-a87f-e5c36b3aed58', 
                    'camera_ip_address': '6.7.6.8', 'camera_region': 'adqwd',
                    'camera_description': 'No description provided.', 
                    'username': 'gqw', 
                    'password': 'awd', 
                    'stream_path': 'profile2/media.smp', 
                    'camera_status': 'active'
                }
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
                payload = {
                    "camera_ip_address": camera_ip_address,
                    "username": username,
                    "password": password,
                    "stream_path": "profile2/media.smp",
                    "camera_region": camera_region,
                    "camera_status": camera_status if camera_status is not None else "inactive",
                    "camera_description": "No description provided."
                }
                response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/create_camera_info", headers=header, json=payload, timeout=1)
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data'                     

                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']]
                else:
                    return [False, response_body['detail'], []]

            except Exception as e:
                return [False , str(e), []]
            
  
        result = request_to_try()
        if result[0]: return result            
        print(f"Refreshing token and retrying once more... {self.create_camera_info.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)    
        return request_to_try()

    def get_last_camera_frame_by_camera_uuid(self, camera_uuid:str = None):
        """
        """
        def request_to_try():
            try:
                header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
                payload = { 'camera_uuid': camera_uuid}                    
                response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/fetch_last_camera_frame_info", headers=header, json=payload, timeout=1)
                response_body = response.json() # dict | 'status', 'is_task_successful', 'detail', 'json_data'                     

                if response_body['is_task_successful']:                
                    return [True,  response_body['detail'] , response_body['json_data']]
                else:
                    return [False, response_body['detail'], []]

            except Exception as e:
                return [False , str(e), []]

        result = request_to_try()
        if result[0]: return result            
        print(f"Refreshing token and retrying once more... {self.get_last_camera_frame_by_camera_uuid.__name__}")
        self.get_access_token(self.USERNAME, self.PASSWORD)
        return request_to_try()


    # def create_user_api(self, username: str, password: str, personal_fullname: str) -> bool:
    #     payload = {'username': username, 'plain_password': password, 'personal_fullname': personal_fullname}
    #     try:
    #         response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/create_user", json=payload, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, -1, str(e), {"detail": str(e)}]

        

    # def update_camera_info_attribute(self, camera_uuid:str = None, attribute:str = None, value:str = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     payload = {}
    #     payload.update({'camera_uuid': camera_uuid})
    #     payload.update({'attribute': attribute})
    #     payload.update({'value': value})

    #     try:
    #         response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/update_camera_info_attribute", headers=header, json=payload, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]
        

    # def delete_camera_info_by_uuid(self, camera_uuid:str = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:
    #         response = requests.delete(f"http://{self.SERVER_IP_ADDRESS}/delete_camera_info_by_uuid/{camera_uuid}", headers=header, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]
        
    # def get_all_last_camera_frame_info_without_BLOB(self):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:
    #         response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/get_all_last_camera_frame_info_without_BLOB", headers=header, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]
    
    # def fetch_rules_by_camera_uuid(self, camera_uuid:str = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:
    #         response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_rules_by_camera_uuid/{camera_uuid}", headers=header, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]
        
    # def delete_rule_by_rule_uuid(self, rule_uuid:str = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:
    #         response = requests.delete(f"http://{self.SERVER_IP_ADDRESS}/delete_rule_by_rule_uuid/{rule_uuid}", headers=header, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]
    
    # def create_rule_for_camera(self, camera_uuid:str = None, rule_department:str = None, rule_type:str = None, evaluation_method:str = None, threshold_value:float = None, rule_polygon:str = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     payload = {}
    #     payload.update({'camera_uuid': camera_uuid})
    #     payload.update({'rule_department': rule_department})
    #     payload.update({'rule_type': rule_type})
    #     payload.update({'evaluation_method': evaluation_method})
    #     payload.update({'threshold_value': float(threshold_value)})
    #     payload.update({'rule_polygon': rule_polygon})

    #     try:
    #         response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/create_rule", headers=header, json=payload, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]
        
    # def fetch_reported_violations_between_dates(self, start_date_ddmmyyyy:str = None, end_date_ddmmyyyy:str = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     start_date_ddmmyyyy = "1.1.1970" if start_date_ddmmyyyy is None or start_date_ddmmyyyy == "" else start_date_ddmmyyyy
    #     end_date_ddmmyyyy = "1.1.2099" if end_date_ddmmyyyy is None or end_date_ddmmyyyy == "" else end_date_ddmmyyyy
    #     try:
    #         response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_reported_violations_between_dates?start_date={start_date_ddmmyyyy}&end_date={end_date_ddmmyyyy}", headers=header, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]
        
    # def get_encrypted_image_by_uuid(self, image_uuid:str = None):
    #     header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
    #     try:
    #         response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/get_encrypted_image_by_uuid?image_uuid={image_uuid}", headers=header, timeout=1)
    #         if response.status_code == 200:
    #             return [True, response.status_code, response.json()]
    #         else:
    #             return [False, response.status_code, response.json()]
    #     except Exception as e:
    #         return [False, None, {"detail": str(e)}]




