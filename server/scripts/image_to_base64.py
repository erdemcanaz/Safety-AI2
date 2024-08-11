import cv2
import base64
import numpy as np

def image_to_base64(image_path):
    # Read the image from file
    with open(image_path, "rb") as image_file:
        # Convert the image to base64
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_string

def base64_to_image(base64_string):
    # Decode the base64 string to bytes
    image_bytes = base64.b64decode(base64_string)
    # Convert bytes to a numpy array
    np_array = np.frombuffer(image_bytes, np.uint8)
    # Decode the numpy array into an image
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    return image

def display_image_from_base64(base64_string):
    # Convert the base64 string back to an image
    image = base64_to_image(base64_string)
    # Display the image using OpenCV
    cv2.imshow("Image from Base64", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Example usage:
image_path = input("Enter the path to the image file: ")

# Convert the image to a base64 string
base64_string = image_to_base64(image_path)
print("Base64 String:", base64_string)

# Display the image decoded from the base64 string
display_image_from_base64(base64_string)