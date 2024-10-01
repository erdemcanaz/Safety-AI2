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
import safety_ai_api_dealer_module, camera_module, models_module, frame_evaluator_module

#================================================================================================================================================================
api_dealer = safety_ai_api_dealer_module.SafetyAIApiDealer()
stream_manager = camera_module.StreamManager(api_dealer=api_dealer)
frame_evaluator = frame_evaluator_module.FrameEvaluator()

last_time_server_last_frame_updated = 0
last_time_violations_reported = 0
best_violations_wrt_camera = {

}

while True:
    #(1) Update the cameras and the rules for each camera
    #(2) Get all the recent frames from the cameras
    #(3) Evaluate the recent frames (same frame is not evaluated twice)
    #(4) Update the server with the last frames (check if violation is detected or not)
    #(5) Update the counts for each camera (to be used for statistics)
    #(6) Report the best violations for each camera (if any) to the local-server
    #(7) Report the best violations for each camera (if any) to the fol-server 
    #(8) TODO: change active cameras to next batch of cameras if the time is up
    #(9) TODO: send signal to iotdevices if violation is detected for respective cameras

    if PREFERENCES.SHOW_FRAMES['show_all_frames']: stream_manager.show_all_frames()
    
    #(1) Update the cameras and the rules for each camera
    stream_manager.update_cameras(update_interval_seconds = PREFERENCES.CAMERA_UPDATE_INTERVAL_SECONDS) #stops and restarts the cameras if new, updated or deleted cameras are detected
    stream_manager.update_camera_rules(update_interval_seconds = PREFERENCES.CAMERA_RULES_UPDATE_INTERVAL_SECONDS) # updates the rules for each camera no matter what.
    
    #(2) Get all the recent frames from the cameras
    recent_frames = stream_manager.return_all_recent_frames_info_as_list() # last decoded frame from each camera 
    
    #(3) Evaluate the recent frames (same frame is not evaluated twice)
    evaluation_results = []
    for frame_info in recent_frames:
        r = frame_evaluator.evaluate_frame(frame_info) # Returns None if the frame is already evaluated
        if r is not None: evaluation_results.append(r)

    #(4) Update the server with the last frames (check if violation is detected or not)
    for evaluation_result in evaluation_results:
        camera_uuid = evaluation_result['frame_info']['camera_uuid']
        is_violation_detected = True if len(evaluation_result['violation_reports']) > 0 else False
        is_person_detected = True if evaluation_result['number_of_people_detected'] > 0 else False
        frame = evaluation_result['processed_cv2_frame']

        api_dealer.update_last_camera_frame_as(camera_uuid=camera_uuid, is_violation_detected=is_violation_detected, is_person_detected=is_person_detected, frame=frame)

    #() Trigger rules 
    for evaluation_result in evaluation_results:
        print(f"evaluation_result['violation_reports']: {evaluation_result['violation_reports']}")
        for violation_report in evaluation_result['violation_reports']:
            rule_uuid = violation_report['rule_uuid']
            print(f"Triggering rule_uuid: {rule_uuid}")
            response = api_dealer.trigger_rule(rule_uuid=rule_uuid)
            if response[0] == False:
                print(f"Error: {response[1]}")

    #(5) Update the counts for each camera (to be used for statistics)
    for evaluation_result in evaluation_results:
        # All time statistics
        # key: camera_uuid | subkey:detected_people_count
        # key: camera_uuid | subkey:detected_hardhat_count
        # key: camera_uuid | subkey:detected_restricted_area_count
        # key: camera_uuid | subkey:check_person_count
        
        # Hourly statistics
        # key: camera_uuid | subkey:detected_people_count_yyyy_mm_dd_hh
        # key: camera_uuid | subkey:detected_hardhat_count_yyyy_mm_dd_hh
        # key: camera_uuid | subkey:detected_restricted_area_count_yyyy_mm_dd_hh
        # key: camera_uuid | subkey:check_person_count_yyyy_mm_dd_hh

        #pprint.pprint(evaluation_result['violation_reports'])
        pass



    continue

    for evaluation_result in evaluation_results:
        for violation_result in evaluation_result["violation_results"]:
            camera_uuid = evaluation_result['frame_info']['camera_uuid']
            if camera_uuid not in best_violations_wrt_camera: best_violations_wrt_camera[camera_uuid] = violation_result
            elif violation_result['violation_score'] > best_violations_wrt_camera[camera_uuid]['violation_score']: best_violations_wrt_camera[camera_uuid] = violation_result

    continue
    if time.time() - last_time_violations_reported > 60:
        last_time_violations_reported = time.time()
        for camera_uuid, violation_result in best_violations_wrt_camera.items():
            print(f"Reporting violation for camera_uuid: {camera_uuid}")
            # camera_uuid:str=None, violation_frame:np.ndarray=None, violation_date_ddmmyyy_hhmmss:str=None, violation_type:str=None, violation_score:float=None, region_name:str=None):
            camera_uuid = violation_result['camera_uuid']
            violation_date_ddmmyyy_hhmmss = violation_result['violation_date_ddmmyyy_hhmmss']
            violation_type = violation_result['violation_type']
            violation_score = round( float(violation_result['violation_score']) , 2 )
            region_name = violation_result['region_name']
            violation_frame = violation_result['violation_frame']

            print(f"camera_uuid: {camera_uuid}, violation_date_ddmmyyy_hhmmss: {violation_date_ddmmyyy_hhmmss}, violation_type: {violation_type}, violation_score: {violation_score}, region_name: {region_name}")
            r = api_dealer.create_reported_violation(camera_uuid=camera_uuid, violation_frame=violation_frame, violation_date_ddmmyyy_hhmmss=violation_date_ddmmyyy_hhmmss, violation_type=violation_type, violation_score=violation_score, region_name=region_name)
            print(r)

        best_violations_wrt_camera = {} # Reset the best violations after reporting them. next time the best violations will be updated again.

        # violation_report_info= { # Will not be added to the evaluation_result if no violation is detected
        #     "camera_uuid": evaluation_result['frame_info']['camera_uuid'],
        #     "region_name": evaluation_result['frame_info']['region_name'],
        #     "violation_frame": None, # Will be added after the person blur is applied at the end of the evaluation, all rules share the same frame
        #     "violation_date_ddmmyyy_hhmmss": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        #     "violation_type": rule_info['rule_type'],
        #     "violation_score": None, # will be added if a violation is detected           
        # }    
    
    if len(evaluation_results) > 0: print(f"len(evaluation_results): {len(evaluation_results)}, remaining time: {60 - (time.time() - last_time_violations_reported):.2f} seconds")

  

    