import pprint
from typing import List, Dict, Tuple #for python3.8 compatibility
import detectors_module
import server_preferences

class EvaluationManager():
  
    def __init__(self, yolo_models_to_be_used:List[str] = None) -> None:
        AVAILABLE_MODELS = ["yolov8n-pose", "yolov8l-pose"] # add model names defined in predictors_module.py classes here
        for model_name in yolo_models_to_be_used:
            print(model_name, AVAILABLE_MODELS)
            if model_name not in AVAILABLE_MODELS:
                raise ValueError(f"Invalid model name. Available models are: {AVAILABLE_MODELS}")
            
        # Create YOLO objects
        self.DETECTORS = {}
        for model_name in yolo_models_to_be_used:
            if model_name == "yolov8n-pose":
                self.DETECTORS[model_name] = detectors_module.PoseDetector(model_name=model_name)
            elif model_name == "yolov8l-pose":
                self.DETECTORS[model_name] = detectors_module.PoseDetector(model_name=model_name)       
            else:
                raise ValueError(f"Invalid model name. Available models are: {AVAILABLE_MODELS}")
            
        # Keep track of the camera 'usefulness' allocation of the computation resources
        self.camera_usefullness = {}
            
    def evaluate_frames_info(self, frames_info:List[Dict]) -> Tuple[List[str], List[Dict]]:
        evaluated_uuids:List[str] = []
        evaluation_results:List[Dict] = []

        self.test_print_camera_usefullness()

        for frame_info in frames_info:
            #TODO: decide if the frame should be evaluated or not probabilistically
            evaluated_uuids.append(frame_info["frame_uuid"])
            
            active_rules = frame_info["active_rules"]            
            for active_rule in active_rules:
                if active_rule["rule_name"] == "RESTRICTED_AREA":
                    evaluation_result, was_usefull_to_evaluate = self.__restricted_area_rule(frame_info = frame_info, active_rule = active_rule)
                    if len(evaluation_result) > 0: evaluation_results.append(evaluation_result)
                    self.__update_camera_usefulness(camera_uuid=frame_info["camera_uuid"], was_usefull=was_usefull_to_evaluate)
                    if server_preferences.EVALUATION_VERBOSE: print(f"Restricted Area Rule is applied: {frame_info['camera_uuid']}, Was useful ?: {was_usefull_to_evaluate}, Usefulness Score: {self.camera_usefullness[frame_info['camera_uuid']]['usefulness_score']}")

        return evaluated_uuids, evaluation_results      

    def test_print_camera_usefullness(self) -> None:
        pprint.pprint(self.camera_usefullness)

    def __update_camera_usefulness(self, camera_uuid:str, was_usefull:bool) -> None:
        if camera_uuid not in self.camera_usefullness:
            self.camera_usefullness[camera_uuid] = {"usefulness_score":0}
        
        if was_usefull:
            self.camera_usefullness[camera_uuid]["usefulness_score"] = 1 + self.camera_usefullness[camera_uuid]["usefulness_score"]*server_preferences.DISCOUNT_FACTOR_FOR_EVALUATION_SCORE
        else:
            self.camera_usefullness[camera_uuid]["usefulness_score"] = self.camera_usefullness[camera_uuid]["usefulness_score"]*server_preferences.DISCOUNT_FACTOR_FOR_EVALUATION_SCORE

    def __restricted_area_rule(self, frame_info:Dict = None, active_rule:Dict = None) -> Dict:
        yolo_model_to_use = active_rule["yolo_model_to_use"]

        was_usefull_to_evaluate = False
        evaluation_result = self.DETECTORS[yolo_model_to_use].predict_frame_and_return_detections(frame_info = frame_info, bbox_confidence=0.75)
        if len(evaluation_result) > 0: was_usefull_to_evaluate = True

        return evaluation_result, was_usefull_to_evaluate
    
    
    



