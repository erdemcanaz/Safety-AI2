import pprint, random
from typing import List, Dict, Tuple #for python3.8 compatibility

import server_preferences
import models_module


class EvaluationManager():
    def test_print_camera_usefulness_and_evaluation_probability(self):
        print("")
        sorted_cameras = sorted(
            self.camera_usefulness.items(), 
            key=lambda item: item[1]['usefulness_score'], 
            reverse=True
        )
        for camera_uuid, usefulness in sorted_cameras:
            print(f"Camera UUID: {camera_uuid:<10}, Usefulness Score: {usefulness['usefulness_score']:<6.2f}, Evaluation Probability: {self.camera_evaluation_probabilities[camera_uuid]:<2}")

    def __init__(self) -> None:   
        self.pose_detector = models_module.PoseDetector(model_name="yolov8n-pose")
        self.hardhat_detector = models_module.HardhatDetector(model_name="hardhat_detector")
        self.forklift_detector = models_module.ForkliftDetector(model_name="forklift_detector")     
        
        # Keep track of the camera 'usefulness' allocation of the computation resources
        self.camera_usefulness = {}
        self.camera_evaluation_probabilities = {} 
        self.recenty_evaluated_frame_uuids_wrt_camera = {} # Keep track of the  UUID of the last frame that is evaluated for each camera
            
    def __get_models_to_call(self, active_rules:List[Dict]) -> List[str]:
        models_to_call = []        
        for active_rule in active_rules:
            if active_rule["rule_name"] == "RESTRICTED_AREA":
                if self.pose_detector not in models_to_call: models_to_call.append(self.pose_detector)
                if self.forklift_detector not in models_to_call: models_to_call.append(self.forklift_detector)
            elif active_rule["rule_name"] == "HARDHAT_DETECTION":
                if self.hardhat_detector not in models_to_call: models_to_call.append(self.hardhat_detector)
                if self.pose_detector not in models_to_call: models_to_call.append(self.pose_detector)
    
        return models_to_call
    
    def evaluate_frames_info(self, frames_info:List[Dict]):
        for frame_info in frames_info:
            # if random number is less than the camera's evaluation probability, the frame will be evaluated  
            random_number = random.random()
            if random_number > self.camera_evaluation_probabilities.setdefault(frame_info["camera_uuid"], server_preferences.MINIMUM_EVALUATION_PROBABILITY):
                continue
            
            # Ensure that same frame is not evaluated twice
            if frame_info["camera_uuid"] not in self.recenty_evaluated_frame_uuids_wrt_camera.keys():
                self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = {}
            elif frame_info["frame_uuid"] == self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]]:
                continue 
            self.recenty_evaluated_frame_uuids_wrt_camera[frame_info["camera_uuid"]] = frame_info["frame_uuid"]

            # Evaluate the frame based on the active rules
            active_rules = frame_info["active_rules"]
            for model in self.__get_models_to_call(active_rules): # For active rules of the camera, the models to call will be-> self.pose_detector, self.hardhat_detector, self.forklift_detector
                model.detect_frame(frame_info = frame_info)
                frame_info["detection_results"].append(model.get_recent_detection_results())

            for active_rule in active_rules:
                if active_rule["rule_name"] == "RESTRICTED_AREA":
                    was_usefull_to_evaluate = self.__restricted_area_rule(frame_info = frame_info, active_rule = active_rule)
                    self.__update_camera_usefulness(camera_uuid=frame_info["camera_uuid"], was_usefull=was_usefull_to_evaluate)
                    pprint.pprint(self.camera_usefulness[frame_info['camera_uuid']])
                    if server_preferences.PARAM_EVALUATION_VERBOSE: print(f"{'Restricted Area Rule is applied:':<40} {frame_info['camera_uuid']}, Was useful ?: {was_usefull_to_evaluate:<5}, Usefulness Score: {self.camera_usefulness[frame_info['camera_uuid']]['usefulness_score']:.2f}")
                elif active_rule["rule_name"] == "HARDHAT_DETECTION":
                    was_usefull_to_evaluate = self.__hardhat_rule(frame_info = frame_info, active_rule = active_rule)
                    self.__update_camera_usefulness(camera_uuid=frame_info["camera_uuid"], was_usefull=was_usefull_to_evaluate)
                    if server_preferences.PARAM_EVALUATION_VERBOSE: print(f"{'Hardhat Detection Rule is applied:':<40} {frame_info['camera_uuid']}, Was useful ?: {was_usefull_to_evaluate:<5}, Usefulness Score: {self.camera_usefulness[frame_info['camera_uuid']]['usefulness_score']:.2f}")

        self.__update_camera_evaluation_probabilities_considering_camera_usefulnesses()
    
    def __is_inside_polygon(self, point:Tuple, polygon:List[Tuple]) -> bool:
        # Ray casting algorithm to check if a point is inside a polygon. Basically, it checks if the point is inside the polygon by drawing a line from the point to infinity and counting the number of intersections with the polygon. If the number of intersections is odd, the point is inside the polygon.
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(n+1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
    def __is_two_polygons_intersecting(self, polygon1:List[Tuple], polygon2:List[Tuple]) -> bool:
        for i in range(len(polygon1)):
            if self.__is_inside_polygon(polygon1[i], polygon2):
                return True
        for i in range(len(polygon2)):
            if self.__is_inside_polygon(polygon2[i], polygon1):
                return True
        return False
    
    def find_rectangle_intersection_percentage(self, rect1:List[int], rect2:List[int]) -> float:
        # Find the intersection percentage of the rectangle 1 to rectangle 2
        x1, y1, x2, y2 = rect1
        x2, y2, x2, y2 = rect2
        w1, h1, w2, h2 = (x2-x1), (y2-y1), (x2-x2), (y2-y2)

        x_overlap = max(0, min(x1+w1, x2+w2) - max(x1, x2))
        y_overlap = max(0, min(y1+h1, y2+h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        area1 = w1*h1
        return intersection / (area1)
    
    def __update_camera_usefulness(self, camera_uuid:str, was_usefull:bool) -> None:
        #Update the camera's usefulness score
        if camera_uuid not in self.camera_usefulness:
            self.camera_usefulness[camera_uuid] = {"usefulness_score":0}
        
        if was_usefull:
            self.camera_usefulness[camera_uuid]["usefulness_score"] = 1 + self.camera_usefulness[camera_uuid]["usefulness_score"]*server_preferences.USEFUL_DISCOUNT_FACTOR_FOR_EVALUATION_SCORE
        else:
            self.camera_usefulness[camera_uuid]["usefulness_score"] = self.camera_usefulness[camera_uuid]["usefulness_score"]*server_preferences.NOT_USEFULL_DISCOUNT_FACTOR_FOR_EVALUATION_SCORE

        if self.camera_usefulness[camera_uuid]["usefulness_score"] < server_preferences.MINIMUM_USEFULNESS_SCORE_TO_CONSIDER:
            self.camera_usefulness[camera_uuid]["usefulness_score"] = 0

    def __update_camera_evaluation_probabilities_considering_camera_usefulnesses(self) -> None:
        #Update the camera's evaluation probability
        different_usefulness = []
        for _, usefulness in self.camera_usefulness.items():
            if usefulness["usefulness_score"] not in different_usefulness:
                different_usefulness.append(usefulness["usefulness_score"])

        number_of_terms = len(different_usefulness)
        if number_of_terms == 0: return
        geometric_sum = (1-server_preferences.GEOMETRIC_R**number_of_terms)/(1-server_preferences.GEOMETRIC_R) # assume first term is 1
        first_term = 1/geometric_sum # Probability of evaluation of the camera(s) with the highest usefulness. Update first term so that sum is 1

        sorted_usefullness = sorted(different_usefulness, reverse=True)
        for camera_uuid, usefulness in self.camera_usefulness.items():
            if camera_uuid not in self.camera_evaluation_probabilities:
                self.camera_evaluation_probabilities[camera_uuid] = server_preferences.MINIMUM_EVALUATION_PROBABILITY
                       
            usefulness_index = sorted_usefullness.index(usefulness["usefulness_score"])
            probability = first_term*server_preferences.GEOMETRIC_R**usefulness_index
            self.camera_evaluation_probabilities[camera_uuid] = max(probability, server_preferences.MINIMUM_EVALUATION_PROBABILITY)     

    def __restricted_area_rule(self, frame_info:Dict = None, active_rule:Dict = None) -> bool:
        # Which method to use for the evaluation
        if active_rule["evaluation_method"] == "ANKLE_INSIDE_POLYGON":
            for pose_bbox in self.pose_detector.get_recent_detection_results()["normalized_bboxes"]:
                left_ankle =  pose_bbox[5]["left_ankle"]
                right_ankle =  pose_bbox[5]["right_ankle"]

                # Check if the left or right ankle is inside the polygon, if not return False
                is_left_ankle_inside = left_ankle[2]>0 and self.__is_inside_polygon( (left_ankle[0], left_ankle[1]), active_rule["normalized_rule_area_polygon_corners"])
                is_right_ankle_inside = right_ankle[2]>0 and self.__is_inside_polygon((right_ankle[0], right_ankle[1]), active_rule["normalized_rule_area_polygon_corners"])
                if not is_left_ankle_inside and not is_right_ankle_inside: return False

                # calculate intersection percentage with person bounding box and if it is greater than a threshold, return False, otherwise return True
                for forklift_bbox in self.forklift_detector.get_recent_detection_results()["normalized_bboxes"]:
                    forklift_bbox = forklift_bbox[:4]
                
                #TODO: Implement the intersection percentage calculation
                return True    
            return False # If no person is detected, return False        
        else:
            raise ValueError(f"Invalid evaluation method: {active_rule['evaluation_method']}")            
                              
    def __hardhat_rule(self, frame_info:Dict = None, active_rule:Dict = None) -> bool:
        return random.choices([True, False], weights=[0.1, 0.9], k=1)[0]

    



