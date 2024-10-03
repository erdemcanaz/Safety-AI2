# Built-in imports
import pprint, time, sys, os, cv2, datetime, random
from pathlib import Path
import numpy as np

# Local imports
SAFETY_AI_DIRECTORY = Path(__file__).resolve().parent
MODULES_DIRECTORY = SAFETY_AI_DIRECTORY / "modules"

SAFETY_AI2_DIRECTORY = SAFETY_AI_DIRECTORY.parent
print(f"API_SERVER_DIRECTORY: {SAFETY_AI_DIRECTORY}")
print(f"MODULES_DIRECTORY: {MODULES_DIRECTORY}")
print(f"SAFETY_AI2_DIRECTORY: {SAFETY_AI2_DIRECTORY}")

sys.path.append(str(MODULES_DIRECTORY)) # Add the modules directory to the system path so that imports work
sys.path.append(str(SAFETY_AI2_DIRECTORY)) # Add the modules directory to the system path so that imports work

import PREFERENCES
import safety_ai_api_dealer_module, camera_module, models_module, frame_evaluator_module, iot_device_module

#================================================================================================================================================================
api_dealer = safety_ai_api_dealer_module.SafetyAIApiDealer()
stream_manager = camera_module.StreamManager(api_dealer=api_dealer)
iot_device_manager = iot_device_module.IoTDevicemanager(api_dealer=api_dealer)
frame_evaluator = frame_evaluator_module.FrameEvaluator()

last_time_server_last_frame_updated = 0
last_time_camera_violation_is_reported = {} # key: camera_uuid | value: time.time()

