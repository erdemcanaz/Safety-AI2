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
import safety_ai_api_dealer
import camera_module
#================================================================================================================================================================
api_dealer = safety_ai_api_dealer.SafetyAIApiDealer()
stream_manager = camera_module.StreamManager(api_dealer=api_dealer)
#her X'dk da bir kamera eklenip çıkarıldı mı kontrol denemesi yapılacak
#her X'dk da bir kamera kuralları değişti mi kontrol denemesi yapılacak

while True:
    stream_manager.update_cameras(update_interval_seconds = 5)



#================================================================================================================================================================
# import server_preferences
# import camera_module 
# import evaluation_module

# stream_manager = camera_module.StreamManager()
# stream_manager.start_cameras_by_uuid(camera_uuids = []) # Start all cameras

# evaluation_manager = evaluation_module.EvaluationManager()

# average_evaluation_time = 0
# while True:
#     evaluations_started_time = time.time()

#     # ================== EVALUATION ==================
#     all_frame_infos = stream_manager.return_all_recent_frames_info_as_list()    # Get all frames from the cameras
#     evaluation_manager.evaluate_frames_info(all_frame_infos)                    # Evaluate the frames
#     # ================================================

#     average_evaluation_time = (1 - server_preferences.PARAM_EVALUATION_TIME_UPDATE_FACTOR) * average_evaluation_time + server_preferences.PARAM_EVALUATION_TIME_UPDATE_FACTOR*( time.time() - evaluations_started_time )
#     total_duration = average_evaluation_time / (1-server_preferences.PARAM_SLEEP_DURATION_PERCENTAGE)
#     sleep_duration = min(total_duration * server_preferences.PARAM_SLEEP_DURATION_PERCENTAGE, server_preferences.PARAM_MAX_SLEEP_DURATION)
#     server_preferences.PARAM_MINIMUM_DECODING_DELAY = sleep_duration # The minimum decoding delay is set to the sleep duration since the server will sleep for this duration and it will not be able to evaluate frames more frequently than this duration
#     if sleep_duration > 0:
#         print(f"average_evaluation_time: {average_evaluation_time:.2f}, sleep_duration: {sleep_duration:.2f}")
#         time.sleep(sleep_duration)


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

  

    