import requests
import json, pprint
import jwt

import PREFERENCES

class SafetyAIApiDealer():
    def __init__(self):
        self.SERVER_IP_ADDRESS = PREFERENCES.SERVER_IP_ADDRESS   
        self.USERNAME = PREFERENCES.SAFETY_AI_USER_INFO['username']
        self.PASSWORD = PREFERENCES.SAFETY_AI_USER_INFO['password']
        self.JWT_TOKEN = None
        self.DECODED_TOKEN = None
        self.PERSONAL_FULLNAME = ""

    def __update_access_token(self) -> bool: #AKA login
        # Ensure that both username and password are provided
        payload = {'username': self.USERNAME, 'password': self.PASSWORD}
        try:
            response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/token", data=payload, timeout=1)
            if response.status_code == 200:
                self.JWT_TOKEN = response.json()['access_token']
                self.DECODED_TOKEN = jwt.decode(self.JWT_TOKEN, options={"verify_signature": False}, algorithms=["HS256"])              
                self.PERSONAL_FULLNAME = self.DECODED_TOKEN['personal_fullname']
                return [True, response.status_code, response.json()]
            else:
                return [False, response.status_code, response.json()]
        except Exception as e:
            return [False, None, {"detail": str(e)}]
                
    def fetch_all_camera_info(self):
        header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}
        
        try:
            # Send a request to the server to fetch all camera info
            response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_camera_info", headers=header, timeout=1)            
            if response.status_code == 200:
                return [True, response.status_code, response.json()]
            
            # If the response is 401 Unauthorized, refresh the token and retry once with the new token
            elif response.status_code == 401:
                self.__update_access_token()
                header = {'Authorization': f'Bearer {self.JWT_TOKEN}'}  # Update the header with the new token                
                response = requests.get(f"http://{self.SERVER_IP_ADDRESS}/fetch_all_camera_info", headers=header, timeout=1)
                if response.status_code == 200:
                    return [True, response.status_code, response.json()]
                else:
                    return [False, response.status_code, response.json()]
                
            # For other status codes, return the response as is
            else:
                return [False, response.status_code, response.json()]
        
        except Exception as e: # In case of an exception, return the exception details                        
            return [False, None, {"detail": str(e)}]
                                        
            





