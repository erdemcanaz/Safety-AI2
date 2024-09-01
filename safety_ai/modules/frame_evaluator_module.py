import pprint
import PREFERENCES
import models_module
import cv2
import numpy as np

class FrameEvaluator():

    def __init__(self):
        self.pose_detector= models_module.PoseDetector(model_name=PREFERENCES.USED_MODELS["pose_detection_model_name"])
        self.hardhat_detector = models_module.HardhatDetector(model_name=PREFERENCES.USED_MODELS["hardhat_detection_model_name"])
        self.forklift_detector = models_module.ForkliftDetector(model_name=PREFERENCES.USED_MODELS["forklift_detection_model_name"])     
        
        self.recenty_evaluated_frame_uuids_wrt_camera = {} # Keep track of the  UUID of the last frame that is evaluated for each camera
        
    def evaluate_frame(self, frame_info:np.ndarray):
        pprint.pprint(frame_info["active_rules"])
        self.pose_detector.detect_frame(frame_info)
        self.hardhat_detector.detect_frame(frame_info)
        self.forklift_detector.detect_frame(frame_info)
        self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = frame_info["frame_uuid"]
    




