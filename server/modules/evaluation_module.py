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
            models_to_call = self.__get_models_to_call(active_rules)
            for model in models_to_call:
                self.DETECTORS[model].predict_frame(frame_info = frame_info)

            continue     
            for active_rule in active_rules:
                if active_rule["rule_name"] == "RESTRICTED_AREA":
                    evaluation_result, was_usefull_to_evaluate = self.__restricted_area_rule(frame_info = frame_info, active_rule = active_rule)
                    was_usefull_to_evaluate =  random.choices([True, False], weights=[0.1, 0.9])[0]
                    self.__update_camera_usefulness(camera_uuid=frame_info["camera_uuid"], was_usefull=was_usefull_to_evaluate)
                    if server_preferences.EVALUATION_VERBOSE: print(f"Restricted Area Rule is applied: {frame_info['camera_uuid']}, Was useful ?: {was_usefull_to_evaluate}, Usefulness Score: {self.camera_usefulness[frame_info['camera_uuid']]['usefulness_score']}")

        self.__update_camera_evaluation_probabilities_considering_camera_usefulnesses()

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

    def __restricted_area_rule(self, frame_info:Dict = None, active_rule:Dict = None) -> Dict:
        yolo_model_to_use = active_rule["yolo_model_to_use"]

        was_usefull_to_evaluate = False
        evaluation_result = self.DETECTORS[yolo_model_to_use].predict_frame_and_return_detections(frame_info = frame_info, bbox_confidence=0.75)
        if len(evaluation_result) > 0: was_usefull_to_evaluate = True

        return evaluation_result, was_usefull_to_evaluate
    
    
    



