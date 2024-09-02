import pprint
import PREFERENCES
import models_module
import cv2
import numpy as np
from typing import List, Dict

class FrameEvaluator():

    def __init__(self):
        self.pose_detector= models_module.PoseDetector(model_name=PREFERENCES.USED_MODELS["pose_detection_model_name"])
        self.hardhat_detector = models_module.HardhatDetector(model_name=PREFERENCES.USED_MODELS["hardhat_detection_model_name"])
        self.forklift_detector = models_module.ForkliftDetector(model_name=PREFERENCES.USED_MODELS["forklift_detection_model_name"])     
        
        self.recenty_evaluated_frame_uuids_wrt_camera = {} # Keep track of the  UUID of the last frame that is evaluated for each camera
        
    def evaluate_frame(self, frame_info:np.ndarray):
        # Check if the frame is already evaluated, if so, return
        if frame_info["camera_uuid"] in self.recenty_evaluated_frame_uuids_wrt_camera and frame_info["frame_uuid"] == self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]]: return
        self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = frame_info["frame_uuid"]    

        evaluation_result = {
            "frame_info": frame_info,
            "flags":{
                "is_person_detected": False,
                "is_violation_detected": False,
            },          
            "pose_detection_result": None,      # Detect_frame result of the pose detector
            "hardhat_detection_result": None,   # Detect_frame result of the hardhat detector
            "forklift_detection_result": None,  # Detect_frame result of the forklift detector
        }   

        #============================detect_frame=======================================================
        #"detector_uuid": self.DETECTOR_UUID,
        #"detection_class": <> # The class that the detector is detecting
        #"frame_uuid": <> # The UUID of the frame 
        #"detections": [], # Contains multiple persons: List of dict of detection results for each person: {"bbox_class_name": str, "bbox_confidence": float, "bbox": [x1, y1, x2, y2], "keypoints": {$keypoint_name: [xn, yn, confidence]}}
        #================================================================================================

        evaluation_result['pose_detection_results'] = self.pose_detector.detect_frame(frame_info, bbox_threshold_confidence= PREFERENCES.POSE_MODEL_BBOX_THRESHOLD_CONFIDENCE)
        evaluation_result['flags']['is_person_detected'] = len(evaluation_result['pose_detection_results']['detections']) > 0
        
        print(f"{frame_info['camera_uuid']} Number of people detected: {len(evaluation_result['pose_detection_results']['detections'])}")#NOTE: DEBUG_PRINT
        
        pprint.pprint(frame_info['active_rules'])
        # frame_rules:List[Dict] = frame_info["active_rules"]        
        # self.hardhat_detector.detect_frame(frame_info)
        # self.forklift_detector.detect_frame(frame_info)
        # self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = frame_info["frame_uuid"]
    
