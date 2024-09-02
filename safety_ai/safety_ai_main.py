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

def update_server_last_frames(recent_frames):
    global last_time_server_last_frame_updated
    if time.time() - last_time_server_last_frame_updated < 300: return
    last_time_server_last_frame_updated = time.time()

    for frame_info in recent_frames:
        #def update_camera_last_frame_api(self, camera_uuid:str=None, is_violation_detected:bool=None, is_person_detected:bool=None, base64_encoded_image:str=None):
        camera_uuid = frame_info["camera_uuid"]
        is_violation_detected = False
        is_person_detected = False
        frame = frame_info["cv2_frame"]
        
        result = api_dealer.update_camera_last_frame_api(camera_uuid=camera_uuid, is_violation_detected=is_violation_detected, is_person_detected=is_person_detected, frame=frame)
        print(f"update_server_last_frames: {result}")

while True:
    stream_manager._StreamManager__test_show_all_frames()
    stream_manager.update_cameras(update_interval_seconds = PREFERENCES.CAMERA_UPDATE_INTERVAL_SECONDS) #stops and restarts the cameras if new, updated or deleted cameras are detected
    stream_manager.update_camera_rules(update_interval_seconds = PREFERENCES.CAMERA_RULES_UPDATE_INTERVAL_SECONDS) # updates the rules for each camera no matter what.
    recent_frames = stream_manager.return_all_recent_frames_info_as_list() # last decoded frame from each camera 
    
    update_server_last_frames(recent_frames)

    evaluation_results = []
    for frame_info in recent_frames:
        r = frame_evaluator.evaluate_frame(frame_info)
        if r is not None: evaluation_results.append(r)

    for evaluation_result in evaluation_results:
        for violation_result in evaluation_result["violation_results"]:
            camera_uuid = evaluation_result['frame_info']['camera_uuid']
            if camera_uuid not in best_violations_wrt_camera: best_violations_wrt_camera[camera_uuid] = violation_result
            elif violation_result['violation_score'] > best_violations_wrt_camera[camera_uuid]['violation_score']: best_violations_wrt_camera[camera_uuid] = violation_result

    if time.time() - last_time_violations_reported > 20:
        last_time_violations_reported = time.time()
        for camera_uuid, violation_result in best_violations_wrt_camera.items():
            print(f"Reporting violation for camera_uuid: {camera_uuid}")
            # camera_uuid:str=None, violation_frame:np.ndarray=None, violation_date_ddmmyyy_hhmmss:str=None, violation_type:str=None, violation_score:float=None, region_name:str=None):
            camera_uuid = violation_result['camera_uuid']
            violation_date_ddmmyyy_hhmmss = violation_result['violation_date_ddmmyyy_hhmmss']
            violation_type = violation_result['violation_type']
            violation_score = float(violation_result['violation_score'])
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
    
    if len(evaluation_results) > 0: print(f"len(evaluation_results): {len(evaluation_results)}")

def test_api_functionality():
    api_dealer = safety_ai_api_dealer.SafetyAIApiDealer()

    r = api_dealer.fetch_all_camera_info()
    pprint.pprint(r)
    camera_uuid = r[2]['camera_info'][0]['camera_uuid']

    r = api_dealer.update_count(camera_uuid=camera_uuid, count_type="TRIAL", delta_count=1)
    pprint.pprint(r)

    shift_date = datetime.datetime.now().strftime("%d.%m.%Y")
    r = api_dealer.update_shift_count(camera_uuid=camera_uuid, shift_date_ddmmyyyy=shift_date, shift_no="0", count_type="TRIAL", delta_count=1)
    pprint.pprint(r)

    width, height = 1920, 1080
    random_frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    text = f"Violation: ({width}x{height}) | {'.jpg'}"
    text_width, text_height = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 1)[0]
    text_x = (random_frame.shape[1] - text_width) // 2
    text_y = (random_frame.shape[0] + text_height) // 2
    cv2.putText(random_frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 1, cv2.LINE_AA)


    r = api_dealer.create_reported_violation(camera_uuid=camera_uuid, violation_frame=random_frame, violation_date_ddmmyyy_hhmmss=datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), violation_type="TRIAL_VIOLATION", violation_score=random.uniform(0,1)*100, region_name=random.choice(["Region 1", "Region 2", "Region 3"]))
    pprint.pprint(r)

  

    