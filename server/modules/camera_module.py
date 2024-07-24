import random, threading, time, json
from pathlib import Path
from typing import Dict, List
import cv2
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
        self.last_frame = {
            "frame": None,
            "timestamp": 0, #time.time()
            "info": {},
            "is_checked_for_active_rules": False
        }
        self.number_of_frames_fetched = 0
        self.camera_score = 0 #A positive real number that represent how 'useful' the camera is. The higher the score, the more source is allocated to the camera by the StreamManager
        self.score_keeping_dictionary = self.__initiliaze_score_keeping_dictionary()

    def __initiliaze_score_keeping_dictionary(self):
        if self.scoring_method == "number_of_people_per_frame":
            return {
                "required_yolo_models": [],
                "number_of_frames_checked": 0,
                "number_of_people_detected": 0,
            }  
        else:
            raise ValueError(f"Scoring method {self.scoring_method} is not implemented yet")
              
    def check_for_active_rules_and_update_score(self, available_yolo_models:List[object]):
        required_models_to_use = [] #name of the models that are required to be used for this camera. This is decided by both 'active rules' and 'scoring method' attributes
        for active_rule in self.active_rules:
            if active_rule["yolo_model_to_use"] not in required_models_to_use:
                required_models_to_use.append(active_rule["yolo_model_to_use"])

        # Check for active rules and update the camera score
        
    def get_camera_score(self):
        return self.camera_score

    def start_fetching_frames(self):
        self.is_fetching_frames = True
        self.thread = threading.Thread(target=self.__IP_camera_frame_fetching_thread)
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

    def __IP_camera_frame_fetching_thread(self):
        url = f'rtsp://{self.username}:{self.password}@{self.camera_ip_address}/{self.stream_path}'
        cap = cv2.VideoCapture(url)

        buffer_size_in_frames = 1
        cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)

        self.last_frame["timestamp"] = time.time() # Set the initial timestamp
        while self.is_fetching_frames:   

            if not cap.grab():# Use grab() to capture the frame but not decode it yet for better performance
                continue 
            
            if time.time() - self.last_frame["timestamp"] > self.camera_fetching_delay: 
                ret, frame = cap.retrieve()
                if ret:
                    self.last_frame["frame"] = frame
                    self.last_frame["timestamp"] = time.time()
                    self.last_frame["is_checked_for_active_rules"] = False
                    self.number_of_frames_fetched += 1
                    self.camera_fetching_delay += random.uniform(server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[0], server_preferences.CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE[1]) # Randomize the fetching delay a little bit so that the cameras are not synchronized which may cause a bottleneck
                    if server_preferences.CAMERA_VERBOSE: print(f'{self.number_of_frames_fetched:8d} |: Got a frame from {self.camera_ip_address} at {time.time()}')
                else:
                    if server_preferences.CAMERA_VERBOSE: print(f'{self.number_of_frames_fetched:8d} |: Could not retrieve frame from {self.camera_ip_address} at {time.time()}')
                    continue

        cap.release()

class StreamManager:
    def __init__(self) -> None:        
        CAMERA_MODULE_PATH = Path(__file__).resolve()
        CAMERA_CONFIGS_JSON_PATH = CAMERA_MODULE_PATH.parent.parent / "configs" / "camera_configs.json"
        with open(CAMERA_CONFIGS_JSON_PATH, "r") as f:
            self.CAMERA_CONFIGS= json.load(f)["cameras"]
        
        # Create Camera Objects whether they are alive or not
        self.cameras = []
        for camera_config in self.CAMERA_CONFIGS:
            camera = CameraStreamFetcher(**camera_config)
            self.cameras.append(camera)

        # Check for IP collisions (no matter whether the cameras are alive or not)
        assigned_ips = []
        for camera in self.cameras:
            if camera.camera_ip_address in assigned_ips:
                raise ValueError(f"IP address {camera.camera_ip_address} is already assigned to another camera")
            assigned_ips.append(camera.camera_ip_address)

    def start_cameras_by_uuid(self, camera_uuids:List[str] = []):    
        # Start fetching frames from the cameras. If camera_uuids is empty, start all cameras, otherwise start only the cameras with the specified uuids    
        # If camera is not alive, skip it. Alive means that the camera is reachable and the stream is available
        number_of_cameras_to_fetch = 0
        for camera in self.cameras:  
            if not camera.is_alive:
                continue
            
            if camera.camera_uuid in camera_uuids or len(camera_uuids) == 0:
                camera.start_fetching_frames()

    def stop_cameras_by_uuid(self, camera_uuids:List[str]):
        # Stop fetching frames from the cameras. If camera_uuids is empty, stop all cameras, otherwise stop only the cameras with the specified uuids
        for camera in self.cameras:
            if camera.camera_uuid in camera_uuids or len(camera_uuids) == 0:
                camera.stop_fetching_frames()        

    def optimize_camera_fetching_delays(self):
        
        number_of_fetching_cameras = 0
        for camera in self.cameras:
            if camera.is_fetching_frames and camera.is_alive:
                number_of_fetching_cameras += 1
        
        server_preferences.PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras=number_of_fetching_cameras)



        # assuming 250ms to process a signle frame, total process time per second should be around 1 second

# Test
if __name__ == "__main__":

    stream_manager = StreamManager()
    stream_manager.start_cameras_by_uuid()

    while True:
        stream_manager.optimize_camera_fetching_delays()
        continue

