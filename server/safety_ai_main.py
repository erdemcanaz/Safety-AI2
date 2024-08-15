# Built-in imports
import pprint, time, sys, os, cv2

# Local imports
project_directory = os.path.dirname(os.path.abspath(__file__))
modules_directory = os.path.join(project_directory, 'modules')
sys.path.append(modules_directory) # Add the modules directory to the system path so that imports work

import server_preferences
import camera_module 
import evaluation_module

stream_manager = camera_module.StreamManager()
stream_manager.start_cameras_by_uuid(camera_uuids = []) # Start all cameras

evaluation_manager = evaluation_module.EvaluationManager()

average_evaluation_time = 0
while True:

    all_frame_infos = stream_manager.return_all_recent_frames_info_as_list()

    evaluations_started_time = time.time()
    evaluation_manager.evaluate_frames_info(all_frame_infos)
    average_evaluation_time = (1 - server_preferences.PARAM_EVALUATION_TIME_UPDATE_FACTOR) * average_evaluation_time + server_preferences.PARAM_EVALUATION_TIME_UPDATE_FACTOR*( time.time() - evaluations_started_time )

    total_duration = average_evaluation_time / (1-server_preferences.PARAM_SLEEP_DURATION_PERCENTAGE)
    sleep_duration = min(total_duration * server_preferences.PARAM_SLEEP_DURATION_PERCENTAGE, server_preferences.PARAM_MAX_SLEEP_DURATION)
    server_preferences.PARAM_MINIMUM_DECODING_DELAY = sleep_duration
    
    print(f"average_evaluation_time: {average_evaluation_time:.2f}, sleep_duration: {sleep_duration:.2f}")
    if sleep_duration > 0:
           time.sleep(sleep_duration)



  

    