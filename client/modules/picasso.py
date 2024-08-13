import cv2
import numpy as np
from scipy.interpolate import interp1d

IMAGE_PATHS = {
    "press_key_page_template": "src/templates/press_key_page_template.png",
    "login_page_template": "src/templates/login_page_template.png",
    "server_failure_page_template": "src/templates/server_failure_page_template.png",
    "user_not_found_page_template": "src/templates/user_not_found_page_template.png",
    "which_app_page_template": "src/templates/which_app_page_template.png",
    "user_not_authorized_for_app_page_template": "src/templates/user_not_authorized_for_app_page_template.png",
    "ISG_app_page_template": "src/templates/ISG_app_page_template.png",
    "kalite_app_page_template": "src/templates/kalite_app_page_template.png",
    "guvenlik_app_page_template": "src/templates/guvenlik_app_page_template.png",
    "ozet_app_page_template": "src/templates/ozet_app_page_template.png",
    "ihlal_raporlari_app_page": "src/templates/ihlal_raporlari_app_page_template.png",
    "kurallar_app_page_template": "src/templates/kurallar_app_page_template.png",
    "kameralar_app_page_template": "src/templates/kameralar_app_page_template.png",

    "anil_right_looking": "src/icons/anil_right_looking.png",
    "anil_left_looking": "src/icons/anil_left_looking.png",
    "app_bar_dark_blue": "src/icons/app_bar_dark_blue.png",
    "app_bar_light_blue": "src/icons/app_bar_light_blue.png",
    "red_hardhat": "src/icons/red_hardhat.png",
    "red_hardhat_transp": "src/icons/red_hardhat_transp.png",
    "red_restricted_area": "src/icons/red_restricted_area.png",
    "red_restricted_area_transp": "src/icons/red_restricted_area_transp.png",
    "ihlal_row_light_blue": "src/icons/ihlal_row_light_blue.png",
    "ihlal_row_dark_blue": "src/icons/ihlal_row_dark_blue.png",
    "violation_image_background": "src/icons/violation_image_background.png",
    "camera_list_bar": "src/icons/camera_list_bar.png",
    "old_camera_icon": "src/icons/old_camera_icon.png",
    "updated_camera_icon": "src/icons/updated_camera_icon.png",
    "new_camera_icon": "src/icons/new_camera_icon.png",
    "eye_dark_blue": "src/icons/eye_dark_blue.png",
    "eye_light_blue": "src/icons/eye_light_blue.png"
    }

def get_image_as_frame(image_name:str=None, width:int=1920, height:int=1080, maintain_aspect_ratio:bool = True):
    global IMAGE_PATHS
    image_path = IMAGE_PATHS[image_name]
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    # Resize image
    if maintain_aspect_ratio:
        im_height, im_width = image.shape[0], image.shape[1]
        scale = min((width / im_width), (height / im_height))
        image = cv2.resize(image, (int(im_width * scale), int(im_height * scale)), interpolation=cv2.INTER_AREA)
    else:
        image = cv2.resize(image, (width, height),interpolation=cv2.INTER_AREA)

    return image

def draw_image_on_frame(frame:np.ndarray=None, image_name:str=None, x:int=None, y:int=None, width:int=100, height:int=100, maintain_aspect_ratio:bool = True):
    global IMAGE_PATHS
    image_path = IMAGE_PATHS[image_name]
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    # Resize image
    if maintain_aspect_ratio:
        im_height, im_width = image.shape[0], image.shape[1]
        scale = min((width / im_width), (height / im_height))
        image = cv2.resize(image, (int(im_width * scale), int(im_height * scale)), interpolation=cv2.INTER_AREA)
    else:
        image = cv2.resize(image, (width, height),interpolation=cv2.INTER_AREA)

    # Draw image on frame
    frame_height, frame_width = frame.shape[0], frame.shape[1]
    resized_image_height, resized_image_width = image.shape[0], image.shape[1]

    roi_x1 = x
    roi_x2 = min(max(x + resized_image_width, 0), frame_width)
    roi_y1 = y
    roi_y2 = min(max(y + resized_image_height, 0), frame_height)

    if roi_x1<0 or roi_y1<0 or (roi_x2 - roi_x1 <= 0) or (roi_y2 - roi_y1 <= 0):
        return
    
    frame_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
    image_roi = image[0:(roi_y2-roi_y1), 0:(roi_x2-roi_x1)]
    
    if image.shape[2]==4:                                   # If image has alpha channel           
        b, g, r, a = cv2.split(image_roi)                   # Split the icon into its channels            
        image_alpha = a / 255.0                             # Normalize the alpha channel to be in the range [0, 1]
        
        for c in range(0, 3):                               # Loop over the RGB channels
            frame_roi[:, :, c] = (frame_roi[:, :, c] * (1 - image_alpha) + image_roi[:, :, c] * image_alpha).astype(np.uint8)
    else:
        frame[roi_y1:roi_y2, roi_x1:roi_x2] = image_roi

