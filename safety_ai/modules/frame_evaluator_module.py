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
            "pose_detection_result": None,      # List of detected people
            "hardhat_detection_result": None,   # List of detected hardhats
            "forklift_detection_result": None,  # List of detected forklifts
        }
        
        evaluation_result['pose_detection_results'] = self.pose_detector.detect_frame(frame_info, bbox_threshold_confidence= PREFERENCES.POSE_MODEL_BBOX_THRESHOLD_CONFIDENCE)
        evaluation_result['flags']['is_person_detected'] = len(evaluation_result['pose_detection_results']) > 0
        
        print(f"{frame_info['camera_uuid']} Number of people detected: {len(evaluation_result['pose_detection_results'])}")
        
        # frame_rules:List[Dict] = frame_info["active_rules"]        
        # self.hardhat_detector.detect_frame(frame_info)
        # self.forklift_detector.detect_frame(frame_info)
        # self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = frame_info["frame_uuid"]
    




