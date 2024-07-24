# Camera Class Preferences:
CAMERA_VERBOSE = True
CAMERA_CONFIG_KEYS = ['camera_uuid', 'camera_region', 'camera_description', 'is_alive', 'NVR_ip', 'camera_ip_address', 'username', 'password', 'stream_path', 'active_rules', 'scoring_method']
CAMERA_DEFAULT_FETCHING_DURATION_SECONDS = 0.1 # Used to calculate randomization range for fetching delay

CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE = [0,10] # When a frame is fetched from a camera, the camera waits for a random time between 0 and 10 seconds before fetching the next frame. This is to prevent bottlenecking when multiple cameras are fetching frames at the same time. The range can be changed by the user using the set_camera_fetching_delay_randomization_range function
def PREF_optimize_camera_fetching_delay_randomization_range(number_of_cameras:int):
    global CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE
    max_delay = max(CAMERA_DEFAULT_FETCHING_DURATION_SECONDS, 2*CAMERA_DEFAULT_FETCHING_DURATION_SECONDS * number_of_cameras)
    CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE = [CAMERA_DEFAULT_FETCHING_DURATION_SECONDS, max_delay]

