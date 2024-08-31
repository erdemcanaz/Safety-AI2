import requests
import json, pprint
import jwt

class ApiDealer():
    def __init__(self, server_ip_address):
        self.SERVER_IP_ADDRESS = server_ip_address   
        self.USERNAME = None
        self.PERSONAL_FULLNAME = None
        self.PASSWORD = None
        self.JWT_TOKEN = None
        self.DECODED_TOKEN = None

    def create_user_api(self, username: str, password: str, personal_fullname: str) -> bool:
        payload = {'username': username, 'plain_password': password, 'personal_fullname': personal_fullname}
        try:
            response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/create_user", json=payload, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, -1, str(e), {"detail": str(e)}]

    def get_acces_token(self, username: str = None, plain_password: str = None) -> bool: #AKA login
        # Ensure that both username and password are provided
        payload = {'username': username, 'password': plain_password}
        try:
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
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/get_authorizations", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def fetch_all_camera_info(self):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_camera_info", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def create_camera_info(self, camera_ip_address:str = None, username:str = None, password:str = None, stream_path:str = None, camera_status:str = None, NVR_ip_address:str = None, camera_region:str = None, camera_description:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        payload = { }
        payload.update({'camera_ip_address': camera_ip_address})
        payload.update({'username': username})
        payload.update({'password': password})
        payload.update({'stream_path': stream_path if stream_path is not None else ""})
        payload.update({'camera_status': camera_status if camera_status is not None else "inactive"})
        if NVR_ip_address is not None: payload.update({'NVR_ip_address': NVR_ip_address})
        if camera_region is not None: payload.update({'camera_region': camera_region})
        if camera_description is not None: payload.update({'camera_description': camera_description})

        try:
            response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/create_camera_info", headers=header, json=payload, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def update_camera_info_attribute(self, camera_uuid:str = None, attribute:str = None, value:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        payload = {}
        payload.update({'camera_uuid': camera_uuid})
        payload.update({'attribute': attribute})
        payload.update({'value': value})

        try:
            response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/update_camera_info_attribute", headers=header, json=payload, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def get_last_camera_frame_by_camera_uuid(self, camera_uuid:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/get_last_camera_frame_by_camera_uuid/{camera_uuid}", headers=header, timeout=1)
            if response.status_code == 200:               
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def delete_camera_info_by_uuid(self, camera_uuid:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.delete(f"http://{self.SERVER_IP_ADDRESS}/delete_camera_info_by_uuid/{camera_uuid}", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def get_all_last_camera_frame_info_without_BLOB(self):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/get_all_last_camera_frame_info_without_BLOB", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
    
    def fetch_rules_by_camera_uuid(self, camera_uuid:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_rules_by_camera_uuid/{camera_uuid}", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def delete_rule_by_rule_uuid(self, rule_uuid:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.delete(f"http://{self.SERVER_IP_ADDRESS}/delete_rule_by_rule_uuid/{rule_uuid}", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
    
    def create_rule_for_camera(self, camera_uuid:str = None, rule_department:str = None, rule_type:str = None, evaluation_method:str = None, threshold_value:float = None, rule_polygon:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        payload = {}
        payload.update({'camera_uuid': camera_uuid})
        payload.update({'rule_department': rule_department})
        payload.update({'rule_type': rule_type})
        payload.update({'evaluation_method': evaluation_method})
        payload.update({'threshold_value': float(threshold_value)})
        payload.update({'rule_polygon': rule_polygon})

        try:
            response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/create_rule", headers=header, json=payload, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def fetch_reported_violations_between_dates(self, start_date_ddmmyyyy:str = None, end_date_ddmmyyyy:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        start_date_ddmmyyyy = "1.1.1970" if start_date_ddmmyyyy is None or start_date_ddmmyyyy == "" else start_date_ddmmyyyy
        end_date_ddmmyyyy = "1.1.2099" if end_date_ddmmyyyy is None or end_date_ddmmyyyy == "" else end_date_ddmmyyyy
        try:
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_reported_violations_between_dates?start_date={start_date_ddmmyyyy}&end_date={end_date_ddmmyyyy}", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
        
    def get_encrypted_image_by_uuid(self, image_uuid:str = None):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        try:
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/get_encrypted_image_by_uuid?image_uuid={image_uuid}", headers=header, timeout=1)
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]




