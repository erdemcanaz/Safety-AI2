import random, threading, time, json, math, uuid, platform, pprint, datetime, re
from pathlib import Path
from typing import Dict, List
import cv2
import numpy as np
import server_preferences

class CameraStreamFetcher:
    CLASS_PARAM_NUMBER_OF_FRAMES_TO_KEEP = 25
    CLASS_PARAM_CAMERA_CONFIG_KEYS = [                            # Will be added to the object as attributes
            'camera_uuid',
            'camera_region',
            'camera_description',
            'is_alive',
            'NVR_ip',            
            'camera_ip_address',
            'username',
            'password',
            'stream_path',
            'active_rules'
    ] 
    def __init__(self, **kwargs )->None:  

        for key in CameraStreamFetcher.CLASS_PARAM_CAMERA_CONFIG_KEYS:
            if key not in kwargs.keys():
                raise ValueError(f"Missing camera config argument. Required: {key}")

        for key, value in kwargs.items():                       # Assing the arguments to the object
            setattr(self, key, value)

        self.RTSP_thread = None                                 # The thread that fetches frames from the camera
        self.camera_retrieving_delay_uniform_range = [0, 10]    # The range of uniform distribution for the delay between frame retrievals. Otherwise grab is used where no decoding happens. The delay is calculated as a random number between the range
        self.is_fetching_frames = False                         # A flag to indicate whether the camera is fetching frames or not. If true, the camera is fetching frames. If false, the camera is not fetching frames
        self.last_frame_info = None                             # keys -> frame, camera_uuid, frame_uuid, frame_timestamp, active_rules, is_evaluated
        self.recent_frames= []                                  # The last 'CLASS_PARAM_NUMBER_OF_FRAMES_TO_KEEP' frames fetched from the camera
        self.number_of_frames_fetched = 0                       # The number of frames fetched from the camera    

    def __repr__(self) -> str:
        return f'CameraStreamFetcher({self.camera_ip_address}, is_alive={self.is_alive}, is_fetching_frames={self.is_fetching_frames})'
    
    def __print_wrapper(self, condition:False, message:str = ""):
        if condition: print(f'{datetime.datetime.strftime("%Y-%m-%d %H:%M:%S")} | CameraStreamFetcher |{message}')
        
    def get_last_frame_info(self)->Dict:
        return self.last_frame_info
    
    def append_frame_to_recent_frames(self, frame:np.ndarray):
        self.recent_frames.append(frame)
        if len(self.recent_frames) > self.CLASS_PARAM_NUMBER_OF_FRAMES_TO_KEEP:
            self.recent_frames.pop(0)
    
    def start_fetching_frames(self):
        if self.RTSP_thread is not None: self.stop_fetching_frames(wait_for_thread_to_join = True)  # Stop the thread if it is already running
        
        self.is_fetching_frames = True
        self.RTSP_thread = threading.Thread(target=self.__IP_camera_frame_fetching_thread)
        self.RTSP_thread.daemon = True                                                              # Set the thread as a daemon means that it will stop when the main program stops
        self.RTSP_thread.start()   
        self.__print_wrapper(condition = server_preferences.PARAM_CAMERA_VERBOSE, message = f'Started fetching frames from {self.camera_ip_address}')

    def stop_fetching_frames(self, wait_for_thread_to_join:bool = True):
        self.is_fetching_frames = False  
        if wait_for_thread_to_join: self.RTSP_thread.join()
        self.RTSP_thread = None
        self.__print_wrapper(condition = server_preferences.PARAM_CAMERA_VERBOSE, message = f'Stopped fetching frames from {self.camera_ip_address}')

    def __IP_camera_frame_fetching_thread(self):
        cap = None

        try:
            # Open the camera RTSP stream which takes about 2 seconds
            url = f'rtsp://{self.username}:{self.password}@{self.camera_ip_address}/{self.stream_path}'
            cap = cv2.VideoCapture(url)
            buffer_size_in_frames = 1
            cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)

            while self.is_fetching_frames:   
                # Use grab() to capture the frame without decoding it. This is faster than retrieve() which decodes the frame 
                if not cap.grab():                             
                    continue                                                                  
                # Decode the frame by calling retrive() on the grabbed frame if enough time has passed since the last frame was decoded
                if self.last_frame_info == None or (time.time() - self.last_frame_info["frame_timestamp"] > self.camera_fetching_delay):
                    ret, frame = cap.retrieve() # Use retrieve() to decode the frame 
                    if ret:
                        self.last_frame_info = {}
                        self.last_frame_info["frame"] = frame
                        self.last_frame_info["camera_uuid"] = self.camera_uuid
                        self.last_frame_info["frame_uuid"] = str(uuid.uuid4())
                        self.last_frame_info["frame_timestamp"] = time.time()
                        self.last_frame_info["active_rules"] = self.active_rules
                        self.number_of_frames_fetched += 1
                        self.camera_fetching_delay = random.uniform(server_preferences.PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[0], server_preferences.PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[1]) # Randomize the fetching delay a little bit so that the cameras are not synchronized which may cause a bottleneck
                        self.__print_wrapper(condition=server_preferences.PARAM_CAMERA_VERBOSE, message = f'Frames fetched: {self.number_of_frames_fetched:8d} |: Got a frame from {self.camera_ip_address} | Delay: {self.camera_fetching_delay:.2f} seconds') 
                        self.append_frame_to_recent_frames(frame)
                    else:
                        self.__print_wrapper(condition=server_preferences.PARAM_CAMERA_VERBOSE, message = f'Error in decoding frame from {self.camera_ip_address}')
                        continue          
        except Exception as e:
            self.__print_wrapper(condition=server_preferences.PARAM_CAMERA_VERBOSE, message = f'Error in fetching frames from {self.camera_ip_address}: {e}')

        if cap is not None: cap.release()
        self.is_fetching_frames = False

    def test_try_fetching_single_frame_and_show(self, window_name_to_show:str = "Test Frame"):
        try:
            cap = cv2.VideoCapture(f'rtsp://{self.username}:{self.password}@{self.camera_ip_address}/{self.stream_path}')
            ret, frame = cap.read()
            if ret:
                cv2.imshow(window_name_to_show, frame)
                cv2.waitKey(2500)
            cap.release()
            return ret
        except Exception as e:
            return False
    
