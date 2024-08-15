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
        self.recent_detection_results: Dict = None

    def __repr__(self):
        return f"PoseDetector(model_name={self.MODEL_PATH})"
    
    def __clear_recent_detection_results(self):
        self.recent_detection_results = {
            "frame_uuid": None,
            "normalized_bboxes": [], # List of normalized bounding boxes in the format [x1n, y1n, x2n, y2n, bbox_confidence, normalized_keypoints_dict]
        }
    
    def detect_frame(self, frame_info:np.ndarray = None):
        self.__clear_recent_detection_results()
        self.recent_detection_results["frame_uuid"] = frame_info["frame_uuid"]

        detections = self.yolo_object(frame_info["frame"], task = "pose", verbose= server_preferences.POSE_DETECTION_VERBOSE)[0]        
        for detection in detections:

            boxes = detection.boxes
            box_cls_no = int(boxes.cls.cpu().numpy()[0])
            box_cls_name = self.yolo_object.names[box_cls_no]
            if box_cls_name not in ["person"]:
                continue

            box_conf = boxes.conf.cpu().numpy()[0]
            box_xyxyn = boxes.xyxyn.cpu().numpy()[0]

            key_points = detection.keypoints  # Keypoints object for pose outputs
            keypoint_confs = key_points.conf.cpu().numpy()[0]
            keypoints_xyn = key_points.xyn.cpu().numpy()[0]

            normalized_keypoints_dict = {}  
            for keypoint_index, keypoint_name in enumerate(PoseDetector.KEYPOINT_NAMES):
                keypoint_xn = keypoints_xyn[keypoint_index][0]
                keypoint_yn = keypoints_xyn[keypoint_index][1]
                keypoint_conf = keypoint_confs[keypoint_index] 
                if keypoint_xn == 0 and keypoint_yn == 0: #if the keypoint is not detected
                    #But this is also a prediction. Thus the confidence should not be set to zero. negative values are used to indicate that the keypoint is not detected
                    keypoint_conf = -keypoint_conf
                normalized_keypoints_dict[keypoint_name] = [keypoint_xn, keypoint_yn, keypoint_conf]

            self.recent_detection_results["normalized_bboxes"].append([box_xyxyn[0], box_xyxyn[1], box_xyxyn[2], box_xyxyn[3], box_conf, normalized_keypoints_dict])

    def get_recent_detection_results(self) -> Dict:
        return self.recent_detection_results
    
class HardhatDetector():
    HARD_HAT_MODEL_PATHS = {
        "hardhat_detector":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'hardhat_detector.pt'}",
    }

    def __init__(self, model_name):
        if model_name not in HardhatDetector.HARD_HAT_MODEL_PATHS.keys():
            raise ValueError(f"Invalid model name. Available models are: {HardhatDetector.HARD_HAT_MODEL_PATHS.keys()}")
        self.MODEL_PATH = HardhatDetector.HARD_HAT_MODEL_PATHS[model_name]
        self.yolo_object = YOLO( self.MODEL_PATH, verbose= server_preferences.HARDHAT_DETECTION_VERBOSE)

        self.recent_detection_results:Dict = None # This will be a list of dictionaries, each dictionary will contain the prediction results for a single detection
    
    def __repr__(self) -> str:
        return f"HardhatDetector(model_name={self.MODEL_PATH})"
    
    def __clear_recent_detection_results(self):
        self.recent_detection_results = {
            "frame_uuid": None,
            "normalized_bboxes": [], # List of normalized bounding boxes in the format [x1n, y1n, x2n, y2n, bbox_confidence]
        }

    def detect_frame(self, frame_info:np.ndarray = None):
        self.__clear_recent_detection_results()
        self.recent_detection_results["frame_uuid"] = frame_info["frame_uuid"]

        detections = self.yolo_object(frame_info["frame"], task = "hardhat", verbose= server_preferences.HARDHAT_DETECTION_VERBOSE)[0]
        print(self.yolo_object.names)
        for detection in detections:
            boxes = detection.boxes
            box_cls_no = int(boxes.cls.cpu().numpy()[0])
            box_cls_name = self.yolo_object.names[box_cls_no]
            if box_cls_name not in ["helmet"]:
                continue

            box_conf = boxes.conf.cpu().numpy()[0]
            box_xyxyn = boxes.xyxyn.cpu().numpy()[0]
            self.recent_detection_results["normalized_bboxes"].append([box_xyxyn[0], box_xyxyn[1], box_xyxyn[2], box_xyxyn[3], box_conf])

class ForkliftDetector():
    FORKLIFT_MODEL_PATHS = {
        "forklift_detector":f"{Path(__file__).resolve().parent / 'trained_yolo_models' / 'forklift_detector.pt'}",
    }

    def __init__(self, model_name):
        if model_name not in ForkliftDetector.FORKLIFT_MODEL_PATHS.keys():
            raise ValueError(f"Invalid model name. Available models are: {ForkliftDetector.FORKLIFT_MODEL_PATHS.keys()}")
        self.MODEL_PATH = ForkliftDetector.FORKLIFT_MODEL_PATHS[model_name]
        self.yolo_object = YOLO( self.MODEL_PATH, verbose= server_preferences.FORKLIFT_DETECTION_VERBOSE)
        self.recent_detection_results:Dict = None # This will be a list of dictionaries, each dictionary will contain the prediction results for a single detection

    def __repr__(self) -> str:
        return f"ForkliftDetector(model_name={self.MODEL_PATH})"
    
    def __clear_recent_detection_results(self):
        self.recent_detection_results = {
            "frame_uuid": None,
            "normalized_bboxes": [], # List of normalized bounding boxes in the format [x1n, y1n, x2n, y2n, bbox_confidence]
        }

    def detect_frame(self, frame_info:np.ndarray = None):
        self.__clear_recent_detection_results()
        self.recent_detection_results["frame_uuid"] = frame_info["frame_uuid"]

        detections = self.yolo_object(frame_info["frame"], task = "forklift", verbose= server_preferences.FORKLIFT_DETECTION_VERBOSE)[0]
        for detection in detections:
            boxes = detection.boxes
            box_cls_no = int(boxes.cls.cpu().numpy()[0])
            box_cls_name = self.yolo_object.names[box_cls_no]
            print(self.yolo_object.names)
            if box_cls_name not in ["forklift"]:
                continue

            box_conf = boxes.conf.cpu().numpy()[0]
            box_xyxyn = boxes.xyxyn.cpu().numpy()[0]
            self.recent_detection_results["normalized_bboxes"].append([box_xyxyn[0], box_xyxyn[1], box_xyxyn[2], box_xyxyn[3], box_conf])
    
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

            

