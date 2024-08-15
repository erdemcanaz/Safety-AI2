import platform
from pathlib import Path

PARAM_SLEEP_DURATION_PERCENTAGE = 0.0      # The percentage of the total duration that the server will sleep. The server will sleep for this percentage of the total duration and work for the rest of the time. The total duration is calculated as the average evaluation time divided by (1 - PARAM_SLEEP_DURATION_PERCENTAGE)
PARAM_MAX_SLEEP_DURATION = 5                # The maximum sleep duration in seconds. The server will sleep for this duration if the evaluation time is less than this value
if PARAM_SLEEP_DURATION_PERCENTAGE < 0 or PARAM_SLEEP_DURATION_PERCENTAGE >= 1:
    raise ValueError("PARAM_SLEEP_DURATION_PERCENTAGE must be between 0 and 1")
PARAM_EVALUATION_TIME_UPDATE_FACTOR = 0.05  # New evaluation time = old evaluation time * (1 - PARAM_EVALUATION_TIME_UPDATE_FACTOR) + new evaluation time * PARAM_EVALUATION_TIME_UPDATE_FACTOR

is_linux = platform.system() == "Linux"
if is_linux:
    PATH_VOLUME = Path(__file__).resolve().parent.parent.parent.parent / "safety_AI_volume" # Container volume path
    PATH_CAMERA_CONFIGS_JSON = Path(__file__).resolve().parent.parent.parent.parent / "safety_AI_volume" / "camera_configs.json" # Container volume path
else:
    PATH_VOLUME = None
    PATH_CAMERA_CONFIGS_JSON= Path(__file__).resolve().parent.parent / "configs" / "camera_configs.json" # Local path



# Camera Module Preferences =============================================================================================
PARAM_CAMERA_VERBOSE = False

PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE = None            # Randomize the fetching delay between 0 and max_duration_before_encoding seconds            
PARAM_CAMERA_APPROXIMATED_FRAME_DECODING_DURATION_SECONDS = 0.033 # Approximate time it takes to decode a frame. This value is used to calculate the camera's fetching delay randomization range 
PARAM_CAMERA_DECODE_FREQUENCY_FACTOR = 2                          # 1 is the no effect value. 2 means that the camera will be decoded half of the time and 0.5 means that the camera will be decoded twice as much as the normal time.
PARAM_MINIMUM_DECODING_DELAY = 0.1                               # The minimum fetching delay in seconds. The camera will not be fetched more frequently than this value
def PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras:int):
    global PARAM_CAMERA_APPROXIMATED_FRAME_DECODING_DURATION_SECONDS
    global PARAM_CAMERA_DECODE_FREQUENCY_FACTOR
    global PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE
    global PARAM_MINIMUM_DECODING_DELAY
    
    max_duration_before_encoding = (PARAM_CAMERA_APPROXIMATED_FRAME_DECODING_DURATION_SECONDS * number_of_cameras) * PARAM_CAMERA_DECODE_FREQUENCY_FACTOR
    
    upper_bound = max(max_duration_before_encoding, PARAM_CAMERA_APPROXIMATED_FRAME_DECODING_DURATION_SECONDS, PARAM_MINIMUM_DECODING_DELAY)
    lower_bound = PARAM_MINIMUM_DECODING_DELAY
    PARAM_CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE = [lower_bound, upper_bound]
    
#Detector Module Preferences:
POSE_DETECTION_VERBOSE = False
HARDHAT_DETECTION_VERBOSE = False
FORKLIFT_DETECTION_VERBOSE = False

#Evaluation Module Preferences:
NOT_USEFULL_DISCOUNT_FACTOR_FOR_EVALUATION_SCORE = 0.95 # Slowly decrease the camera's usefulness score if the frame is evaluated as not useful
USEFUL_DISCOUNT_FACTOR_FOR_EVALUATION_SCORE = 0.90 # If a frame is evaluated as useful, the camera's score is 1. If it is evaluated as not useful, the camera's usefulness score is 0. The usefulness score is updated by -> usefulness_score = usefulness_score * DISCOUNT_FACTOR_FOR_EVALUATION_SCORE + evaluation_score

MINIMUM_USEFULNESS_SCORE_TO_CONSIDER = 0.5 # The minimum usefulness score that a camera can have. If the camera's usefulness score is less than this value, it is set to zero
MINIMUM_EVALUATION_PROBABILITY = 0.025 # The minimum probability that a camera will be evaluated. If the camera's calculated evaluation probability is less than this value, it is set to this value
GEOMETRIC_R = 0.75 # The evaluation probability of a camera is calculated as a geometric series. The first term is 1, and the common ratio is this value. The probability is calculated as 1 + 1*EVALUATION_PROBABILITY_GEOMETRIC_SERIES_MULTIPLIER + 1*EVALUATION_PROBABILITY_GEOMETRIC_SERIES_MULTIPLIER^2 + ...
PARAM_EVALUATION_VERBOSE = True

