# Built-in imports
import pprint, time, sys, os, cv2, datetime, random, uuid
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

#=========================================================================================
# OWERWRITING THE PREFERENCES FOR TESTING
import PREFERENCES
PREFERENCES.SAFETY_AI_VERBOSES = {
    'header_class_name_width': 20, # The width of the class name in the printed header
    "updating_camera_info": True,
    "camera_initialization": True,
    "CRUD_on_camera_info": True,
    "frame_fetching_starts": True,
    "frame_fetching_stops": True,
    "frame_decoded": False,
    "frame_decoding_failed": True,
    "error_raised_rtsp": True,
}

# Models module related parameters
PREFERENCES.MODELS_MODULE_VERBOSES = {
"pose_detection_model_verbose": True,
"hardhat_detection_model_verbose": True,
"forklift_detection_model_verbose": True,
}
#=========================================================================================

import safety_ai_api_dealer_module, camera_module, models_module, frame_evaluator_module

class CameraModuleTests:
    
    def __init__(self):
        self.stream_path = "profile2/media.smp"

    def init_secret_variables(self):
        print("\n#### Initializing the secret variables")
        
        self.defined_camera_ip_addresses = input("Enter the defined camera IP addresses separated by commas (i.e. x.x.x.x,y.y.y.y,z.z.z.z): ").split(",")
        self.username = input("Enter the camera username: ")
        self.password = input("Enter the camera password: ")

        for camera_ip_address in self.defined_camera_ip_addresses:
            camera_ip_address = camera_ip_address.strip()
            if not all(part.isdigit() and 0 <= int(part) <= 255 for part in camera_ip_address.split('.')):
                raise ValueError(f"Invalid IP address format for camera: {camera_ip_address}. Please ensure that each IP address is in the format XXX.XXX.XXX.XXX where x is a digit between 0-9")

        print(f"Number of defined cameras: {len(self.defined_camera_ip_addresses)}")
        print(f"Username: {self.username}")
        print(f"Password: {self.password}")

    def test_rtsp_fetch_frame_from_cameras(self):
        print("\n#### Testing the CameraStreamFetcher class with the defined camera IP addresses")

        test_result_dict = {} # camera_ip_address: {is_fetched_properly (bool), resolution (tuple)}
        counter = 0
        for camera_ip_address in self.defined_camera_ip_addresses: 
            
            test_result_dict[camera_ip_address] = {"is_fetched_properly": False, "resolution": (0,0), "test_duration": 0}
            cap = None # cv2 capture object to capture the frames from the camera rtsp stream

            start_time = time.time()
            try:
                url = f'rtsp://{self.username}:{self.password}@{camera_ip_address}/{self.stream_path}'
                cap = cv2.VideoCapture(url)
                buffer_size_in_frames = 1
                cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)

                ret, frame = cap.read()
                if ret:
                    test_result_dict[camera_ip_address]["is_fetched_properly"] = True
                    test_result_dict[camera_ip_address]["resolution"] = frame.shape[:2]                    
            except Exception as e:
                print(f"Error in fetching frames from {camera_ip_address}: {e}")
                continue            
            end_time = time.time()

            test_result_dict[camera_ip_address]["test_duration"] = end_time - start_time
            print(f"{counter:<4} | Camera IP: {camera_ip_address:<16} | Is fetched properly: {test_result_dict[camera_ip_address]['is_fetched_properly']} | Resolution: {str(test_result_dict[camera_ip_address]['resolution']):<16} | test_duration time: {test_result_dict[camera_ip_address]['test_duration']:.2f} seconds")
            if cap is not None: cap.release()

            counter += 1
    
        succesful_counter = 0
        for camera_ip_address, test_result in test_result_dict.items():
            if test_result['is_fetched_properly']: succesful_counter += 1
        print(f"Number of successful camera fetches: {succesful_counter}/{len(test_result_dict)}")

    def do_camera_module_tests(self):
        camera_module_tests = CameraModuleTests()
        camera_module_tests.init_secret_variables()

        # 1. Test the RTSP frame fetching from the cameras one by one
        is_test_rtsp_fetch_frame_from_cameras = input("Do you want to test the RTSP frame fetching from the cameras one by one? (y/n): ")
        if(is_test_rtsp_fetch_frame_from_cameras == 'y'): camera_module_tests.test_rtsp_fetch_frame_from_cameras()

        # 2. create camera stream fetchers
        camera_stream_fetchers = []
        for camera_no, camera_ip_address in enumerate(self.defined_camera_ip_addresses):
            camera_init_dict = {
                'camera_uuid': str(uuid.uuid4()),
                'camera_region': f'Test Region {camera_no}',
                'camera_description': f'Test Camera {camera_no}',
                'camera_status': 'active',
                'NVR_ip_address': '172.0.0.0',
                'camera_ip_address': camera_ip_address,
                'username': self.username,
                'password': self.password,
                'stream_path': self.stream_path
            }
        camera_stream_fetchers.append(camera_module.CameraStreamFetcher(**camera_init_dict))
        print(f"Number of camera stream fetchers created: {len(camera_stream_fetchers)}")

        # 3.
        camera_manager = camera_module.StreamManager()
        camera_manager._StreamManager__test_overwrite_CameraStreamFetchers(camera_stream_fetchers)

        max_number_of_cameras = int(input("Enter the maximum number of cameras to start fetching frames from: "))
        camera_manager.start_cameras_by_uuid(camera_uuids=[], max_number_of_cameras=max_number_of_cameras)
        start_time = time.time()
        is_show_frames = input("Do you want to show the frames fetched from the cameras for 60 seconds? (y/n): ")
        while time.time() - start_time < 60 and is_show_frames == 'y':
            camera_manager.show_all_frames(window_size=(1280, 720))
        cv2.destroyAllWindows()

        is_apply_pose_detection = input("Do you want to apply the models (pose detection, hardhat detection, forklift detection) on the frames for 120 seconds? (y/n): ")
        if(is_apply_pose_detection == 'y'):  
            pose_detector= models_module.PoseDetector(model_name=PREFERENCES.USED_MODELS["pose_detection_model_name"])
            hardhat_detector = models_module.HardhatDetector(model_name=PREFERENCES.USED_MODELS["hardhat_detection_model_name"])
            forklift_detector = models_module.ForkliftDetector(model_name=PREFERENCES.USED_MODELS["forklift_detection_model_name"])     
            
            recenty_evaluated_frame_uuids_wrt_camera = {} # Keep track of the  UUID of the last frame that is evaluated for each camera
            frame_evaluation_counts_wrt_camera = {} # Keep track of the number of frames evaluated for each camera
            start_time = time.time()
            while time.time() - start_time < 120:
                frames = camera_manager.return_all_recent_frames_info_as_list()
                for frame_info in frames:

                    if frame_info["camera_uuid"] in recenty_evaluated_frame_uuids_wrt_camera and frame_info["frame_uuid"] == recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]]: continue
                    recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = frame_info["frame_uuid"]    
                    
                    pose_detection_result = pose_detector.detect_frame(frame=None, frame_info=frame_info, bbox_threshold_confidence=0.5)
                    hardhat_detection_result = hardhat_detector.detect_frame(frame=None, frame_info=frame_info, bbox_threshold_confidence=0.5)
                    forklift_detection_result = forklift_detector.detect_frame(frame=None, frame_info=frame_info, bbox_threshold_confidence=0.5)

                    if frame_info["camera_uuid"] not in frame_evaluation_counts_wrt_camera: frame_evaluation_counts_wrt_camera[frame_info["camera_uuid"]] = 0
                    frame_evaluation_counts_wrt_camera[frame_info["camera_uuid"]] += 1

            print("Number of frames evaluated for each camera:")
            pprint.pprint(frame_evaluation_counts_wrt_camera)

            print("###Showing the last frames fatched by the first stream fetcher")
            camera_uuid = camera_manager.camera_stream_fetchers[0].camera_uuid
            for frame_info in camera_manager.return_last_frame_infos_by_camera_uuid(camera_uuid):
                frame = cv2.resize(frame_info["cv2_frame"], (1280, 720))
                cv2.putText(frame, f"{frame_info['frame_timestamp']}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.imshow('Frame', frame)
                cv2.waitKey(0) 

        cv2.destroyAllWindows()   
        print("Stopping all cameras")
        camera_manager.stop_cameras_by_uuid(camera_uuids=[])
        print("Test is completed")
                

if __name__ == "__main__":
    pass


    

    