def draw_frame_on_frame(frame:np.ndarray=None, frame_to_draw:np.ndarray=None, x:int=None, y:int=None, width:int=100, height:int=100, maintain_aspect_ratio:bool = True):
    # Resize image
    if maintain_aspect_ratio:
        im_height, im_width = frame_to_draw.shape[0], frame_to_draw.shape[1]
        scale = min((width / im_width), (height / im_height))
        frame_to_draw = cv2.resize(frame_to_draw, (int(im_width * scale), int(im_height * scale)), interpolation=cv2.INTER_AREA)
    else:
        frame_to_draw = cv2.resize(frame_to_draw, (width, height),interpolation=cv2.INTER_AREA)

    # Draw image on frame
    frame_height, frame_width = frame.shape[0], frame.shape[1]
    resized_image_height, resized_image_width = frame_to_draw.shape[0], frame_to_draw.shape[1]

    roi_x1 = x
    roi_x2 = min(max(x + resized_image_width, 0), frame_width)
    roi_y1 = y
    roi_y2 = min(max(y + resized_image_height, 0), frame_height)

    if roi_x1<0 or roi_y1<0 or (roi_x2 - roi_x1 <= 0) or (roi_y2 - roi_y1 <= 0):
        return
    
    frame_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
    image_roi = frame_to_draw[0:(roi_y2-roi_y1), 0:(roi_x2-roi_x1)]
    
    if frame_to_draw.shape[2]==4:                                   # If image has alpha channel           
        b, g, r, a = cv2.split(image_roi)                   # Split the icon into its channels            
        image_alpha = a / 255.0                             # Normalize the alpha channel to be in the range [0, 1]
        
        for c in range(0, 3):                               # Loop over the RGB channels
            frame_roi[:, :, c] = (frame_roi[:, :, c] * (1 - image_alpha) + image_roi[:, :, c] * image_alpha).astype(np.uint8)
    else:
        frame[roi_y1:roi_y2, roi_x1:roi_x2] = image_roi

def plot_smooth_curve_on_frame(frame: np.ndarray, points_list: np.ndarray, color: tuple = (0, 0, 255), thickness: int = 2):
    # Convert points_list to a numpy array and sort by x values
    points = np.array(points_list, dtype=np.float32)
    points = points[points[:, 0].argsort()]  # Sort by x values

    # Remove duplicate x-values by averaging the corresponding y-values
    unique_x, indices = np.unique(points[:, 0], return_index=True)
    avg_y = np.array([points[points[:, 0] == x, 1].mean() for x in unique_x])

    # Create a new set of points with unique x values and their corresponding averaged y values
    unique_points = np.stack((unique_x, avg_y), axis=-1)

    # Perform linear interpolation to ensure a single y-value for each x-value
    f = interp1d(unique_x, avg_y, kind='cubic')

    # Generate new x values for smooth plotting
    x_new = np.linspace(unique_x.min(), unique_x.max(), 1000)
    y_new = f(x_new)

    # Convert smoothed points to integer coordinates
    smooth_points = np.array([x_new, y_new]).T.astype(np.int32)

    # Draw the smooth curve on the image
    cv2.polylines(frame, [smooth_points], isClosed=False, color=color, thickness=thickness)
