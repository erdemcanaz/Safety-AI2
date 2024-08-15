#Built-in imports
import time,pprint,copy, uuid, pprint, math, time, os
from pathlib import Path
from typing import List, Dict, Tuple #for python3.8 compatibility
#3rd party imports
from ultralytics import YOLO
import numpy as np
import cv2
#Local imports
#import modules.server_preferences as server_preferences
import server_preferences

class PoseDetector(): 
    #keypoints detected by the model in the detection order
    KEYPOINT_NAMES = ["nose", "right_eye", "left_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder", "left_elbow" ,"right_elbow","left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
    POSE_MODEL_PATHS = {
        "yolov8n-pose":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'yolov8n-pose.pt'}",
        "yolov8s-pose":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'yolov8s-pose.pt'}",
        "yolov8m-pose":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'yolov8m-pose.pt'}",
        "yolov8l-pose":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'yolov8l-pose.pt'}",
        "yolov8x-pose":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'yolov8x-pose.pt'}",
    }

    def __init__(self, model_name: str = None ) -> None:   
        if model_name not in PoseDetector.POSE_MODEL_PATHS.keys():
            raise ValueError(f"Invalid model name. Available models are: {PoseDetector.POSE_MODEL_PATHS.keys()}")
        self.MODEL_PATH = PoseDetector.POSE_MODEL_PATHS[model_name]        
        self.yolo_object = YOLO( self.MODEL_PATH, verbose= server_preferences.POSE_DETECTION_VERBOSE)        
        self.recent_detection_results = None

    def __repr__(self):
        return f"PoseDetector(model_name={self.MODEL_PATH})"
    
    def __get_empty_prediction_dict_template(self) -> dict:
        empty_prediction_dict = {   
                    "common_keys":{
                        "DETECTOR_TYPE":"PoseDetector",                             # which detector made this prediction
                        "frame": None,                                              # frame in which the detection was made
                        "camera_uuid":"",                                           # unique id for the camera
                        "frame_uuid":"",                                            # unique id for the frame
                        "detection_uuid":str(uuid.uuid4()),                         # unique id for the detection
                        "frame_timestamp":0,                                        # timestamp of the detection
                        "frame_shape": [0,0],                                       # [0,0], [height , width] in pixels
                        "class_name":"",                                            # hard_hat, no_hard_hat
                        "bbox_confidence":0,                                        # 0.0 to 1.0
                        "bbox_xyxy_px":[0,0,0,0],                                   # [x1,y1,x2,y2] in pixels
                        "bbox_center_px": [0,0],                                    # [x,y] in pixels
                    },
                    #------------------pose specific fields------------------
                    "unique_keys":{ # Any other information that is not covered by the fields above
                        "keypoints": { # Keypoints are in the format [x,y,confidence]
                            "left_eye": [0,0,0,0,0],
                            "right_eye": [0,0,0,0,0],
                            "nose": [0,0,0,0,0],
                      
                            "left_shoulder": [0,0,0,0,0],
                            "right_shoulder": [0,0,0,0,0],
                            "left_elbow": [0,0,0,0,0],
                            "right_elbow": [0,0,0,0,0],
                            "left_wrist": [0,0,0,0,0],
                            "right_wrist": [0,0,0,0,0],
                            "left_hip": [0,0,0,0,0],
                            "right_hip": [0,0,0,0,0],
                            "left_knee": [0,0,0,0,0],
                            "right_knee": [0,0,0,0,0],
                            "left_ankle": [0,0,0,0,0],
                            "right_ankle": [0,0,0,0,0],
                        }
                    },                                            
                   
        }
        return empty_prediction_dict
    
    def detect_frame(self, frame_info:np.ndarray = None) -> List[Dict]:
        self.recent_prediction_results = []
        detections = self.yolo_object(frame_info["frame"], task = "pose", verbose= server_preferences.POSE_DETECTION_VERBOSE)[0]
        
        for detection in detections:
            boxes = detection.boxes
            box_cls_no = int(boxes.cls.cpu().numpy()[0])
            box_cls_name = self.yolo_object.names[box_cls_no]
            if box_cls_name not in ["person"]:
                continue
            box_conf = boxes.conf.cpu().numpy()[0]
            box_xyxyn = boxes.xyxyn.cpu().numpy()[0]

            # prediction_dict_template = self.__get_empty_prediction_dict_template()
            # prediction_dict_template["common_keys"]["frame"] = frame
            # prediction_dict_template["common_keys"]["camera_uuid"] = camera_uuid
            # prediction_dict_template["common_keys"]["frame_uuid"] = frame_uuid
            # prediction_dict_template["common_keys"]["detection_uuid"] = str(uuid.uuid4()) #unique id for the detection
            # prediction_dict_template["common_keys"]["frame_timestamp"] = frame_timestamp
            # prediction_dict_template["common_keys"]["frame_shape"] = list(results.orig_shape)
            # prediction_dict_template["common_keys"]["class_name"] = box_cls_name
            # prediction_dict_template["common_keys"]["bbox_confidence"] = box_conf
            # prediction_dict_template["common_keys"]["bbox_xyxy_px"] = box_xyxy # Bounding box in the format [x1,y1,x2,y2]
            # prediction_dict_template["common_keys"]["bbox_center_px"] = [ (box_xyxy[0]+box_xyxy[2])/2, (box_xyxy[1]+box_xyxy[3])/2]
            
            key_points = detection.keypoints  # Keypoints object for pose outputs
            keypoint_confs = key_points.conf.cpu().numpy()[0]
            keypoints_xy = key_points.xyn.cpu().numpy()[0]
                       
            for keypoint_index, keypoint_name in enumerate(PoseDetector.KEYPOINT_NAMES):
                keypoint_conf = keypoint_confs[keypoint_index] 
                keypoint_x = keypoints_xy[keypoint_index][0]
                keypoint_y = keypoints_xy[keypoint_index][1]
                if keypoint_x == 0 and keypoint_y == 0: #if the keypoint is not detected
                    #But this is also a prediction. Thus the confidence should not be set to zero. negative values are used to indicate that the keypoint is not detected
                    keypoint_conf = -keypoint_conf

                prediction_dict_template["unique_keys"]["keypoints"][keypoint_name] = [keypoint_x, keypoint_y , keypoint_conf]

            self.recent_prediction_results.append(prediction_dict_template)

        return self.recent_prediction_results

