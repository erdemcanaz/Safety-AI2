import requests


url = input("Enter the URL: ")
token = input("Enter the token: ")
enter_data = input("Enter the data: ")

body = {

    "SafetyData": [

        {

            "RelatedShiftDate": "08.07.2024 11:11",

            "RelatedShiftNo": "1",

            "DeviceTimestamp": "08.07.2024 11:11",

            "Image": "",

            "RegionName": "DENEME",

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

response = requests.post(url, headers = headers, data=body)
print(response.status_code)
print(response.text)
