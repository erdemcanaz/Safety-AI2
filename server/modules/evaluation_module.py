from typing import List, Dict, Tuple #for python3.8 compatibility
import evaluation_module
import server.modules.detectors_module as detectors_module

class Evaluator():
  
    def __init__(self, yolo_models_to_be_used:List[str] = None) -> None:

        AVAILABLE_MODELS = ["yolov8n"] # add model names defined in predictors_module.py classes here
        for model_name in yolo_models_to_be_used:
            if model_name not in AVAILABLE_MODELS:
                raise ValueError(f"Invalid model name. Available models are: {AVAILABLE_MODELS}")
            
        # Create YOLO objects
        self.yolo_objects = {}
        for model_name in yolo_models_to_be_used:
            if model_name == "yolov8n":
                self.yolo_objects[model_name] = detectors_module.PoseDetector(model_name=model_name)        
            else:
                raise ValueError(f"Invalid model name. Available models are: {AVAILABLE_MODELS}")
            

       