class StreamManager:
    def __init__(self) -> None:        
        self.cameras = []
        self.reinitiliaze_cameras_from_camera_configs_file()

    def reinitiliaze_cameras_from_camera_configs_file(self):
        # Ensure that the cameras are stopped before reinitializing them if they are already fetching frames    
        for camera in self.cameras:
            camera.stop_fetching_frames(wait_for_thread_to_join = True)
        self.cameras = []

        # Read the camera configurations from the camera_configs.json file
        with open(server_preferences.PATH_CAMERA_CONFIGS_JSON, "r") as f:
                    camera_configs= json.load(f)["cameras"]
            
        # Create the camera objects
        for camera_config in camera_configs:         
            self.cameras.append(CameraStreamFetcher(**camera_config)) 

        # Check for IP collisions
        camera_ip_addresses = [camera.camera_ip_address for camera in self.cameras]
        if len(camera_ip_addresses) != len(set(camera_ip_addresses)):
            duplicate_ips = {ip for ip in camera_ip_addresses if camera_ip_addresses.count(ip) > 1}
            raise ValueError(f"There are cameras with the same IP address: {', '.join(duplicate_ips)}. Please ensure that each camera has a unique IP address")

        # Check for IP format (xxx.xxx.xxx.xxx) where x is a digit between 0-9
        invalid_ip_cameras = [
            camera.camera_ip_address for camera in self.cameras
            if not all(part.isdigit() and 0 <= int(part) <= 255 for part in camera.camera_ip_address.split('.'))
        ]
        if invalid_ip_cameras:
            raise ValueError(f"Invalid IP address format for cameras: {', '.join(invalid_ip_cameras)}. Please ensure that each IP address is in the format XXX.XXX.XXX.XXX where x is a digit between 0-9")

        # Check for camera UUID collisions
        camera_uuids = [camera.camera_uuid for camera in self.cameras]
        if len(camera_uuids) != len(set(camera_uuids)):
            duplicate_uuids = {uuid for uuid in camera_uuids if camera_uuids.count(uuid) > 1}
            raise ValueError(f"There are cameras with the same UUID: {', '.join(duplicate_uuids)}. Please ensure that each camera has a unique UUID")

        # Check for camera UUID format
        uuid_regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
        invalid_uuid_cameras = [camera.camera_uuid for camera in self.cameras if not uuid_regex.match(camera.camera_uuid)]
        if invalid_uuid_cameras:
            raise ValueError(f"Invalid UUID format for cameras: {', '.join(invalid_uuid_cameras)}. Please ensure that each UUID is in the format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")

        server_preferences.PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras=len(self.cameras)) #NOTE: Worst case scenario is when all cameras are fetching frames. It will be updated later to reflect the actual number of fetching cameras.
    
    def __optimize_camera_decoding_delays(self):        
        # Optimize the decoding delays of the cameras. The decoding delay is the delay between decoding frames from the camera stream.
        # Since decoding is computationally intensive, the decoding delay is used to prevent the cameras from being synchronized.
        # It aims that each camera has a different decoding delay to prevent bottlenecks.
        number_of_fetching_cameras = sum(1 for camera in self.cameras if camera.is_fetching_frames and camera.is_alive)
        server_preferences.PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras=number_of_fetching_cameras)

    def start_cameras_by_uuid(self, camera_uuids:List[str] = []):    
        # Start fetching frames from the cameras. If camera_uuids is empty, start all cameras, otherwise start only the cameras with the specified uuids    
        # If camera is not alive, skip it. Alive means that the camera is reachable and the stream is available
        start_all_alive_cameras = len(camera_uuids) == 0
        for camera in self.cameras:
            if camera.is_alive and (start_all_alive_cameras or camera.camera_uuid in camera_uuids):           
                camera.start_fetching_frames()

        self.__optimize_camera_decoding_delays() # One my use this externally. Yet since its rarely used and not computationally intensive, It is also put here

    def stop_cameras_by_uuid(self, camera_uuids:List[str]):
        # Stop fetching frames from the cameras. If camera_uuids is empty, stop all cameras, otherwise stop only the cameras with the specified uuids
        stop_all_cameras = len(camera_uuids) == 0
        for camera in self.cameras:
            if stop_all_cameras or camera.camera_uuid in camera_uuids:
                camera.stop_fetching_frames()        

        self.__optimize_camera_decoding_delays() # One my use this externally. Yet since its rarely used and not computationally intensive, It is also put here

    def return_all_not_evaluated_frames_info(self) -> List[Dict]:
        not_evaluated_frames_info = []
        for camera in self.cameras:
            if camera.get_last_frame_info() is not None and not camera.get_last_frame_info()["is_evaluated"]:
                not_evaluated_frames_info.append(camera.get_last_frame_info())
                camera.set_last_frame_as_evaluated_if_frame_uuid_matches()

        return not_evaluated_frames_info

    def update_frame_evaluations(self, evaluated_frame_uuids:List[str]):
        for camera in self.cameras:
            camera.set_last_frame_as_evaluated_if_frame_uuid_matches(evaluated_frame_uuids)
    
    def test_show_all_frames(self, window_size=(1280, 720)):
        frames_to_show = []
    
        for camera in self.cameras:
            frame = camera.get_last_frame_info()["frame"] if camera.get_last_frame_info() is not None else None
            if frame is not None:
                frames_to_show.append(frame)            

        num_frames = len(frames_to_show)

        if num_frames == 0:
            return
        
        # Determine the optimal grid size (rows x cols)
        grid_cols = math.ceil(math.sqrt(num_frames))
        grid_rows = math.ceil(num_frames / grid_cols)

        # Determine the size of each frame to fit in the grid within the window size
        frame_width = window_size[0] // grid_cols
        frame_height = window_size[1] // grid_rows

        # Create an empty canvas to place the frames
        canvas = np.zeros((window_size[1], window_size[0], 3), dtype=np.uint8)

        for i, frame in enumerate(frames_to_show):
            row = i // grid_cols
            col = i % grid_cols

            # Resize frame to fit in the grid
            resized_frame = cv2.resize(frame, (frame_width, frame_height))
            canvas[row * frame_height:(row + 1) * frame_height, col * frame_width:(col + 1) * frame_width] = resized_frame

        cv2.imshow('Fetched CCTV Frames', canvas)
        cv2.waitKey(1)

    def return_yolo_models_to_use(self)->List[str]:
        yolo_model_to_use = []
        for camera in self.cameras:
            for rule in camera.active_rules:
                if rule["yolo_model_to_use"] not in yolo_model_to_use:
                    yolo_model_to_use.append(rule["yolo_model_to_use"])

        return yolo_model_to_use

if __name__ == "__main__":

    server_preferences.PARAM_CAMERA_VERBOSE = False

    # Fetch and show a single frame from the camera for all cameras
    print("Testing fetching a single frame from the camera")
    cameras = []
    with open(server_preferences.PATH_CAMERA_CONFIGS_JSON, "r") as f:
                camera_configs = json.load(f)["cameras"]       
  
    for camera_config in camera_configs:         
        cameras.append(CameraStreamFetcher(**camera_config)) 

    for camera_index, camera in enumerate(cameras):
        is_fetched_properly = camera.test_try_fetching_single_frame_and_show("Test Frame")
        print(f"    {camera_index:<3}/{len(cameras):<3} | {camera.camera_ip_address:<16} | {'Success' if is_fetched_properly else 'An error occurred'}")

    

