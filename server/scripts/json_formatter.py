from typing import Dict, List
import json, pprint

json_path = input("Enter the path of the JSON file: ")
with open(json_path, "r") as f:
    cameras_old_data: Dict[str, Dict[str, str]] = json.load(f)["cameras"]

for old_data in cameras_old_data:  
    struct_dict = {}
    
    print(struct_dict, ",")


