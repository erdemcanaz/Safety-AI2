import json
import pyperclip
import uuid

ips = [
  
]

template =   {       "is_alive": True,
            "camera_uuid": str(uuid.uuid4()),
            "camera_region": "",
            "camera_description": "",
            "NVR_ip": "",
            "username": "",
            "password": "",
            "camera_ip_address": None,
            "stream_path": "profile2/media.smp",
            "active_rules": [
                {
                    "rule_name": "RESTRICTED_AREA",
                    "evaluation_method": "ANKLE_INSIDE_POLYGON",
                    "trigger_score": "0.5",
                    "rule_uuid": str(uuid.uuid4()),
                    "related_departments": [
                        "ISG"
                    ],
                    "normalized_rule_area_polygon_corners": [
                        
                    ]
                }
            ]
        }

str = ""
for ip in ips:
    template["camera_ip_address"] = ip
    str += json.dumps(template, indent=4) +",\n"

pyperclip.copy(str)



