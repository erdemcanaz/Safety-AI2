# Built-in imports
import pprint, time, sys, os

# Local imports
project_directory = os.path.dirname(os.path.abspath(__file__))
modules_directory = os.path.join(project_directory, 'modules')
sys.path.append(modules_directory) # Add the modules directory to the system path so that imports work

import camera_module
import evaluation_module

stream_manager = camera_module.StreamManager()
stream_manager.start_cameras_by_uuid(camera_uuids = []) # Start all cameras

#evaluation_manager = evaluation_module.EvaluationManager(yolo_models_to_be_used = stream_manager.return_yolo_models_to_use())
evaluation_manager = evaluation_module.EvaluationManager(yolo_models_to_be_used = ["yolov8n-pose"])

while True:
    stream_manager.optimize_camera_fetching_delays()        
    stream_manager.test_show_all_frames(window_size=(1280, 720))

    evaluated_uuids, evaluation_results = evaluation_manager.evaluate_frames_info(frames_info = stream_manager.return_all_not_evaluated_frames_info())
    stream_manager.update_frame_evaluations(evaluated_frame_uuids = evaluated_uuids)
    