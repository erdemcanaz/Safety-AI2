import random, threading, time, json, math, uuid, platform, pprint, datetime, re, sys, copy
from pathlib import Path
from typing import Dict, List
import cv2
import numpy as np
import PREFERENCES
import safety_ai_api_dealer_module

class CameraStreamFetcher:
    def __init__(self, **kwargs )->None:  
        
        for key in ['camera_uuid', 'camera_region', 'camera_description', 'camera_status', 'NVR_ip_address', 'camera_ip_address', 'username', 'password', 'stream_path']: # Check if all the required arguments are provided
            if key not in kwargs.keys():
                raise ValueError(f"Missing camera config argument. Required: {key}")

        for key, value in kwargs.items():                       # Assing the arguments to the object
            setattr(self, key, value)

        self.lock = threading.Lock()                            # A lock to prevent race conditions when deep copying the last_frame_info
        self.number_of_frames_decoded = 0                       # The number of frames fetched from the camera    
        self.RTSP_thread = None                                 # The thread that fetches frames from the camera
        self.camera_retrieving_delay_uniform_range = [0, 10]    # The range of uniform distribution for the delay between frame retrievals. Otherwise grab is used where no decoding happens. The delay is calculated as a random number between the range
        self.is_fetching_frames = False                         # A flag to indicate whether the camera is fetching frames or not. If true, the camera is fetching frames. If false, the camera is not fetching frames
        self.last_frame_info = None                             # keys -> frame, camera_uuid, frame_uuid, frame_timestamp, active_rules, is_evaluated
        self.active_rules:List[Dict] = []                       # keys -> # camera_uuid, date_created, date_updated, evaluation_method, rule_department, rule_polygon, rule_type, rule_uuid
        self.last_frame_infos = []                              # A list of the last frame info fetched from the camera. It is used to keep track of the last few frames fetched from the camera
        self.__print_with_header(text = f'CameraStreamFetcher object created for {self.camera_ip_address}')

    def __repr__(self) -> str:
        return f'CameraStreamFetcher({self.camera_ip_address}, camera_status={self.camera_status}, is_fetching_frames={self.is_fetching_frames})'
    
    def __print_with_header(self, text:str = "", pprint_object = None):
        """
        This function prints the text with the header 'CameraStreamFetcher' and the current timestamp. If the pprint_object is provided, it is pretty-printed as well with an indentation.
        """
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {'CameraStreamFetcher':<{PREFERENCES.SAFETY_AI_VERBOSES['header_class_name_width']}} | {text}")
        if pprint_object is not None:
            formatted_text = pprint.pformat(text)   
            for line in formatted_text.splitlines():
                print(f"\t{line}")
        
    def update_active_rules(self, active_rules:List = []):
        self.active_rules = active_rules
    
    def is_camera_status_active(self)->bool:
        return self.camera_status == "active"
    
    def get_last_frame_info(self)->Dict:
        """
        This function is thread-safe. It returns the last frame info fetched from the camera. If no frame is fetched yet, it returns None.
        """
        with self.lock:
            return copy.deepcopy(self.last_frame_info) # To prevent race conditions. Since the self.last_frame_info is continuously updated by the RTSP thread, it is better to return a deep copy of it
    
    def get_last_frame_infos(self)->List[Dict]:
        """
        This function is thread-safe. It returns the last few frame infos fetched from the camera. If no frame is fetched yet, it returns an empty list.
        """
        with self.lock:
            return copy.deepcopy(self.last_frame_infos) # To prevent race conditions. Since the self.last_frame_infos is continuously updated by the RTSP thread, it is better to return a deep copy of it
                                 
    def start_fetching_frames(self):
        if self.RTSP_thread is not None: self.stop_fetching_frames(wait_for_thread_to_join = True)  # Stop the thread if it is already running
        
        self.is_fetching_frames = True
        self.RTSP_thread = threading.Thread(target=self.__IP_camera_frame_fetching_thread)
        self.RTSP_thread.daemon = True                                                              # Set the thread as a daemon means that it will stop when the main program stops
        self.RTSP_thread.start()   
        if PREFERENCES.SAFETY_AI_VERBOSES['frame_fetching_starts']: self.__print_with_header(text = f'Started fetching frames from {self.camera_ip_address}')

    def stop_fetching_frames(self, wait_for_thread_to_join:bool = True):
        self.is_fetching_frames = False  
        if wait_for_thread_to_join and self.RTSP_thread is not None: self.RTSP_thread.join()
        self.RTSP_thread = None
        if PREFERENCES.SAFETY_AI_VERBOSES['frame_fetching_stops']: self.__print_with_header(text = f'Stopped fetching frames from {self.camera_ip_address}')

    def __IP_camera_frame_fetching_thread(self):
        cap = None # cv2 capture object to capture the frames from the camera rtsp stream

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
                            self.last_frame_info["cv2_frame"] = frame
                            self.last_frame_info["camera_uuid"] = self.camera_uuid
                            self.last_frame_info["region_name"] = self.camera_region
                            self.last_frame_info["frame_uuid"] = str(uuid.uuid4())
                            self.last_frame_info["frame_timestamp"] = time.time()
                            self.last_frame_info["active_rules"] = self.active_rules
                            self.number_of_frames_decoded += 1

                            self.last_frame_infos.insert(0, self.last_frame_info) 
                            if len(self.last_frame_infos) > PREFERENCES.MAXIMUM_NUMBER_OF_STORED_FRAMES: self.last_frame_infos.pop(-1) # Keep the last few frames fetched from the camera

                            self.camera_fetching_delay = random.uniform(PREFERENCES.CAMERA_DECODING_RANDOMIZATION_RANGE[0], PREFERENCES.CAMERA_DECODING_RANDOMIZATION_RANGE[1]) # Randomize the fetching delay a little bit so that the cameras are not synchronized which may cause a bottleneck
                            if PREFERENCES.SAFETY_AI_VERBOSES['frame_decoded']: self.__print_with_header(text = f'Frames fetched: {self.number_of_frames_decoded:8d} |: Got a frame from {self.camera_ip_address:<15} | Delay before next decode: {self.camera_fetching_delay:.2f} seconds')
                    else:
                        if PREFERENCES.SAFETY_AI_VERBOSES['frame_decoding_failed']: self.__print_with_header(text = f'Error in decoding frame from {self.camera_ip_address}')
        except Exception as e:
            if PREFERENCES.SAFETY_AI_VERBOSES['error_raised_rtsp']: self.__print_with_header(text = f'Error in fetching frames from {self.camera_ip_address}: {e}')
        finally:
            if cap is not None: cap.release()
            self.is_fetching_frames = False
   
