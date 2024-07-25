# Camera Class Preferences:
CAMERA_VERBOSE = False
CAMERA_CONFIG_KEYS = ['camera_uuid', 'camera_region', 'camera_description', 'is_alive', 'NVR_ip', 'camera_ip_address', 'username', 'password', 'stream_path', 'active_rules']
CAMERA_DEFAULT_FETCHING_DURATION_SECONDS = 0.1 # Used to calculate randomization range for fetching delay
CAMERA_FETCH_DELAY_SAFETY_MARGIN = 2 # Used to increase the fetching delay to prevent bottlenecking. Basically the max delay is calculated by multiplying the default fetching duration by the number of cameras and this safety margin

CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE = [0,10] # When a frame is fetched from a camera, the camera waits for a random time between 0 and 10 seconds before fetching the next frame. This is to prevent bottlenecking when multiple cameras are fetching frames at the same time. The range can be changed by the user using the set_camera_fetching_delay_randomization_range function
def PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras:int):
    global CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE
    global CAMERA_FETCH_DELAY_SAFETY_MARGIN

    max_delay = max(CAMERA_DEFAULT_FETCHING_DURATION_SECONDS, CAMERA_FETCH_DELAY_SAFETY_MARGIN*CAMERA_DEFAULT_FETCHING_DURATION_SECONDS * number_of_cameras)
    CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE = [CAMERA_DEFAULT_FETCHING_DURATION_SECONDS, max_delay]

#Detector Module Preferences:
POSE_DETECTION_VERBOSE = False

#Evaluation Module Preferences:
DISCOUNT_FACTOR_FOR_EVALUATION_SCORE = 0.90 # If a frame is evaluated as useful, the camera's score is 1. If it is evaluated as not useful, the camera's usefulness score is 0. The usefulness score is updated by -> usefulness_score = usefulness_score * DISCOUNT_FACTOR_FOR_EVALUATION_SCORE + evaluation_score
MINIMUM_EVALUATION_PROBABILITY = 0.05 # The minimum probability that a camera will be evaluated. If the camera's calculated evaluation probability is less than this value, it is set to this value
GEOMETRIC_R = 0.9 # The evaluation probability of a camera is calculated as a geometric series. The first term is 1, and the common ratio is this value. The probability is calculated as 1 + 1*EVALUATION_PROBABILITY_GEOMETRIC_SERIES_MULTIPLIER + 1*EVALUATION_PROBABILITY_GEOMETRIC_SERIES_MULTIPLIER^2 + ...
EVALUATION_VERBOSE = False

