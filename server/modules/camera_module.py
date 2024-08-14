import random, threading, time, json, math, uuid, platform, pprint
from pathlib import Path
from typing import Dict, List
import cv2
import numpy as np

import server_preferences

class CameraStreamFetcher:
    def __init__(self, **kwargs )->None:         
        for key in server_preferences.CAMERA_CONFIG_KEYS:
            if key not in kwargs.keys():
                raise ValueError(f"Missing camera config argument. Required: {key}")
              
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.camera_fetching_delay = random.uniform(server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[0], server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[1]) # Randomize the fetching delay a little bit so that the cameras are not synchronized which may cause a bottleneck
        self.is_fetching_frames = False
        self.last_frame_info = None # keys -> frame, camera_uuid, frame_uuid, frame_timestamp, active_rules, is_evaluated
        self.number_of_frames_fetched = 0
        self.camera_score = 0 #A positive real number that represent how 'useful' the camera is. The higher the score, the more source is allocated to the camera by the StreamManager
           
    def get_last_frame_info(self):
        return self.last_frame_info
    
    def start_fetching_frames(self):
        self.is_fetching_frames = True
        self.thread = threading.Thread(target=self.__IP_camera_frame_fetching_thread_single_frame)
        self.thread.daemon = True # Set the thread as a daemon means that it will stop when the main program stops
        self.thread.start()   
        if server_preferences.CAMERA_VERBOSE: print(f'Started fetching frames from {self.camera_ip_address} at {time.time()}')     

    def stop_fetching_frames(self):
        self.is_fetching_frames = False  
        self.thread.join()
        self.thread = None

    def update_camera_fetching_delay(self, new_delay:float = None):
        if self.is_fetch_without_delay:
            raise ValueError(f"Camera {self.camera_ip_address} is set to fetch frames without delay. Cannot change the fetching delay")
        self.soon_camera_fetching_delay = new_delay

    def set_last_frame_as_evaluated_if_frame_uuid_matches(self, frame_uuids:List[str]=[]):
        if self.last_frame_info is not None and self.last_frame_info["frame_uuid"] in frame_uuids:
            self.last_frame_info["is_evaluated"] = True

    def __IP_camera_frame_fetching_thread(self):
        try:
            url = f'rtsp://{self.username}:{self.password}@{self.camera_ip_address}/{self.stream_path}'
            cap = cv2.VideoCapture(url)

            buffer_size_in_frames = 1
            cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)

            while self.is_fetching_frames:   
                if not cap.grab():# Use grab() to capture the frame but not decode it yet for better performance
                    continue                 

                if self.last_frame_info == None or (time.time() - self.last_frame_info["frame_timestamp"] > self.camera_fetching_delay): #NOTE: If frame is none,  
                    ret, frame = cap.retrieve()
                    if ret:
                        self.last_frame_info = {}
                        self.last_frame_info["frame"] = frame
                        self.last_frame_info["camera_uuid"] = self.camera_uuid
                        self.last_frame_info["frame_uuid"] = str(uuid.uuid4())
                        self.last_frame_info["frame_timestamp"] = time.time()
                        self.last_frame_info["active_rules"] = self.active_rules
                        self.last_frame_info["is_evaluated"] = False
                        self.number_of_frames_fetched += 1
                        self.camera_fetching_delay = random.uniform(server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[0], server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[1]) # Randomize the fetching delay a little bit so that the cameras are not synchronized which may cause a bottleneck
                        if server_preferences.CAMERA_VERBOSE: print(f'{self.number_of_frames_fetched:8d} |: Got a frame from {self.camera_ip_address} at {time.time()}')
                    else:
                        if server_preferences.CAMERA_VERBOSE: print(f'{self.number_of_frames_fetched:8d} |: Could not retrieve frame from {self.camera_ip_address} at {time.time()}')
                        continue

            cap.release()           
        except Exception as e:
            if server_preferences.CAMERA_VERBOSE: print(f'Error in fetching frames from {self.camera_ip_address}: {e}')

        self.is_fetching_frames = False

    def __IP_camera_frame_fetching_thread_single_frame(self):
        try:
            url = f'rtsp://{self.username}:{self.password}@{self.camera_ip_address}/{self.stream_path}'
          
            cap = None
            while self.is_fetching_frames:  
                cap = cv2.VideoCapture(url)
                buffer_size_in_frames = 1
                cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)             
                ret, frame = cap.read()
                if ret:
                    self.last_frame_info = {}
                    self.last_frame_info["frame"] = frame
                    self.last_frame_info["camera_uuid"] = self.camera_uuid
                    self.last_frame_info["frame_uuid"] = str(uuid.uuid4())
                    self.last_frame_info["frame_timestamp"] = time.time()
                    self.last_frame_info["active_rules"] = self.active_rules
                    self.last_frame_info["is_evaluated"] = False
                    self.number_of_frames_fetched += 1           
                    self.camera_fetching_delay = random.uniform(server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[0], server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[1]) # Randomize the fetching delay a little bit so that the cameras are not synchronized which may cause a bottleneck
                    if server_preferences.CAMERA_VERBOSE: print(f'{self.number_of_frames_fetched:8d} |: Got a frame from {self.camera_ip_address} at {time.time()}')                      
                else:
                    if server_preferences.CAMERA_VERBOSE: print(f'{self.number_of_frames_fetched:8d} |: Could not retrieve frame from {self.camera_ip_address} at {time.time()}')
                    break # Break the loop if the frame could not be retrieved
                self.camera_fetching_delay = random.uniform(0,10) # Randomize the fetching delay a little bit so that the cameras are not synchronized which may cause a bottleneck CPU
                time.sleep( self.camera_fetching_delay) # Sleep so that CPU is not bottlenecked
            if cap is not None: cap.release()          
        except Exception as e:
            if server_preferences.CAMERA_VERBOSE: print(f'Error in fetching frames from {self.camera_ip_address}: {e}')

        self.is_fetching_frames = False

