import random, threading, time, json, math, uuid, platform, pprint, datetime, re, sys, copy
from pathlib import Path
from typing import Dict, List
import cv2
import numpy as np

import PREFERENCES
import safety_ai_api_dealer

class CameraStreamFetcher:
    CLASS_PARAM_NUMBER_OF_FRAMES_TO_KEEP = 10                         # The number of frames to keep in the recent_frames list. If the list grows larger than this number, the oldest frames are removed
    CLASS_PARAM_MINIMUM_DURATION_BETWEEN_RECENT_FRAME_APPENDING = 1.5 # The minimum duration between appending frames to the recent_frames list in seconds. This is to prevent the list from growing too large too quickly. If a frame is fetched before this duration has passed, it is not appended to the list
    CLASS_PARAM_CAMERA_CONFIG_KEYS = [                                # Will be added to the object as attributes
            'camera_uuid',
            'camera_region',
            'camera_description',
            'camera_status',
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

        self.lock = threading.Lock()                            # A lock to prevent race conditions when deep copying the last_frame_info
        self.number_of_frames_fetched = 0                       # The number of frames fetched from the camera    
        self.RTSP_thread = None                                 # The thread that fetches frames from the camera
        self.camera_retrieving_delay_uniform_range = [0, 10]    # The range of uniform distribution for the delay between frame retrievals. Otherwise grab is used where no decoding happens. The delay is calculated as a random number between the range
        self.is_fetching_frames = False                         # A flag to indicate whether the camera is fetching frames or not. If true, the camera is fetching frames. If false, the camera is not fetching frames
        self.last_frame_info = None                             # keys -> frame, camera_uuid, frame_uuid, frame_timestamp, active_rules, is_evaluated
        self.recent_frames= []                                  # The last 'CLASS_PARAM_NUMBER_OF_FRAMES_TO_KEEP' frames fetched from the camera
        self.__print_wrapper(condition = PREFERENCES.SAFETY_AI_VERBOSES['camera_initialization'], message = f'CameraStreamFetcher object created for {self.camera_ip_address}')

    def __repr__(self) -> str:
        return f'CameraStreamFetcher({self.camera_ip_address}, camera_status={self.camera_status}, is_fetching_frames={self.is_fetching_frames})'
    
    def __print_wrapper(self, condition:False, message:str = ""):
        if condition: print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | CameraStreamFetcher |{message}')
        
    def get_last_frame_info(self)->Dict:
        with self.lock:
            return copy.deepcopy(self.last_frame_info) # To prevent race conditions. Since the self.last_frame_info is continuously updated by the RTSP thread, it is better to return a deep copy of it
    
    def get_recent_frames_infos(self)->List[np.ndarray]:
        with self.lock:            
            return copy.deepcopy(self.recent_frames)   # To prevent race conditions. Since the self.recent_frames is continuously updated by the RTSP thread, it is better to return a deep copy of it
        
    def append_frame_to_recent_frames(self, frame:np.ndarray):
        if self.last_frame_info is None or time.time() - self.last_frame_info["frame_timestamp"] > self.CLASS_PARAM_MINIMUM_DURATION_BETWEEN_RECENT_FRAME_APPENDING:
            self.recent_frames.append(frame)
            if len(self.recent_frames) > self.CLASS_PARAM_NUMBER_OF_FRAMES_TO_KEEP:
                popped_frame = self.recent_frames.pop(0)
                del popped_frame  # Explicitly delete the popped frame immediately to free up memory
    
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
                        with self.lock:
                            self.last_frame_info = {}
                            self.last_frame_info["frame"] = frame
                            self.last_frame_info["camera_uuid"] = self.camera_uuid
                            self.last_frame_info["frame_uuid"] = str(uuid.uuid4())
                            self.last_frame_info["frame_timestamp"] = time.time()
                            self.last_frame_info["active_rules"] = self.active_rules
                            self.last_frame_info["detection_results"] = []
                            self.last_frame_info["rule_violations"] = {}
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

        def draw_points(frame, points):
            for i, point in enumerate(points):
                x, y = point
                height, width, _ = frame.shape
                x = int(x * width)
                y = int(y * height)
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                if i > 0:
                    x_prev, y_prev = points[i - 1]
                    x_prev = int(x_prev * width)
                    y_prev = int(y_prev * height)
                    cv2.line(frame, (x_prev, y_prev), (x, y), (255, 0, 0), 2)

            # If there are at least 3 points, connect the first and last points to close the polygon
            if len(points) > 2:
                x_first, y_first = points[0]
                x_last, y_last = points[-1]
                x_first = int(x_first * width)
                y_first = int(y_first * height)
                x_last = int(x_last * width)
                y_last = int(y_last * height)
                cv2.line(frame, (x_last, y_last), (x_first, y_first), (0, 0, 255), 2)  # Red color for closing the polygon

        try:
            cap = cv2.VideoCapture(f'rtsp://{self.username}:{self.password}@{self.camera_ip_address}/{self.stream_path}')
            ret, frame = cap.read()
            resoulution = (None,None)
            if ret:
                for rule in self.active_rules:
                    points = rule.get("normalized_rule_area_polygon_corners", [])
                    draw_points(frame, points)
                cv2.imshow(window_name_to_show, frame)
                resoulution = (frame.shape[1], frame.shape[0])
                cv2.waitKey(1000)

            cap.release()
            return ret, resoulution, frame
        except Exception as e:
            return False, (None,None)
    
class StreamManager:
    def __init__(self, api_dealer:safety_ai_api_dealer.SafetyAIApiDealer = None) -> None:  
        self.api_dealer = api_dealer   
        self.camera_info_dicts ={} # A dict where the key is the camera UUID and the value is the camera info | # NVR_ip_address, camera_description, camera_ip_address, camera_region, camera_status, camera_uuid, date_created, date_updated, password, stream_path, username
        self.last_time_camera_info_dict_updated = 0 # The time when the camera info dictionary was last updated
        self.camera_rules_dicts = {} # A dict where the key is the camera UUID and the value is the camera rules
        self.last_time_camera_rules_dict_updated = 0 # The time when the camera rules dictionary was last updated
        self.camera_stream_fetchers = [] # A list of CameraStreamFetcher objects

        # self.reinitiliaze_cameras_from_camera_configs_file()

    def update_cameras(self, update_interval_seconds:float = 30):
        """
        This function periodically fetches updated camera information from the server and synchronizes the camera_stream_fetchers list with the latest data.
        Every 'update_interval_seconds' seconds, the function retrieves the current camera info, checking for any new, updated, or removed cameras. If changes are detected, the camera_stream_fetchers list is fully refreshed: all existing camera streams are stopped and removed, and new stream fetcher objects are initialized to reflect the latest camera data.
        The function also includes several built-in validation checks:
        - Checks for IP address collisions.
        - Checks for camera UUID collisions.
        - Validates camera UUID formats.
        - Validates IP address formats (xxx.xxx.xxx.xxx), ensuring each segment is a digit between 0-9.
        """
        # NOTE: This function prioritizes simplicity over performance optimization, as camera information and rules are not updated frequently. 
        # If updates to camera information and rules become more frequent, consider optimizing this function to enhance performance. 
        # In such cases, it may be unnecessary to reinitialize all cameras. Yet, easier to implement and maintain this way.

        if time.time() - self.last_time_camera_info_dict_updated < update_interval_seconds: return # If the camera info was updated recently, skip updating it
        self.last_time_camera_info_dict_updated = time.time()

        # Fetch the camera info from the server and update the camera_info_dict
        response = self.api_dealer.fetch_all_camera_info() # [is_successful, status code, response_data]

        if response[0] == False:
            print(f"Error in fetching camera info: {response[2]}")
            return

        # Initialize flags
        is_new_camera_added = False
        is_camera_info_changed = False
        is_camera_removed = False

        fetched_dicts = response[2]["camera_info"] # NVR_ip_address, camera_description, camera_ip_address, camera_region, camera_status, camera_uuid, date_created, date_updated, password, stream_path, username]
        fetched_camera_info_dicts = {fetched_camera_info_dict['camera_uuid']: fetched_camera_info_dict for fetched_camera_info_dict in fetched_dicts}
        
        #check for new cameras
        for fetched_camera_uuid in fetched_camera_info_dicts.keys():
            if fetched_camera_uuid not in self.camera_info_dicts:
                is_new_camera_added = True
                break

        # check for deleted cameras
        for existing_camera_uuid in self.camera_info_dicts.keys():
            if existing_camera_uuid not in fetched_camera_info_dicts:
                is_camera_removed = True
                break
        
        # check for updated cameras
        for fetched_camera_uuid, fetched_camera_info in fetched_camera_info_dicts.items():
            if fetched_camera_uuid in self.camera_info_dicts:
                for key, value in fetched_camera_info.items():
                    if self.camera_info_dicts[fetched_camera_uuid][key] != value:
                        self.camera_info_dicts[fetched_camera_uuid][key] = value
                        is_camera_info_changed = True
                        break
        
        if not is_new_camera_added and not is_camera_info_changed and not is_camera_removed: return # If there is no change in the camera info, skip updating the camera stream fetchers
        if PREFERENCES.SAFETY_AI_VERBOSES["CRUD_on_camera_info"]: print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | StreamManager | New camera added: {is_new_camera_added:<6}, Camera info changed: {is_camera_info_changed:<6}, Camera removed: {is_camera_removed:<6}")
                                                                        
        # UPDATE THE CAMERA INFO DICTIONARY & REINITIALIZE THE CAMERA STREAM FETCHERS ========================================================
        self.camera_info_dicts = fetched_camera_info_dicts 

        # Check for IP collisions
        camera_ip_addresses = [camera_info_dict["camera_ip_address"] for camera_info_dict in self.camera_info_dicts.values()]
        if len(camera_ip_addresses) != len(set(camera_ip_addresses)):
            duplicate_ips = {ip for ip in camera_ip_addresses if camera_ip_addresses.count(ip) > 1}
            raise ValueError(f"There are cameras with the same IP address: {', '.join(duplicate_ips)}. Please ensure that each camera has a unique IP address")
        
        # Check for IP format (xxx.xxx.xxx.xxx) where x is a digit between 0-9
        invalid_ip_cameras = [
            camera_info_dict["camera_ip_address"] for camera_info_dict in self.camera_info_dicts.values()
            if not all(part.isdigit() and 0 <= int(part) <= 255 for part in camera_info_dict["camera_ip_address"].split('.'))
        ]
        if invalid_ip_cameras:
            raise ValueError(f"Invalid IP address format for cameras: {', '.join(invalid_ip_cameras)}. Please ensure that each IP address is in the format XXX.XXX.XXX.XXX where x is a digit between 0-9")
        
        # Check for camera UUID collisions
        camera_uuids = [camera_info_dict["camera_uuid"] for camera_info_dict in self.camera_info_dicts.values()]
        if len(camera_uuids) != len(set(camera_uuids)):
            duplicate_uuids = {uuid for uuid in camera_uuids if camera_uuids.count(uuid) > 1}
            raise ValueError(f"There are cameras with the same UUID: {', '.join(duplicate_uuids)}. Please ensure that each camera has a unique UUID")
        
        # Check for camera UUID format
        uuid_regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
        invalid_uuid_cameras = [camera_info_dict["camera_uuid"] for camera_info_dict in self.camera_info_dicts.values() if not uuid_regex.match(camera_info_dict["camera_uuid"])]
        if invalid_uuid_cameras:
            raise ValueError(f"Invalid UUID format for cameras: {', '.join(invalid_uuid_cameras)}. Please ensure that each UUID is in the format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        
        # The rules will be fetched separately, assume that there are no active rules for now
        for camera_info_dict in self.camera_info_dicts.values():
            camera_info_dict.update({'active_rules':[]}) 

        # Stop all cameras. Code waits for the threads to join.
        self.stop_cameras_by_uuid([])
        self.camera_stream_fetchers = [] # Garbage collect the old camera stream fetchers
        for camera_info_dict in self.camera_info_dicts.values():
            self.camera_stream_fetchers.append(CameraStreamFetcher(**camera_info_dict))

    def stop_cameras_by_uuid(self, camera_uuids:List[str]):
        stop_all_cameras = len(camera_uuids) == 0
        for camera in self.camera_stream_fetchers:
            if stop_all_cameras or camera.camera_uuid in camera_uuids:
                camera.stop_fetching_frames()  

    def reinitiliaze_cameras_from_camera_configs_file(self, number_of_cameras:int = 24):
        # Ensure that the cameras are stopped before reinitializing them if they are already fetching frames    
        for camera in self.cameras:
            camera.stop_fetching_frames(wait_for_thread_to_join = True)
        self.cameras = []

        # Read the camera configurations from the camera_configs.json file
        with open(server_preferences.PATH_CAMERA_CONFIGS_JSON, "r") as f:
                    camera_configs= json.load(f)["cameras"]

        # If the number_of_cameras is specified, only use the first number_of_cameras cameras from the camera_configs
        if number_of_cameras > 0:
            camera_configs = camera_configs[:number_of_cameras]
            
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

        # Check for active rules UUID collisions
        active_rules_uuids = []
        for camera in self.cameras:
            active_rules_uuids.extend([rule.get("rule_uuid") for rule in camera.active_rules])
        if len(active_rules_uuids) != len(set(active_rules_uuids)):
            duplicate_uuids = {uuid for uuid in active_rules_uuids if active_rules_uuids.count(uuid) > 1}
            raise ValueError(f"There are active rules with the same UUID for camera {camera.camera_uuid}: {', '.join(duplicate_uuids)}. Please ensure that each active rule has a unique UUID")
        
        # Check for active rules UUID format
        invalid_uuids = []
        for camera in self.cameras:
            active_rules = camera.active_rules
            for rule in active_rules:
                rule_uuid = rule.get("rule_uuid")
                if not uuid_regex.match(rule_uuid):
                    invalid_uuids.append((camera.camera_uuid, rule_uuid))

        if invalid_uuids:
            error_messages = [f"Invalid rule UUID format for camera {camera_uuid}: {rule_uuid}" for camera_uuid, rule_uuid in invalid_uuids]
            raise ValueError("Invalid UUIDs found:\n" + "\n".join(error_messages))

        # Initiliaze the camera fetching delay randomization range considering if the all cameras are fetching frames (worst case scenario)
        server_preferences.PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras=len(self.cameras))
            
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

    def return_all_recent_frames_info_as_list(self) -> List[Dict]:
        recent_frames_info: List[Dict] = [] 
        for camera in self.cameras:
            if camera.get_last_frame_info() is not None:
                recent_frames_info.append(camera.get_last_frame_info())
        return recent_frames_info

    def update_frame_evaluations(self, evaluated_frame_uuids:List[str]):
        for camera in self.cameras:
            camera.set_last_frame_as_evaluated_if_frame_uuid_matches(evaluated_frame_uuids)
    
    def return_yolo_models_to_use(self)->List[str]:
        yolo_model_to_use = []
        for camera in self.cameras:
            for rule in camera.active_rules:
                if rule["yolo_model_to_use"] not in yolo_model_to_use:
                    yolo_model_to_use.append(rule["yolo_model_to_use"])

        return yolo_model_to_use
    
    def __test_get_camera_objects_ram_usage_MB(self)->float:
        # Calculate the RAM usage of the camera objects in MB
        try:
            def get_deep_size(obj, seen=None):
                size = sys.getsizeof(obj)
                if seen is None:
                    seen = set()
                obj_id = id(obj)
                if obj_id in seen:
                    return 0
                seen.add(obj_id)
                if isinstance(obj, dict):
                    size += sum(get_deep_size(v, seen) for v in obj.values())
                    size += sum(get_deep_size(k, seen) for k in obj.keys())
                elif hasattr(obj, '__dict__'):
                    size += get_deep_size(obj.__dict__, seen)
                elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
                    size += sum(get_deep_size(i, seen) for i in obj)
                return size

            camera_objects_ram_usage_bytes = sum(get_deep_size(camera) for camera in self.cameras)
            return camera_objects_ram_usage_bytes / 1024 / 1024
        except Exception as e:
            print(f"Error in calculating the RAM usage of the camera objects: {e}")
            return 0

    def __test_show_all_frames(self, window_size=(1280, 720)):
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

# if __name__ == "__main__":

#     server_preferences.PARAM_CAMERA_VERBOSE = False

#     # Fetch and show a single frame from the camera for all cameras
#     print("Printing the camera configurations")
#     with open(server_preferences.PATH_CAMERA_CONFIGS_JSON, "r") as f:
#             camera_configs = json.load(f)["cameras"]    
#     pprint.pprint(camera_configs)
#     time.sleep(10)   

#     print("Testing the CameraStreamFetcher class")
#     cameras = []   
#     for camera_config in camera_configs:         
#         cameras.append(CameraStreamFetcher(**camera_config)) 

#     for camera_index, camera in enumerate(cameras):
#         is_fetched_properly, resolution, frame = camera.test_try_fetching_single_frame_and_show("Test Frame")
#         save_path = f"{server_preferences.PATH_VOLUME}/camera_{str(camera.camera_ip_address).replace('.', '_')}.jpg"
#         cv2.imwrite(save_path, frame)
#         print(f"    {camera_index+1:<3}/ {len(cameras):<3} | {camera.camera_ip_address:<16} | {str(resolution[0])+'x'+str(resolution[1]):<10} -> {'Success' if is_fetched_properly else 'An error occurred'}")
#         print(f"     -----> Saving sample frame to {save_path}")

#     print("Test is completed")
#     cv2.destroyAllWindows()
#     time.sleep(5)

#     # Test the StreamManager class
#     print("\nTesting the StreamManager class")
#     server_preferences.PARAM_CAMERA_VERBOSE = True
#     print("Creating the StreamManager object, which will create the CameraStreamFetcher objects")
#     time.sleep(1)
#     stream_manager = StreamManager()

#     print(f"\n Decoding delay before starting the cameras : {server_preferences.PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE}")
#     print(server_preferences.PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE)
#     time.sleep(1)   

#     print("\nStarting all cameras")
#     stream_manager.start_cameras_by_uuid()
#     print(f"\n Decoding delay before aftar starting the cameras : {server_preferences.PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE}")
    
#     print("\nShowing the frames fetched from the cameras for 20 seconds")
#     start_time = time.time()
#     while time.time() - start_time < 35:
#         stream_manager._StreamManager__test_show_all_frames(window_size=(1280, 720))

#     memory_usage = stream_manager._StreamManager__test_get_camera_objects_ram_usage_MB()
        
#     print("\nStopping all cameras and waiting for 20 seconds")
#     stream_manager.stop_cameras_by_uuid([])
#     time.sleep(20)
    
#     print("\n"+"="*50)
#     print(f"\nMemory usage of the camera objects: {memory_usage:.2f} MB")
#     print("="*50)

#     time.sleep(10)

#     print("\nStarting all cameras again")
#     stream_manager.start_cameras_by_uuid()

#     print("\nShowing the frames fetched from the cameras for 20 seconds")
#     start_time = time.time()
#     while time.time() - start_time < 20:
#         stream_manager._StreamManager__test_show_all_frames(window_size=(1280, 720))
    
#     print("\nStopping all cameras and waiting for the threads to join")
#     stream_manager.stop_cameras_by_uuid([])
    
#     print("Test is completed")

#     exit()








