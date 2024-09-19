import requests, json, uuid

url = input("Enter the URL: ")
token = input("Enter the token: ")

body = {

    "SafetyData": [
        {

            "RelatedShiftDate": "15.08.2024 16:15",

            "RelatedShiftNo": "3",

            "DeviceTimestamp": "15.08.2024 11:11",

            "RegionName": "SHE-matters",

            "ViolationType": "restricted_area_rule_statistics",

            "ViolationScore": "36",

            "ViolationUID": str(uuid.uuid4()),

            "CameraUID": str(uuid.uuid4()), 

            "Image": "",
        }
    ]
}

headers = {
    "Content-Type": "application/json",
    "token": f"{token}"
}

response = requests.post(url, headers = headers, data=json.dumps(body))
print(response.status_code)
print(response.text)
