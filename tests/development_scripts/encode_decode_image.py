import cv2
import numpy as np
import base64
import pyperclip

def encode_frame_for_url_body_b64_string(np_ndarray: np.ndarray = None):
        if np_ndarray is None or not isinstance(np_ndarray, np.ndarray):
            raise ValueError('Invalid np_ndarray provided')
        
        success, encoded_image = cv2.imencode('.jpg', np_ndarray)
        if not success:
            raise ValueError('Failed to encode image')
        base64_encoded_jpg_image_string = base64.b64encode(encoded_image.tobytes()).decode('utf-8')

        return base64_encoded_jpg_image_string

image_path = input('Enter image path: ')
image = cv2.imread(image_path)
encoded_image = encode_frame_for_url_body_b64_string(image)
pyperclip.copy(encoded_image)