class HardhatDetector():
    HARD_HAT_MODEL_PATHS = {
        "hardhat_detector":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'hardhat_detector.pt'}",
    }

    def __init__(self, model_name):
        if model_name not in HardhatDetector.HARD_HAT_MODEL_PATHS.keys():
            raise ValueError(f"Invalid model name. Available models are: {HardhatDetector.HARD_HAT_MODEL_PATHS.keys()}")
        self.MODEL_PATH = HardhatDetector.HARD_HAT_MODEL_PATHS[model_name]
        self.yolo_object = YOLO( self.MODEL_PATH, verbose= server_preferences.HARDHAT_DETECTION_VERBOSE)
        #self.recent_prediction_results:List[Dict] = None # This will be a list of dictionaries, each dictionary will contain the prediction results for a single detection

    def __repr__(self) -> str:
        return f"HardhatDetector(model_name={self.MODEL_PATH})"
    
class ForkliftDetector():
    FORKLIFT_MODEL_PATHS = {
        "forklift_detector":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'forklift_detector.pt'}",
    }

    def __init__(self, model_name):
        if model_name not in ForkliftDetector.FORKLIFT_MODEL_PATHS.keys():
            raise ValueError(f"Invalid model name. Available models are: {ForkliftDetector.FORKLIFT_MODEL_PATHS.keys()}")
        self.MODEL_PATH = ForkliftDetector.FORKLIFT_MODEL_PATHS[model_name]
        self.yolo_object = YOLO( self.MODEL_PATH, verbose= server_preferences.FORKLIFT_DETECTION_VERBOSE)
        #self.recent_prediction_results:List[Dict] = None # This will be a list of dictionaries, each dictionary will contain the prediction results for a single detection

    def __repr__(self) -> str:
        return f"ForkliftDetector(model_name={self.MODEL_PATH})"
    
if __name__ == "__main__":
    last_time_detection = time.time()
    username = input("Enter the username: ")
    password = input("Enter the password: ")
    camera_ip_address = input("Enter the camera ip address: ")

    try:
        print("Connecting to the camera...")
        url = f'rtsp://{username}:{password}@{camera_ip_address}/{"profile2/media.smp"}'
        cap = cv2.VideoCapture(url)
        buffer_size_in_frames = 1
        cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)

        while True:   
            ret, frame = cap.read()
            if ret:
              if time.time() - last_time_detection > 0.5:
                last_time_detection = time.time()
                cv2.imshow("frame", frame)
    
    except Exception as e:
        print(e)

            

