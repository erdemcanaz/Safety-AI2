import pprint, random, datetime
from typing import List, Dict, Tuple #for python3.8 compatibility

import server_preferences
import models_module

import cv2


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
        self.pose_detector = models_module.PoseDetector(model_name="yolov8m-pose")
        self.hardhat_detector = models_module.HardhatDetector(model_name="hardhat_detector")
        self.forklift_detector = models_module.ForkliftDetector(model_name="forklift_detector")     
        
        # Keep track of the camera 'usefulness' allocation of the computation resources
        self.camera_usefulness = {}
        self.camera_evaluation_probabilities = {} 
        self.recenty_evaluated_frame_uuids_wrt_camera = {} # Keep track of the  UUID of the last frame that is evaluated for each camera
        
        self.test_frame_evaluation_counter = {} #NOTE: for testing purposes
        self.total_violation_counter = 0 #NOTE: for testing purposes
        self.number_of_persons = 0 #NOTE: for testing purposes

    def __get_models_to_call(self, active_rules:List[Dict]) -> List[str]:
        models_to_call = []        
        for active_rule in active_rules:
            if active_rule["rule_name"] == "RESTRICTED_AREA":
                if self.pose_detector not in models_to_call: models_to_call.append(self.pose_detector)
                if self.forklift_detector not in models_to_call: models_to_call.append(self.forklift_detector)
            elif active_rule["rule_name"] == "HARDHAT_DETECTION":
                if self.hardhat_detector not in models_to_call: models_to_call.append(self.hardhat_detector)
                if self.pose_detector not in models_to_call: models_to_call.append(self.pose_detector)
                if self.forklift_detector not in models_to_call: models_to_call.append(self.forklift_detector)
            else:
                raise ValueError(f"Invalid rule name: {active_rule['rule_name']}")
            
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

            cv2.imshow(frame_info["camera_uuid"], cv2.resize(frame_info["frame"], (100,100) )) #NOTE: for testing purposes
            self.test_frame_evaluation_counter.setdefault(frame_info["camera_uuid"], 0) #NOTE: for testing purposes
            self.test_frame_evaluation_counter[frame_info["camera_uuid"]] += 1 #NOTE: for testing purposes

            # Evaluate the frame based on the active rules
            active_rules = frame_info["active_rules"]
            for model in self.__get_models_to_call(active_rules): # For active rules of the camera, the models to call will be-> self.pose_detector, self.hardhat_detector, self.forklift_detector
                model.detect_frame(frame_info = frame_info)
                frame_info["detection_results"].append(model.get_recent_detection_results())

            for active_rule in active_rules:
                if active_rule["rule_name"] == "RESTRICTED_AREA":
                    was_usefull_to_evaluate, was_violation = self.__restricted_area_rule(frame_info = frame_info, active_rule = active_rule)
                    self.__update_camera_usefulness(camera_uuid=frame_info["camera_uuid"], was_usefull=was_usefull_to_evaluate)      

                    if was_usefull_to_evaluate:
                        self.number_of_persons += 1
                    if was_violation:
                        self.total_violation_counter += 1
                        save_path = f"{server_preferences.PATH_VOLUME}/reports/restricted_area_violation_{frame_info['camera_uuid']}_{datetime.datetime.now().strftime('%H_%M_%S')}.jpg"
                        cv2.imshow("frame_last_violation", frame_info["frame"])       
                        cv2.waitKey(2500)
                        cv2.destroyAllWindows()

                    if server_preferences.PARAM_EVALUATION_VERBOSE: print(f"#{self.total_violation_counter:<4} / {self.number_of_persons:<5} - {'Restricted Area Rule is applied:':<40} { self.test_frame_evaluation_counter[frame_info['camera_uuid']]:<6}| {frame_info['camera_uuid']}, Was useful?: {was_usefull_to_evaluate:<3}, Was violation?:{was_violation:<3}, Usefulness Score: {self.camera_usefulness[frame_info['camera_uuid']]['usefulness_score']:.2f}")
                
                elif active_rule["rule_name"] == "HARDHAT_DETECTION":
                    was_usefull_to_evaluate, was_violation = self.__hardhat_rule(frame_info = frame_info, active_rule = active_rule)
                    self.__update_camera_usefulness(camera_uuid=frame_info["camera_uuid"], was_usefull=was_usefull_to_evaluate)
                    
                    if was_usefull_to_evaluate:
                        self.number_of_persons += 1
                    if was_violation:
                        self.total_violation_counter += 1
                        save_path = f"{server_preferences.PATH_VOLUME}/reports/hardhat_violation_{frame_info['camera_uuid']}_{datetime.datetime.now().strftime('%H_%M_%S')}.jpg"
                        cv2.imwrite(save_path,  frame_info["frame"])
                        cv2.imshow("frame_last_violation", frame_info["frame"])       
                        cv2.waitKey(2500)
                        cv2.destroyAllWindows()

                    if server_preferences.PARAM_EVALUATION_VERBOSE: print(f"#{self.total_violation_counter:<4} / {self.number_of_persons:<5}- {'Hardhat Detection Rule is applied:':<40} { self.test_frame_evaluation_counter[frame_info['camera_uuid']]:<6}| {frame_info['camera_uuid']}, Was useful?: {was_usefull_to_evaluate:<3}, Was violation?:{was_violation:<3}, Usefulness Score: {self.camera_usefulness[frame_info['camera_uuid']]['usefulness_score']:.2f}")

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
    
    def __find_rectangle_intersection_percentage(self, rect1: List[int], rect2: List[int]) -> float:
        # Find the intersection percentage of rectangle 1 to rectangle 2
        x1, y1, x3, y3 = rect1  # Coordinates for rect1
        x2, y2, x4, y4 = rect2  # Coordinates for rect2

        x_overlap = max(0, min(x3, x4) - max(x1, x2))
        y_overlap = max(0, min(y3, y4) - max(y1, y2))
        
        intersection = x_overlap * y_overlap        
        area1 = (x3 - x1) * (y3 - y1)
        overlap_percentage = intersection / area1 if area1 > 0 else 0      
        return overlap_percentage
    
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
        if active_rule["evaluation_method"] == "ANKLE_INSIDE_POLYGON":
            was_usefull = False
            was_violation = False
            for pose_bbox in self.pose_detector.get_recent_detection_results()["normalized_bboxes"]:
                if pose_bbox[4] < 0.75: continue # If the confidence of the pose detection is less than 0.5, skip this person
                print("A person is detected")
                was_usefull = True # If a person is detected, the evaluation is usefull 

                # resized_image = cv2.resize(frame_info["frame"], (700, 540))
                # cv2.imshow("person_frame_restricted_area", resized_image) #NOTE: delete this line
                # cv2.waitKey(1000)

                left_ankle =  pose_bbox[5]["left_ankle"]
                right_ankle =  pose_bbox[5]["right_ankle"]

                # Check if the left or right ankle is inside the polygon, if not return False
                is_left_ankle_inside = left_ankle[2]>0 and self.__is_inside_polygon( (left_ankle[0], left_ankle[1]), active_rule["normalized_rule_area_polygon_corners"])
                is_right_ankle_inside = right_ankle[2]>0 and self.__is_inside_polygon((right_ankle[0], right_ankle[1]), active_rule["normalized_rule_area_polygon_corners"])
                if not is_left_ankle_inside and not is_right_ankle_inside: 
                    print("Both ankles are not inside the polygon")                    
                    continue # If both ankles are not inside the polygon, continue to the next person

                # calculate intersection percentage of the person bounding box with forklift and if it is greater than a threshold, return False, otherwise return True
                is_inside_forklift = False
                for forklift_bbox in self.forklift_detector.get_recent_detection_results()["normalized_bboxes"]:
                    if forklift_bbox[4] < 0.5: continue # If the confidence of the forklift detection is less than 0.5, skip this forklift
                    forklift_bbox = forklift_bbox[:4]
                    if self.__find_rectangle_intersection_percentage(pose_bbox[:4], forklift_bbox) > 0.8:
                        is_inside_forklift = True
                        break
                if is_inside_forklift: 
                    print("Person is inside the forklift")
                    continue
                
                pose_confidence = pose_bbox[4]
                mean_ankle_confidence = (left_ankle[2]*is_left_ankle_inside + right_ankle[2]*is_right_ankle_inside) / (is_left_ankle_inside + is_right_ankle_inside) # Booleans are treated as 1 or 0. At this step, atleast one of the ankles is inside the polygon
                violation_score = pose_confidence * mean_ankle_confidence
                if violation_score < float(active_rule["trigger_score"]): 
                    print("Violation score is less than the trigger score")
                    continue  # If the violation score is less than the trigger score, continue to the next person
                frame_info["rule_violations"].setdefault("RESTRICTED_AREA", []) # If there is a restricted area record, add it to the frame_info
                
                frame_info["rule_violations"]["RESTRICTED_AREA"].append(
                    {
                     "evaluation_method":active_rule["evaluation_method"],                     
                     "violated_rule_area_polygon_corners":active_rule["normalized_rule_area_polygon_corners"],
                     "violated_person_bbox":pose_bbox[:4],
                     "violation_score":violation_score
                    }
                )  
                was_violation = True          
            return was_usefull, was_violation # If no person is detected, return False otherwise return True       
        else:
            raise ValueError(f"Invalid evaluation method: {active_rule['evaluation_method']}")            
                              
    def __hardhat_rule(self, frame_info:Dict = None, active_rule:Dict = None) -> bool:        
        if active_rule["evaluation_method"] == "INTERSECTION_WITH_PERSON":
            was_usefull = False
            was_violation = False
            for pose_bbox in self.pose_detector.get_recent_detection_results()["normalized_bboxes"]:
                if pose_bbox[4] < 0.75: continue # If the confidence of the pose detection is less than 0.5, skip this person
                print("A person is detected")
                was_usefull = True # If a person is detected, the evaluation is usefull

                # resized_image = cv2.resize(frame_info["frame"], (700, 540))
                # cv2.imshow("person_frame_hardhat", resized_image) #NOTE: delete this line
                # cv2.waitKey(1000)

                # calculate intersection percentage of the person bounding box with forklift and if it is greater than a threshold, continue to the next person
                is_inside_forklift = False
                for forklift_bbox in self.forklift_detector.get_recent_detection_results()["normalized_bboxes"]:
                    if forklift_bbox[4] < 0.5: continue # If the confidence of the forklift detection is less than 0.5, skip this forklift
                    forklift_bbox = forklift_bbox[:4]
                    if self.__find_rectangle_intersection_percentage(pose_bbox[:4], forklift_bbox) > 0.75:
                        is_inside_forklift = True
                        break
                if is_inside_forklift: 
                    print("Person is inside the forklift")
                    continue

                # Find the best hardhat detection candidate for the person
                best_hardhat_detection_candidate = None
                pprint.pprint(self.hardhat_detector.get_recent_detection_results())
                for hardhat_bbox in self.hardhat_detector.get_recent_detection_results()["normalized_bboxes"]:
                    if hardhat_bbox[4] < 0.2: continue
                    hardhat_bbox_center = ((hardhat_bbox[0]+hardhat_bbox[2])/2, (hardhat_bbox[1]+hardhat_bbox[3])/2)
                    # Check if the hardhat detection is inside the polygon, if not continue to the next hardhat detection
                    if not self.__is_inside_polygon(hardhat_bbox_center, active_rule["normalized_rule_area_polygon_corners"]): continue

                    if self.__find_rectangle_intersection_percentage(pose_bbox[:4], hardhat_bbox[:4]) < 0.75: continue

                    if best_hardhat_detection_candidate is None:
                        best_hardhat_detection_candidate = hardhat_bbox
                    elif hardhat_bbox[4] > best_hardhat_detection_candidate[4]: # If the confidence of the new detection is higher, update the best detection
                        best_hardhat_detection_candidate = hardhat_bbox
                if best_hardhat_detection_candidate is None: 
                    
                    print("No hardhat detection is found")
                    continue
                
                #At this point, a person with hardhat detection is found
                pose_confidence = pose_bbox[4]
                hardhat_violation_confidence = (1-best_hardhat_detection_candidate[4]) if best_hardhat_detection_candidate[5] == "hard_hat" else best_hardhat_detection_candidate[4]
                violation_score = pose_confidence * hardhat_violation_confidence
                
                if violation_score < float(active_rule["trigger_score"]): 
                    print("Violation score is less than the trigger score")
                    continue # If the violation score is less than the trigger score, continue to the next person

                frame_info["rule_violations"].setdefault("HARDHAT_DETECTION", [])
                frame_info["rule_violations"]["HARDHAT_DETECTION"].append(
                    {
                     "evaluation_method":active_rule["evaluation_method"],
                     "violated_person_bbox":pose_bbox[:4],
                     "violated_hardhat_bbox":best_hardhat_detection_candidate[:4],
                     "hardhat_class_name":best_hardhat_detection_candidate[5],
                     "violation_score":violation_score
                    }
                )
                was_violation = True
            return was_usefull, was_violation # If no person is detected, return False otherwise return True
        else:
            raise ValueError(f"Invalid evaluation method: {active_rule['evaluation_method']}")

                
                    

                 


            
        #return random.choices([True, False], weights=[0.1, 0.9], k=1)[0]

    



