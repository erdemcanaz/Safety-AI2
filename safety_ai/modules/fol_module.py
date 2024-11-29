import requests, json, uuid, datetime, time, pprint, PREFERENCES

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
            region_name:str = None,
            image_base64:str = None,
            cooldown:float = None,
            violation_type:str = None       

        ):

        if time.time() - self.last_time_sent < cooldown:
            return 
        self.last_time_sent = time.time()

        if violation_type not in PREFERENCES.DEFINED_RULE_FOL_MAPPING.keys():
            raise ValueError(f"Violation type {violation_type} not defined in PREFERENCES.DEFINED_RULE_FOL_MAPPING")
        fol_mapped_violation_type = PREFERENCES.DEFINED_RULE_FOL_MAPPING[violation_type]

        headers = {
            "Content-Type": "application/json",
            "token": f"{self.token}"
            ""
        }

        hour = datetime.datetime.now().hour
        shift_no = hour // 8 + 1

        if region_name is None:
            region_name = "SHE-matters-None"
        if type(region_name) == str and len(region_name) == 0:
            region_name = "SHE-matters-empty"

        body = {
            "SafetyData": [
                {

                    "RelatedShiftDate": str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")),

                    "RelatedShiftNo": str(shift_no),

                    "DeviceTimestamp": str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")),

                    "RegionName": region_name,

                    "ViolationType": fol_mapped_violation_type,

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
