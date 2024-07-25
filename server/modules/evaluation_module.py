from typing import List, Dict, Tuple #for python3.8 compatibility
import detectors_module

class EvaluationManager():
  
    def __init__(self, yolo_models_to_be_used:List[str] = None) -> None:
        AVAILABLE_MODELS = ["yolov8n-pose"] # add model names defined in predictors_module.py classes here
        for model_name in yolo_models_to_be_used:
            if model_name not in AVAILABLE_MODELS:
                raise ValueError(f"Invalid model name. Available models are: {AVAILABLE_MODELS}")
            
        # Create YOLO objects
        self.yolo_objects = {}
        for model_name in yolo_models_to_be_used:
            if model_name == "yolov8n-pose":
                self.yolo_objects[model_name] = detectors_module.PoseDetector(model_name=model_name)        
            else:
                raise ValueError(f"Invalid model name. Available models are: {AVAILABLE_MODELS}")
            
    def evaluate_frames_info(self, frames_info:List[Dict]) -> Tuple[List[str], List[Dict]]:
        evaluated_uuids:List[str] = []
        evaluation_results:List[Dict] = []

        for frame_info in frames_info:
            frame_uuid = frame_info["uuid"]
            frame_image = frame_info["image"]
            frame_image = frame_image[:,:,::-1]


        return evaluated_uuids
       