class StreamManager:

    def __init__(self, api_dealer:safety_ai_api_dealer_module.SafetyAIApiDealer = None) -> None:  
        self.api_dealer = api_dealer   
        self.camera_info_dicts ={} # A dict where the key is the camera UUID and the value is the camera info | # NVR_ip_address, camera_description, camera_ip_address, camera_region, camera_status, camera_uuid, date_created, date_updated, password, stream_path, username
        self.last_time_camera_info_dict_updated = 0 # The time when the camera info dictionary was last updated
        self.camera_rules_dicts = {} # A dict where the key is the camera UUID and the value is the camera rules
        self.last_time_camera_rules_dict_updated = 0 # The time when the camera rules dictionary was last updated
        self.camera_stream_fetchers = [] # A list of CameraStreamFetcher objects
        
        self.last_time_server_last_frames_updated = time.time() # The time when the server last frames were updated, not pleasing to update the server last frames immediately since the frames are not fetched yet
        
    def __print_with_header(self, text:str = "", pprint_object = None):
        """
        This function prints the text with the header 'StreamManager' and the current timestamp. If the pprint_object is provided, it is pretty-printed as well with an indentation.
        """
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {'StreamManager':<{PREFERENCES.SAFETY_AI_VERBOSES['header_class_name_width']}} | {text}")
        if pprint_object is not None:
            formatted_text = pprint.pformat(text)   
            for line in formatted_text.splitlines():
                print(f"\t{line}")
        
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
        if(PREFERENCES.SAFETY_AI_VERBOSES['updating_camera_info']):self.__print_with_header(text=f"Checking if camera info is changed")

        # Fetch the camera info from the server and update the camera_info_dict
        response = self.api_dealer.fetch_all_camera_info() 

        if response[0] == False:
            self.__print_with_header(text=f"Error in fetching camera info", pprint_object=response[2])
            return

        # Initialize flags
        is_new_camera_added = False
        is_camera_info_changed = False
        is_camera_removed = False

        pprint.pprint(response)

        fetched_dicts = response[2]["camera_info"] # NVR_ip_address, camera_description, camera_ip_address, camera_region, camera_status, camera_uuid, date_created, date_updated, password, stream_path, username]
        
        # Check for camera UUID collisions
        camera_uuids = [fetched_dict["camera_uuid"] for fetched_dict in fetched_dicts]
        if len(camera_uuids) != len(set(camera_uuids)):
            duplicate_uuids = {uuid for uuid in camera_uuids if camera_uuids.count(uuid) > 1}
            raise ValueError(f"There are cameras with the same UUID: {', '.join(duplicate_uuids)}. Please ensure that each camera has a unique UUID")
        
        # Knowing Camera UUIDs are unique, create a dictionary where the key is the camera UUID and the value is the camera info
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
        self.__print_with_header(text=f"New camera added: {is_new_camera_added}, Camera info changed: {is_camera_info_changed}, Camera removed: {is_camera_removed}")
                                                                        
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
        
        # Check for camera UUID format
        uuid_regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
        invalid_uuid_cameras = [camera_info_dict["camera_uuid"] for camera_info_dict in self.camera_info_dicts.values() if not uuid_regex.match(camera_info_dict["camera_uuid"])]
        if invalid_uuid_cameras:
            raise ValueError(f"Invalid UUID format for cameras: {', '.join(invalid_uuid_cameras)}. Please ensure that each UUID is in the format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        
        # The rules will be fetched separately, assume that there are no active rules for now
        for camera_info_dict in self.camera_info_dicts.values():
            camera_info_dict.update({'active_rules':[]}) 

        # Stop cameras code waits for the threads to join.
        self.stop_cameras_by_uuid([])
        self.camera_stream_fetchers = [] # Garbage collect the old camera stream fetchers
        for camera_info_dict in self.camera_info_dicts.values():
            self.camera_stream_fetchers.append(CameraStreamFetcher(**camera_info_dict))
        self.start_cameras_by_uuid([]) 

    def update_camera_rules(self, update_interval_seconds:float = 30):
        """
        This function periodically fetches updated camera rules from the server and synchronizes the camera_stream_fetchers list with the latest data.
        Every 'update_interval_seconds' seconds, the function retrieves the current camera rules, checking for any new, updated, or removed rules. If changes are detected, the camera_stream_fetchers list is fully refreshed: all existing camera streams are stopped and removed, and new stream fetcher objects are initialized to reflect the latest camera data.
        The function also includes several built-in validation checks:
        - Checks for active rule UUID collisions.
        - Validates active rule UUID formats.
        """
        if time.time() - self.last_time_camera_rules_dict_updated < update_interval_seconds: return
        self.last_time_camera_rules_dict_updated = time.time()
        if PREFERENCES.SAFETY_AI_VERBOSES['updating_camera_info']: self.__print_with_header(text=f"Updating camera rules")

        # Fetch the camera rules from the server and update the camera_rules_dict        
        response = self.api_dealer.fetch_all_rules() # [is_successful, status code, response_data]
        if response[0] == False:
            self.__print_with_header(text=f"Error in fetching camera rules", pprint_object=response[2])
            return
        
        fetched_dicts:List = response[2]["rules"] # camera_uuid, date_created, date_updated, evaluation_method, rule_department, rule_polygon, rule_type, rule_uuid
        active_rule_uuids = [fetched_rule_dict["rule_uuid"] for fetched_rule_dict in fetched_dicts]
        if len(active_rule_uuids) != len(set(active_rule_uuids)):
            duplicate_uuids = {uuid for uuid in active_rule_uuids if active_rule_uuids.count(uuid) > 1}
            raise ValueError(f"There are active rules with the same UUID: {', '.join(duplicate_uuids)}. Please ensure that each active rule has a unique UUID")
        
        # Update the camera rules of the CAMERA STREAM FETCHERS =================================================================================
    
        for camera_stream_fetcher in self.camera_stream_fetchers:
            camera_uuid = camera_stream_fetcher.camera_uuid
            this_camera_related_rule_dicts:List[Dict] = [fetched_rule_dict for fetched_rule_dict in fetched_dicts if fetched_rule_dict["camera_uuid"] == camera_uuid]
            for rule_dict in this_camera_related_rule_dicts:
                rule_polygon_str:str = rule_dict["rule_polygon"].split(",")
                rule_polygon = [(float(rule_polygon_str[i]), float(rule_polygon_str[i+1])) for i in range(0, len(rule_polygon_str), 2)]
                rule_dict["rule_polygon"] = rule_polygon          
            camera_stream_fetcher.update_active_rules(this_camera_related_rule_dicts)
        
    def stop_cameras_by_uuid(self, camera_uuids:List[str]):
        """
        This function stops the camera stream fetchers with the specified camera UUIDs. If no camera UUIDs are provided, all cameras are stopped.
        Since camera fetchers are running in separate threads, the function waits for the threads to join before returning.
        """
        stop_all_cameras = len(camera_uuids) == 0
        for camera in self.camera_stream_fetchers:
            if stop_all_cameras or camera.camera_uuid in camera_uuids:
                camera.stop_fetching_frames()  

    def start_cameras_by_uuid(self, camera_uuids:List[str] = [], max_number_of_cameras:int = PREFERENCES.MAXIMUM_NUMBER_OF_FETCHING_CAMERAS):    
        """
        This function starts the camera stream fetchers with the specified camera UUIDs. If no camera UUIDs are provided, all cameras are started.  
        If the camera is already running, it is stopped and restarted.          
        """
        start_all_alive_cameras = len(camera_uuids) == 0
        started_camera_count = 0
        for camera_stream_fetcher in self.camera_stream_fetchers:
            if started_camera_count >= max_number_of_cameras: break
            if camera_stream_fetcher.is_camera_status_active and (start_all_alive_cameras or camera_stream_fetcher.camera_uuid in camera_uuids):           
                camera_stream_fetcher.start_fetching_frames()
                started_camera_count += 1

    def return_all_recent_frames_info_as_list(self) -> List[Dict]:
        recent_frames_info: List[Dict] = [] 
        for camera in self.camera_stream_fetchers:
            if camera.get_last_frame_info() is not None:
                recent_frames_info.append(camera.get_last_frame_info())
        return recent_frames_info

    def return_last_frame_infos_by_camera_uuid(self, camera_uuid:str) -> List[Dict]:
        for camera in self.camera_stream_fetchers:
            if camera.camera_uuid == camera_uuid:
                return camera.get_last_frame_infos()
        return []
    
    def update_update_server_last_frames(self, most_recent_evaluation_results:Dict = {}, time_interval_seconds:float = 60):
        #TODO: Implement the update_server_last_frames function
        pass

    def show_all_frames(self, window_size=(1280, 720)):
        frames_to_show = []
    
        for camera in self.camera_stream_fetchers:
            frame = camera.get_last_frame_info()["cv2_frame"] if camera.get_last_frame_info() is not None else None
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

    def __test_overwrite_CameraStreamFetchers(self, camera_stream_fetchers):
        self.camera_stream_fetchers = camera_stream_fetchers



