# Built-in imports
import pprint, time, sys, os, cv2

# Local imports
project_directory = os.path.dirname(os.path.abspath(__file__))
modules_directory = os.path.join(project_directory, 'modules')
sys.path.append(modules_directory) # Add the modules directory to the system path so that imports work

import camera_module 

stream_manager = camera_module.StreamManager()
stream_manager.start_cameras_by_uuid(camera_uuids = []) # Start all cameras

while True:
    all_frame_infos = stream_manager.return_all_recent_frames_info_as_list()

    