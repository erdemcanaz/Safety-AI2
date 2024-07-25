# Built-in imports
import pprint, time
# Local imports
import modules.camera_module as camera_module

stream_manager = camera_module.StreamManager()
stream_manager.start_cameras_by_uuid(camera_uuids = []) # Start all cameras

while True:
    stream_manager.optimize_camera_fetching_delays()        
    stream_manager.test_show_all_frames(window_size=(1280, 720))

    not_evaluated_frames_info = stream_manager.return_all_not_evaluated_frames_info()
    
    uuids = []
    for frame_info in not_evaluated_frames_info:
        uuids.append(frame_info["frame_uuid"])
        time.sleep(0.25)

    stream_manager.update_frame_evaluations(evaluated_frame_uuids = uuids)

    if len(not_evaluated_frames_info) > 0:
        print("Not evaluated frames:", len(not_evaluated_frames_info))  
