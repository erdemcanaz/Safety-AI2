import requests, json, uuid, datetime, time, pprint

class FolModule:
    def __init__(self):
        self.end_point_url = "http://172.17.24.2:56189/Services/FolInboundService.svc/json/SendSafetyAI"
        self.token = input("Enter the token for FOL: ")
        self.last_time_sent = 0

        pass

    def send_data(self, 
            violation_score:float = None,
            violation_uuid:str = None,
            camera_uuid:str = None, 
            image_base64:str = None,
            cooldown:float = None              

        ):

        if time.time() - self.last_time_sent < cooldown:
            return 
        self.last_time_sent = time.time()

        headers = {
            "Content-Type": "application/json",
            "token": f"{self.token}"
            ""
        }

        hour = datetime.datetime.now().hour
        shift_no = hour // 8 + 1

        body = {
            "SafetyData": [
                {

                    "RelatedShiftDate": str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")),

                    "RelatedShiftNo": str(shift_no),

                    "DeviceTimestamp": str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")),

                    "RegionName": "SHE-matters-1",

                    "ViolationType": "restricted_area_rule_statistics",

                    "ViolationScore": str(violation_score),

                    "ViolationUID": violation_uuid,

                    "CameraUID": camera_uuid, 

                    "Image": image_base64,
                }
            ]
        }


        response = requests.post(self.end_point_url, headers = headers, data=json.dumps(body))
        #remove Image from body before printing
        body["SafetyData"][0].pop("Image")
        pprint.pprint(body)
        pprint.pprint(response)
        return response.status_code, response.text
