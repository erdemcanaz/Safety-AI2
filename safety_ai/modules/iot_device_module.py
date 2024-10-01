import safety_ai_api_dealer_module
from typing import List, Dict
import time, pprint

class IoTDevicemanager:
    #TODO: add serial communication with the iot devices

    def __init__(self, api_dealer:safety_ai_api_dealer_module.SafetyAIApiDealer):
        self.api_dealer = api_dealer
        self.iot_devices = {} # key: iot_device_uuid | device_uuid (str), device_name (str),  device_id (str), linked_rule_uuids_and_actions (List[str, str])
        self.last_time_iot_devices_updated = 0

        self.last_time_signal_sent_to_iot_devices = {} #  key: iot_device_uuid | value: time.time() to prevent sending signals to iot devices too frequently
        pass

    def update_iot_devices(self, update_interval_seconds:float = 60):
        if time.time() - self.last_time_iot_devices_updated < update_interval_seconds: return
        self.last_time_iot_devices_updated = time.time()

        # fetch all iot devices
        response = self.api_dealer.fetch_all_iot_devices()
        if response[0] == True:
            self.iot_devices = {}    
            for iot_device_dict in response[2]:
                iot_device_dict.update({'linked_rule_uuids_and_actions': []})
                self.iot_devices[iot_device_dict['device_uuid']] = iot_device_dict
        else:
            print("Error: ", response[1])

        # fetch all linked rules for each iot device
        response = self.api_dealer.fetch_all_iot_device_and_rule_relations()
        if response[0] == True:
            for relation_dict in response[2]:
                # relation_uuid, device_uuid, rule_uuid, which_action 
                device_uuid = relation_dict['device_uuid']
                rule_uuid = relation_dict['rule_uuid']
                which_action = relation_dict['which_action']
                if device_uuid in self.iot_devices:
                    self.iot_devices[device_uuid]['linked_rule_uuids_and_actions'].append([rule_uuid, which_action])
        else:
            print("Error: ", response[1])

    def send_signal_to_iot_devices_if_rule_triggered_recently(self):
        response = self.api_dealer.fetch_all_rules()
        pprint.pprint(response)
        pass

        
        



