import pprint
import PREFERENCES
import models_module
import cv2
import numpy as np
from typing import List, Dict
import copy

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
    
    def __is_inside_another_bbox(self, normalized_bbox1:List[float], normalized_bbox2:List[float], intersection_percentage_threshold:float = 0.5) -> bool:
        # Check the percentage of the normalized_bbox1 is inside the normalized_bbox2 wrt. the normalized_bbox1
        # The normalized_bbox is in the form of [x1, y1, x2, y2] where x1, y1 is the top-left corner and x2, y2 is the bottom-right corner
        # The percentage is the percentage of the normalized_bbox1 that should be inside the normalized_bbox2
        # if  bbox_1 = [0.4, 0.4, 0.8, 0.8] and bbox_2 = [0.0, 0.0, 0.6, 0.6], then the intersectio percentage is 0.25

        intersection_bbox = [max(normalized_bbox1[0], normalized_bbox2[0]), max(normalized_bbox1[1], normalized_bbox2[1]), min(normalized_bbox1[2], normalized_bbox2[2]), min(normalized_bbox1[3], normalized_bbox2[3])]
        if intersection_bbox[0] >= intersection_bbox[2] or intersection_bbox[1] >= intersection_bbox[3]: return False
        intersection_area = (intersection_bbox[2] - intersection_bbox[0]) * (intersection_bbox[3] - intersection_bbox[1])
        bbox1_area = (normalized_bbox1[2] - normalized_bbox1[0]) * (normalized_bbox1[3] - normalized_bbox1[1])
        pprint.pprint(intersection_area/bbox1_area)
        return intersection_area/bbox1_area >= intersection_percentage_threshold

    def __gaussian_blur_bbox(self, normalized_bbox:List[int], frame:np.ndarray, kernel_size:int = PREFERENCES.PERSON_BBOX_BLUR_KERNEL_SIZE):
        # Apply the Gaussian blur to the bbox of the frame
        # The bbox is in the form of [x1, y1, x2, y2]
        # The kernel_size is the size of the Gaussian kernel (ODD number)
        x1,y1,x2,y2 = self.__translate_normalized_bbox_to_frame_bbox(normalized_bbox=normalized_bbox, frame=frame)
        frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], (kernel_size, kernel_size), 0)
        return frame
    
    def __draw_rect_on_frame(self, normalized_bbox:List[int], frame:np.ndarray, color:List[int]=[0, 255, 0], thickness:int=2):
        # Draw a rectangle on the frame
        # The normalized bbox is in the form of [x1, y1, x2, y2]
        # The frame is the numpy array of the frame
        x1, y1, x2, y2 = self.__translate_normalized_bbox_to_frame_bbox(normalized_bbox=normalized_bbox, frame=frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    def __translate_normalized_bbox_to_frame_bbox(self, normalized_bbox:List[int], frame:np.ndarray) -> List[int]:
        # Translate the normalized bbox to the frame bbox
        # The normalized bbox is in the form of [x1, y1, x2, y2]
        # The frame is the numpy array of the frame
        frame_width, frame_height = frame.shape[1], frame.shape[0]
        x1, y1, x2, y2 = normalized_bbox
        x1, y1, x2, y2 = int(x1*frame_width), int(y1*frame_height), int(x2*frame_width), int(y2*frame_height)
        return [x1, y1, x2, y2]
    
    def evaluate_frame(self, frame_info:np.ndarray):
        # Check if the frame is already evaluated, if so, return
        if frame_info["camera_uuid"] in self.recenty_evaluated_frame_uuids_wrt_camera and frame_info["frame_uuid"] == self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]]: return
        self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = frame_info["frame_uuid"]    

        evaluation_result = {
            "frame_info": frame_info,
            "processed_frame": copy.deepcopy(frame_info),            # The frame that is processed by the frame evaluator (e.g., blurring the bbox of the person)
            "flags":{
                "is_person_detected": False,
                "is_violation_detected": False,
            },          
            "pose_detection_result": None,      # Detect_frame result of the pose detector List of Dict
            "hardhat_detection_result": None,   # Detect_frame result of the hardhat detector List of Dict
            "forklift_detection_result": None,  # Detect_frame result of the forklift detector List of Dict 
            "violated_rules": []                # List of violated rules to be reported
        }   

        #============================detect_frame=======================================================
        #"detector_uuid": self.DETECTOR_UUID,
        #"detection_class": <> # The class that the detector is detecting
        #"frame_uuid": <> # The UUID of the frame 
        #"detections": [], # Contains multiple persons: List of dict of detection results for each person: {"bbox_class_name": str, "bbox_confidence": float, "bbox": [x1, y1, x2, y2], "normalized_keypoints": {$keypoint_name: [xn, yn, confidence]}}
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

        # TODO blur the bbox of the persons
        normalized_person_bboxes_to_blur = [detection['normalized_bbox'] for detection in evaluation_result['pose_detection_results']['detections']]
        for normalized_bbox in normalized_person_bboxes_to_blur:
            self.__gaussian_blur_bbox(normalized_bbox = normalized_bbox, frame= evaluation_result['processed_frame'], kernel_size= PREFERENCES.PERSON_BBOX_BLUR_KERNEL_SIZE)
            self.__draw_rect_on_frame(normalized_bbox, evaluation_result['processed_frame'], color=[169, 69, 0], thickness=1)

    def __restricted_area_violation_isg_v1(self, evaluation_result:Dict, rule_info:Dict):
        # ===============================================================================================
        # evaluation type: restricted_area_violation ||| evaluation method: v1
        # If a person ankle is inside the restricted area, then it is a violation.
        # VIOLATION SCORE -> bbox_confidence * (mean of the confidence of the left and right ankle)
        # Exception: If the person is inside the forklift, then it is not a violation.
        #================================================================================================

        frame_info = evaluation_result['frame_info']
        rule_polygon = rule_info['rule_polygon']   
        
        # Ensure that the pose detection results are available
        if evaluation_result['pose_detection_results'] is None: raise Exception("Pose detection results are not available for the restricted area violation evaluation")
        
        # Get the forklift bboxes so that we can exclude them from the violation detection
        evaluation_result['forklift_detection_results'] = self.forklift_detector.detect_frame(frame_info, bbox_threshold_confidence= PREFERENCES.FORKLIFT_MODEL_BBOX_THRESHOLD_CONFIDENCE)
        normalized_forklift_bboxes = [detection['normalized_bbox'] for detection in evaluation_result['forklift_detection_results']['detections']]

        # Check if the ankle of the person is inside the restricted area
        # {"bbox_class_name": str, "bbox_confidence": float, "bbox": [x1, y1, x2, y2], "normalized_keypoints": {$keypoint_name: [xn, yn, confidence]}}
        for detection in evaluation_result['pose_detection_results']['detections']:

            # Check if the person is inside the forklift, if so, continue
            normalized_bbox = detection['normalized_bbox']
            is_person_inside_forklift = False
            for normalized_forklift_bbox in normalized_forklift_bboxes:
                if self.__is_inside_another_bbox(normalized_bbox, normalized_forklift_bbox, intersection_percentage_threshold = 0.5):
                    is_person_inside_forklift = True
                    break
            if is_person_inside_forklift: continue

            # Check if the ankle of the person is inside the restricted area
            normalized_keypoints = detection['normalized_keypoints']
            left_ankle = normalized_keypoints['left_ankle']
            right_ankle = normalized_keypoints['right_ankle']
            is_left_ankle_in_restricted_area = self.__is_normalized_point_inside_polygon(left_ankle, rule_polygon) if left_ankle[2] > 0 else False # negative confidence means that the keypoint is not detected
            is_right_ankle_in_restricted_area = self.__is_normalized_point_inside_polygon(right_ankle, rule_polygon) if right_ankle[2] > 0 else False # negative confidence means that the keypoint is not detected
        
            if is_left_ankle_in_restricted_area or is_right_ankle_in_restricted_area and not is_person_inside_forklift:
                violation_score = detection["bbox_confidence"] * (is_left_ankle_in_restricted_area * left_ankle[2] + is_right_ankle_in_restricted_area* right_ankle[2])/(is_left_ankle_in_restricted_area + is_right_ankle_in_restricted_area)
                print(f"Violation detected for rule_uuid: {rule_info['rule_uuid']}, violation_score: {violation_score}")

                self.__draw_rect_on_frame(normalized_bbox, frame_info['processed_frame'], color=[0, 0, 255], thickness=5)
                resized_frame = cv2.resize(frame_info['processed_frame'], (500, 500))
                cv2.imshow("violation_v1", resized_frame)

            #prepare the frame to be reported: add text, add timestamp, etc.

    def __restricted_area_violation_isg_v2(self, evaluation_result:Dict, rule_info:Dict):
        # ===============================================================================================
        # evaluation type: restricted_area_violation ||| evaluation method: v2
        # If people bbox-center is inside the restricted area, then it is a violation.
        # VIOLATION SCORE -> bbox_confidence
        # Exception: If the person is inside the forklift, then it is not a violation.
        #================================================================================================
        frame_info = evaluation_result['frame_info']
        rule_polygon = rule_info['rule_polygon']   

        # Ensure that the pose detection results are available
        if evaluation_result['pose_detection_results'] is None: raise Exception("Pose detection results are not available for the restricted area violation evaluation")
        
        # Get the forklift bboxes so that we can exclude them from the violation detection
        evaluation_result['forklift_detection_results'] = self.forklift_detector.detect_frame(frame_info, bbox_threshold_confidence= PREFERENCES.FORKLIFT_MODEL_BBOX_THRESHOLD_CONFIDENCE)
        normalized_forklift_bboxes = [detection['normalized_bbox'] for detection in evaluation_result['forklift_detection_results']['detections']]

        # {"bbox_class_name": str, "bbox_confidence": float, "normalized_bbox": [x1n, y1n, x2n, y2n], "keypoints": {$keypoint_name: [xn, yn, confidence]}}
        # Check if the bbox-center of the person is inside the restricted area and not inside the forklift
        for detection in evaluation_result['pose_detection_results']['detections']:            
            normalized_bbox = detection['normalized_bbox']
            normalized_bbox_center = [(normalized_bbox[0]+normalized_bbox[2])/2, (normalized_bbox[1]+normalized_bbox[3])/2]
            
            # Check if the person is inside the forklift, if so, continue
            is_person_inside_forklift = False
            for normalized_forklift_bbox in normalized_forklift_bboxes:
                if self.__is_inside_another_bbox(normalized_bbox, normalized_forklift_bbox, intersection_percentage_threshold = 0.5):
                    is_person_inside_forklift = True
                    break
            if is_person_inside_forklift: continue
            
            is_person_in_restricted_area = self.__is_normalized_point_inside_polygon(normalized_bbox_center, rule_polygon)
            if is_person_in_restricted_area:
                violation_score = detection["bbox_confidence"]
                print(f"Violation detected for rule_uuid: {rule_info['rule_uuid']} violation_score: {violation_score}")
                self.__draw_rect_on_frame(normalized_bbox, frame_info['processed_frame'], color=[0, 0, 255], thickness=5)
                resized_frame = cv2.resize(frame_info['processed_frame'], (500, 500))
                cv2.imshow("violation_v2", resized_frame)

                
        #prepare the frame to be reported: add text, add timestamp, etc.
        
    def __hardhat_violation_isg_v1(self, evaluation_result:Dict, rule_info:Dict):
        pass