last_frames_for_timelapse = {} # key: camera_uuid | pop <-[frame0 (oldest), frame1, frame2, frame3, frame4 (newest)] <- insert
while True:
    #(1) Update the cameras and the rules for each camera
    #(2) Get all the recent frames from the cameras
    #(3) Evaluate the recent frames (same frame is not evaluated twice)
    #(4) Update the server with the last frames (check if violation is detected or not)
    #(5) Update the counts for each camera (to be used for statistics)
    #(6) Report violations for each camera (if any) to the local-server and the fol-server if coolddown time is passed
    #(7) Trigger rules
    #(8) TODO: send signal to iot devices if violation is detected for respective cameras
    #() TODO: change active cameras to next batch of cameras if the time is up

    if PREFERENCES.SHOW_FRAMES['show_all_frames']: stream_manager.show_all_frames()
    
    #(1) Update the cameras and the rules for each camera
    stream_manager.update_cameras(update_interval_seconds = PREFERENCES.CAMERA_UPDATE_INTERVAL_SECONDS) #stops and restarts the cameras if new, updated or deleted cameras are detected
    stream_manager.update_camera_rules(update_interval_seconds = PREFERENCES.CAMERA_RULES_UPDATE_INTERVAL_SECONDS) # updates the rules for each camera no matter what.
    iot_device_manager.update_iot_devices(update_interval_seconds = PREFERENCES.IOT_DEVICE_UPDATE_INTERVAL_SECONDS) # updates the iot devices

    #(2) Get all the recent frames from the cameras
    recent_frames = stream_manager.return_all_recent_frames_info_as_list() # last decoded frame from each camera 
    
    #(3) Evaluate the recent frames (same frame is not evaluated twice)
    evaluation_results = []
    for frame_info in recent_frames:
        r = frame_evaluator.evaluate_frame(frame_info) # Returns None if the frame is already evaluated
        if r is not None: evaluation_results.append(r)

    #(4) Update the server with the last frames (check if violation is detected or not). Note that all the frames in the evaluation_results are new frames, so we can update the server with them
    for evaluation_result in evaluation_results:
        camera_uuid = evaluation_result['frame_info']['camera_uuid']
        is_violation_detected = True if len(evaluation_result['violation_reports']) > 0 else False
        is_person_detected = True if evaluation_result['number_of_people_detected'] > 0 else False
        frame = evaluation_result['processed_cv2_frame']
        api_dealer.update_last_camera_frame_as(camera_uuid=camera_uuid, is_violation_detected=is_violation_detected, is_person_detected=is_person_detected, frame=frame)

        if camera_uuid in last_frames_for_timelapse:
            last_frames_for_timelapse[camera_uuid].append(frame)
            if len(last_frames_for_timelapse[camera_uuid]) > 5: last_frames_for_timelapse[camera_uuid].pop(0)    
        else:
            last_frames_for_timelapse[camera_uuid] = [frame]
        
    #(5) Update the counts for each camera (to be used for statistics)
    for evaluation_result in evaluation_results:
        # All time statistics
        # key: camera_uuid | subkey:evaluated_frame_count
        # key: camera_uuid | subkey:number_of_people_detected_count
        # key: camera_uuid | subkey:detected_hardhat_count
        # key: camera_uuid | subkey:detected_restricted_area_count
        # key: camera_uuid | subkey:check_person_count
        
        # Hourly statistics
        # key: camera_uuid | subkey:evaluated_frame_count_yyyy_mm_dd_hh
        # key: camera_uuid | subkey:number_of_people_detected_count_yyyy_mm_dd_hh
        # key: camera_uuid | subkey:detected_hardhat_count_yyyy_mm_dd_hh
        # key: camera_uuid | subkey:detected_restricted_area_count_yyyy_mm_dd_hh
        # key: camera_uuid | subkey:check_person_count_yyyy_mm_dd_hh

        camera_uuid = evaluation_result['frame_info']['camera_uuid']
        number_of_people_detected = evaluation_result['number_of_people_detected']
        timestamp_str = datetime.datetime.now().strftime("%Y_%m_%d_%H")

        # update detected_people_count
        api_dealer.update_count(count_key= camera_uuid, count_subkey="detected_people_count", delta_count=number_of_people_detected)
        api_dealer.update_count(count_key= camera_uuid, count_subkey=f"detected_people_count_{timestamp_str}", delta_count=number_of_people_detected)

        # update evaluated_frame_count
        api_dealer.update_count(count_key= camera_uuid, count_subkey="evaluated_frame_count", delta_count=1)
        api_dealer.update_count(count_key= camera_uuid, count_subkey=f"evaluated_frame_count_{timestamp_str}", delta_count=1)

        for violation_report in evaluation_result['violation_reports']:
            camera_uuid = evaluation_result['frame_info']['camera_uuid']
            violation_type = violation_report['violation_type']
            violation_score = violation_report['violation_score']
            threshold_value = violation_report['threshold_value']
            if violation_score < threshold_value: continue
            #    def update_count(self, count_key:str=None, count_subkey:str=None, delta_count:float = None):           
            if violation_type == "hardhat_violation":
                api_dealer.update_count(count_key= camera_uuid, count_subkey="detected_hardhat_count", delta_count=1)
                api_dealer.update_count(count_key= camera_uuid, count_subkey=f"detected_hardhat_count_{timestamp_str}", delta_count=1)
            elif violation_type == "restricted_area_violation":
                api_dealer.update_count(count_key= camera_uuid, count_subkey="detected_restricted_area_count", delta_count=1)
                api_dealer.update_count(count_key= camera_uuid, count_subkey=f"detected_restricted_area_count_{timestamp_str}", delta_count=1)
            elif violation_type == "check_person":
                api_dealer.update_count(count_key= camera_uuid, count_subkey="check_person_count", delta_count=1)
                api_dealer.update_count(count_key= camera_uuid, count_subkey=f"check_person_count_{timestamp_str}", delta_count=1)

    #(6) Report the best violations for each camera (if any) to the local-server and the fol-server
    for evaluation_result in evaluation_results:
        for violation_report in evaluation_result['violation_reports']:
            camera_uuid = evaluation_result['frame_info']['camera_uuid']

            if camera_uuid not in last_time_camera_violation_is_reported: last_time_camera_violation_is_reported[camera_uuid] = 0
            if time.time() - last_time_camera_violation_is_reported[camera_uuid] < 60: continue # Report the violation every 60 seconds
            last_time_camera_violation_is_reported[camera_uuid] = time.time()

            violation_frame = evaluation_result['processed_cv2_frame']
            violation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            violation_type = violation_report['violation_type']
            violation_score = round( float(violation_report['violation_score']) , 2 )
            region_name = violation_report['region_name']

            # 
            if violation_score > violation_report['threshold_value']:
                number_of_previous_frames = len(last_frames_for_timelapse[camera_uuid])
                api_dealer.create_reported_violation(camera_uuid=camera_uuid, violation_frame=violation_frame, violation_date=violation_date, violation_type=violation_type, violation_score=violation_score, region_name=region_name)
                print(f"Reported violation for camera_uuid: {camera_uuid}")
            if violation_score > violation_report['fol_threshold_value']:
                pass #TODO: report the violation to the fol-server
                
    #(7) Trigger rules and send signals to the IoT devices if the linked rules are triggered
    for evaluation_result in evaluation_results:
        for violation_report in evaluation_result['violation_reports']:
            rule_uuid = violation_report['rule_uuid']
            api_dealer.trigger_rule(rule_uuid=rule_uuid)

    #(8) Ping IoT devices if their rules are triggered in recent 
    iot_device_manager.send_signal_to_iot_devices_if_rule_triggered_recently()
        
    
       

    