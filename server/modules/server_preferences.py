# Camera Class Preferences:
CAMERA_VERBOSE = True
CAMERA_CONFIG_KEYS = ['is_fetch_without_delay','camera_uuid', 'camera_region', 'camera_description', 'is_alive', 'NVR_ip', 'camera_ip_address', 'username', 'password', 'stream_path', 'active_rules', 'scoring_method']
CAMERA_DEFAULT_FETCHING_DELAY_SECONDS = 10
CAMERA_FETCHING_DELAY_RANDOMIZATION_RANGE = [0, 5] # [min, max] in seconds No matter if delay is set or not, this range will be used to randomize the delay added between each frame fetching
