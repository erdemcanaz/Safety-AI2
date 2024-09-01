import PREFERENCES
import models_module

class FrameEvaluator():

    def __init__(self):
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