class StreamManager:
    def __init__(self) -> None:        
        CAMERA_MODULE_PATH = Path(__file__).resolve()

        is_linux = platform.system() == "Linux"
        if is_linux:
            CAMERA_CONFIGS_JSON_PATH = CAMERA_MODULE_PATH.parent.parent.parent.parent / "safety_AI_volume" / "camera_configs.json"
        else:
            CAMERA_CONFIGS_JSON_PATH = CAMERA_MODULE_PATH.parent.parent / "configs" / "camera_configs.json"

        with open(CAMERA_CONFIGS_JSON_PATH, "r") as f:
            self.CAMERA_CONFIGS= json.load(f)["cameras"]
       
        # Create camera objects for alive cameras
        self.cameras = []
        for camera_config in self.CAMERA_CONFIGS:
            if not camera_config["is_alive"]: continue

            camera = CameraStreamFetcher(**camera_config)
            self.cameras.append(camera)

        # Check for IP collisions (Consider only the initialized cameras)
        assigned_ips = []
        for camera in self.cameras:
            if camera.camera_ip_address in assigned_ips:
                raise ValueError(f"IP address {camera.camera_ip_address} is already assigned to another camera")
            assigned_ips.append(camera.camera_ip_address)

    def start_cameras_by_uuid(self, camera_uuids:List[str] = []):    
        # Start fetching frames from the cameras. If camera_uuids is empty, start all cameras, otherwise start only the cameras with the specified uuids    
        # If camera is not alive, skip it. Alive means that the camera is reachable and the stream is available

        for camera in self.cameras:  
            if not camera.is_alive:
                continue

            if (camera.camera_uuid in camera_uuids or len(camera_uuids) == 0) and not camera.is_fetching_frames:              
                camera.start_fetching_frames()

        self.optimize_camera_fetching_delays() # One my use this externally. Yet since its rarely used and not computationally intensive, It is also put here

    def optimize_camera_fetching_delays(self):        
        number_of_fetching_cameras = 0
        for camera in self.cameras:
            if camera.is_fetching_frames and camera.is_alive:
                number_of_fetching_cameras += 1
        
        server_preferences.PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras=number_of_fetching_cameras)

    def stop_cameras_by_uuid(self, camera_uuids:List[str]):
        # Stop fetching frames from the cameras. If camera_uuids is empty, stop all cameras, otherwise stop only the cameras with the specified uuids
        for camera in self.cameras:
            if camera.camera_uuid in camera_uuids or len(camera_uuids) == 0:
                camera.stop_fetching_frames()        

        self.optimize_camera_fetching_delays() # One my use this externally. Yet since its rarely used and not computationally intensive, It is also put here

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

# Test
if __name__ == "__main__":

    stream_manager = StreamManager()
    stream_manager.start_cameras_by_uuid(camera_uuids = []) # Start all cameras

    while True:
        stream_manager.optimize_camera_fetching_delays()        
        stream_manager.test_show_all_frames(window_size=(1280, 720))


