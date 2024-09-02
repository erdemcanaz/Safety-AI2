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
        
    def __is_normalized_point_inside_polygon(self, point:List[float], polygon:List[List[float]]) -> bool:
        # Check if the point is inside the polygon
        # The polygon is a list of points in the form of [x, y]
        # The point is a list of points in the form of [x, y]
        # The polygon is a closed polygon, i.e., the last point is the same as the first point
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
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
            "violated_rules": []                # List of violated rules
        }   

        #============================detect_frame=======================================================
        #"detector_uuid": self.DETECTOR_UUID,
        #"detection_class": <> # The class that the detector is detecting
        #"frame_uuid": <> # The UUID of the frame 
        #"detections": [], # Contains multiple persons: List of dict of detection results for each person: {"bbox_class_name": str, "bbox_confidence": float, "bbox": [x1, y1, x2, y2], "keypoints": {$keypoint_name: [xn, yn, confidence]}}
        #================================================================================================

        # No matter what, the pose detection is done for each frame
        evaluation_result['pose_detection_results'] = self.pose_detector.detect_frame(frame_info, bbox_threshold_confidence= PREFERENCES.POSE_MODEL_BBOX_THRESHOLD_CONFIDENCE)
        evaluation_result['flags']['is_person_detected'] = len(evaluation_result['pose_detection_results']['detections']) > 0
        
        # Evaluate the frame for each active rule
        for active_rule in frame_info['active_rules']: #rule_uuid, camera_uuid, rule_type, evaluation_method, rule_department, rule_polygon, threshold_value
            # Restricted area violation
            if active_rule['rule_type'] == "restricted_area_violation" and active_rule['rule_department'] == "ISG":
                if active_rule['evaluation_method'] == "v1":
                    self.__restricted_area_violation_isg_v1(evaluation_result=  evaluation_result, rule_info = active_rule)
                elif active_rule['evaluation_method'] == "v2":
                    self.__restricted_area_violation_isg_v2(evaluation_result = evaluation_result, rule_info= active_rule)
                else:
                    raise Exception(f"Unknown evaluation method: {active_rule['evaluation_method']} for rule type: {active_rule['rule_type']}")
            elif active_rule['rule_type'] == "hardhat_violation":
                if active_rule['evaluation_method'] == "v1":
                    self.__hardhat_violation_isg_v1(evaluation_result=  evaluation_result, rule_info = active_rule)
                else:
                    raise Exception(f"Unknown evaluation method: {active_rule['evaluation_method']} for rule type: {active_rule['rule_type']}")
            else:
                raise Exception(f"Unknown rule type: {active_rule['rule_type']} or rule department: {active_rule['rule_department']}")
                
    def __restricted_area_violation_isg_v1(self, evaluation_result:Dict, rule_info:Dict):
        # TODO: Implement this function later on
        return 
    
        # If a person ankle (either left OR right) is inside the restricted area, then it is a violation.
        if evaluation_result['pose_detection_results'] is None: raise Exception("Pose detection results are not available for the restricted area violation evaluation")
        
        # Check if a person is detected
        if len(evaluation_result['pose_detection_results']['detections']) == 0: return # No person is detected, so no violation

        # Check if the ankle of the person is inside the restricted area
        # {"bbox_class_name": str, "bbox_confidence": float, "bbox": [x1, y1, x2, y2], "keypoints": {$keypoint_name: [xn, yn, confidence]}}

    def __restricted_area_violation_isg_v2(self, evaluation_result:Dict, rule_info:Dict):
        # ===============================================================================================
        # If people bbox-center is inside the restricted area, then it is a violation.
        # Exception: If the person is inside the forklift, then it is not a violation.
        #================================================================================================
        frame_info = evaluation_result['frame_info']
        rule_polygon = rule_info['rule_polygon']   

        # Ensure that the pose detection results are available
        if evaluation_result['pose_detection_results'] is None: raise Exception("Pose detection results are not available for the restricted area violation evaluation")
        
        # Get the forklift bboxes so that we can exclude them from the violation detection
        evaluation_result['forklift_detection_results'] = self.forklift_detector.detect_frame(frame_info, bbox_threshold_confidence= PREFERENCES.FORKLIFT_MODEL_BBOX_THRESHOLD_CONFIDENCE)
        forklift_bboxes = [detection['normalized_bbox'] for detection in evaluation_result['forklift_detection_results']['detections']]
        pprint.pprint(forklift_bboxes)

        for forklift_bbox in forklift_bboxes:
            cv2.rectangle(frame_info['cv2_frame'], (int(forklift_bbox[0]*frame_info['cv2_frame'].shape[1]), int(forklift_bbox[1]*frame_info['cv2_frame'].shape[0])), (int(forklift_bbox[2]*frame_info['cv2_frame'].shape[1]), int(forklift_bbox[3]*frame_info['cv2_frame'].shape[0])), (0, 0, 255), 2)
        if len(forklift_bboxes) > 0:
            resized_frame = cv2.resize(frame_info['cv2_frame'], (320, 320))
            cv2.imshow("forklift", resized_frame)

        # {"bbox_class_name": str, "bbox_confidence": float, "normalized_bbox": [x1n, y1n, x2n, y2n], "keypoints": {$keypoint_name: [xn, yn, confidence]}}
        for detection in evaluation_result['pose_detection_results']['detections']:
            bbox = detection['normalized_bbox']
            bbox_center = [(bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2]
            if self.__is_normalized_point_inside_polygon(bbox_center, rule_polygon):
                print(f"Violation detected for rule_uuid: {rule_info['rule_uuid']}")

            resized_frame = cv2.resize(frame_info['cv2_frame'], (320, 320))
            cv2.imshow("frame", resized_frame)

    def __hardhat_violation_isg_v1(self, evaluation_result:Dict, rule_info:Dict):
        pass
