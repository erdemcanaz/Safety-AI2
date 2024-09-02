import cv2
import numpy as np
from scipy.interpolate import interp1d
from pathlib import Path

PICASSO_MODULE_PATH = Path(__file__).resolve()
SRC_FOLDER_PATH = PICASSO_MODULE_PATH.parent.parent / "src"
IMAGE_PATHS = {
        "red_hardhat_transparent": str(SRC_FOLDER_PATH / "icons" / "red_hardhat_transparent.png"),
        "red_restricted_area_transparent": str(SRC_FOLDER_PATH / "icons" / "red_restricted_area_transparent.png"),
        "red_hardhat_transparent_with_background": str(SRC_FOLDER_PATH / "icons" / "red_hardhat_transparent_with_background.png"),
        "red_restricted_area_transparent_with_background": str(SRC_FOLDER_PATH / "icons" / "red_restricted_area_transparent_with_background.png"),
    }

def create_frame(width: int, height: int, color: tuple = (0, 0, 0)):
    """Creates a blank frame with the specified width, height, and color."""
    return np.ones((height, width, 3), np.uint8) * color

def get_bbox_coordinates_from_normalized(frame: np.ndarray, pos_n: tuple, size_n: tuple):
    """
    Calculates the bounding box coordinates from normalized position and size values.

    :param frame: The frame where the bounding box will be drawn.
    :param pos_n: The normalized position of the bounding box (x, y).
    :param size_n: The normalized size of the bounding box (width, height).
    :return: The bounding box coordinates (x1, y1, x2, y2).
    """
    frame_height, frame_width = frame.shape[0], frame.shape[1]
    x1 = int(pos_n[0] * frame_width)
    y1 = int(pos_n[1] * frame_height)
    x2 = int((pos_n[0] + size_n[0]) * frame_width)
    y2 = int((pos_n[1] + size_n[1]) * frame_height)
    return x1, y1, x2, y2

def draw_text_on_frame(frame: np.ndarray, text: str, position: tuple, area_size: tuple, alignment: str = 'center', font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1, text_color=(255, 255, 255), thickness=2, padding=10):
    """
    Draws text within a given area on a frame, aligning it based on the specified alignment option.

    :param frame: The image/frame where the text will be drawn.
    :param text: The text to draw.
    :param position: The top-left corner of the area (x, y).
    :param area_size: The width and height of the area (width, height).
    :param alignment: Text alignment: 'left', 'center', or 'right'.
    :param font: The font type.
    :param font_scale: The scale factor for the font.
    :param text_color: The color of the text in BGR format.
    :param thickness: The thickness of the text.
    :param padding: The padding inside the area for the text.
    """
    # Replace Turkish characters with English characters since OpenCV does not support Turkish characters
    replacements = {
        "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G",
        "ı": "i", "I": "I", "ö": "o", "Ö": "O",
        "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
        "İ": "I"
    }
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)

    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    area_width, area_height = area_size

    # Shorten text if it is wider than the area
    while text_size[0] > area_width - 2 * padding and len(text) > 0:
        text = text[:-1]
        text_size = cv2.getTextSize(text + "...", font, font_scale, thickness)[0]

    # Add ellipsis if text was shortened
    if text_size[0] > area_width - 2 * padding:
        text = text[:-3] + "..."
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

    # Calculate text position based on alignment
    if alignment == 'left':
        text_x = position[0] + padding
    elif alignment == 'right':
        text_x = position[0] + area_width - text_size[0] - padding
    else:  # Default is centered
        text_x = position[0] + (area_width - text_size[0]) // 2

    text_y = position[1] + (area_height + text_size[1]) // 2

    # Draw the text on the frame
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, text_color, thickness, cv2.LINE_AA)

def draw_text_on_frame_with_newlines(frame, text, position=(10, 20), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=0.5, color=(255, 255, 255), thickness=1, line_type=cv2.LINE_AA):
    """
    Draws multi-line text on an OpenCV frame where '\n' is considered.

    Args:
    - frame: The OpenCV image/frame to draw the text on.
    - text: The text string to draw, with '\n' representing new lines.
    - position: Tuple (x, y) where text drawing starts.
    - font: Font type for the text.
    - font_scale: Font scale (size).
    - color: Color of the text (B, G, R).
    - thickness: Thickness of the text.
    - line_type: Line type for text rendering.
    """
    # Replace Turkish characters with English characters since OpenCV does not support Turkish characters
    replacements = {
        "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G",
        "ı": "i", "I": "I", "ö": "o", "Ö": "O",
        "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
        "İ": "I"
    }
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)

    # Split the text into lines
    lines = text.split('\n')

    # Initial y position
    y = position[1]

    # Iterate over each line and put it on the frame
    for line in lines:
        cv2.putText(frame, line.strip(), (position[0], y), font, font_scale, color, thickness, line_type)
        # Update y position for the next line
        y += int(font_scale * 30)  # Adjust the multiplier as necessary for line spacing

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

def draw_polygon_on_frame( frame: np.ndarray = None, points: list = None, color: tuple = (0, 0, 255), thickness: int = 2, last_dot_color: tuple = (255, 0, 0), first_last_line_color: tuple = (0, 255, 0)):
    if len(points) < 2:
        return
    # Ensure points are numpy array in the correct shape
    points = np.array(points)

    # Draw the main polygon
    cv2.polylines(frame, [points.reshape((-1, 1, 2))], isClosed=False, color=color, thickness=thickness)

    # Draw the last dot with a different color
    last_point = tuple(points[-1])
    cv2.circle(frame, last_point, radius=thickness * 2, color=last_dot_color, thickness=-1)

    # Draw the first-to-last connection with a different color
    first_point = tuple(points[0])
    cv2.line(frame, first_point, last_point, color=first_last_line_color, thickness=thickness)

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