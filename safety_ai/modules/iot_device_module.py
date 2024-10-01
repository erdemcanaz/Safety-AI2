import safety_ai_api_dealer_module
from typing import List, Dict
import time, pprint

class IoTDevicemanager:
    #TODO: add serial communication with the iot devices

    def __init__(self, api_dealer:safety_ai_api_dealer_module.SafetyAIApiDealer):
        self.api_dealer = api_dealer
        self.iot_devices = {} # key: iot_device_uuid | device_name (str),  device_id (str), linked_rule_uuids (List[str])
        self.last_time_iot_devices_updated = 0
        pass

    def update_iot_devices(self, update_interval_seconds:float = 60):
        if time.time() - self.last_time_iot_devices_updated < update_interval_seconds: return
        self.last_time_iot_devices_updated = time.time()

        response = self.api_dealer.fetch_all_iot_devices()
        if response[0] == True:
            self.iot_devices = response[2]
            pprint.pprint(self.iot_devices)
        else:
            print(f"Error: {response[1]}")
        



