import requests, json

url = input("Enter the URL: ")
token = input("Enter the token: ")

body = {

    "SafetyData": [
        {

            "RelatedShiftDate": "08.07.2024 11:11",

            "RelatedShiftNo": "1",

            "DeviceTimestamp": "08.07.2024 11:11",

            "Image": "",

            "RegionName": "gg",

            "ViolationType": "restricted_area_rule_statistics",

            "ViolationScore": "36",

            "ViolationUID": "DENEME",

            "CameraUID": "DENEME" 

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
