import cv2
import os
import pprint

# Folder containing the images
folder_path = input("Enter the path to the folder containing the images: ")
image_files = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

# Sort the image files to maintain order
image_files.sort()

# Variables to track current image index and the list of points
current_index = 0
points = []

def draw_points(img):
    for i, point in enumerate(points):
        x, y = point
        height, width, _ = img.shape
        x = int(x * width)
        y = int(y * height)
        cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
        if i > 0:
            x_prev, y_prev = points[i - 1]
            x_prev = int(x_prev * width)
            y_prev = int(y_prev * height)
            cv2.line(img, (x_prev, y_prev), (x, y), (255, 0, 0), 2)

    # If there are at least 3 points, connect the first and last points to close the polygon
    if len(points) > 2:
        x_first, y_first = points[0]
        x_last, y_last = points[-1]
        x_first = int(x_first * width)
        y_first = int(y_first * height)
        x_last = int(x_last * width)
        y_last = int(y_last * height)
        cv2.line(img, (x_last, y_last), (x_first, y_first), (0, 0, 255), 2)  # Red color for closing the polygon

# Mouse callback function to capture click events
def click_event(event, x, y, flags, params):
    global points
    img = params.copy()  # Copy the image to prevent overwriting
    if event == cv2.EVENT_LBUTTONDOWN:
        # Normalize coordinates
        height, width, _ = img.shape
        x_norm = x / width
        y_norm = y / height
        points.append([x_norm, y_norm])
        print(f"Point recorded: [{x_norm}, {y_norm}]")
        print("Current points list:")
        pprint.pprint(points)
        print()

        draw_points(img)
        cv2.imshow("Image Viewer", img)

# Function to display the current image, draw points, and print the image path
def display_image(index):
    img_path = os.path.join(folder_path, image_files[index])
    img = cv2.imread(img_path)
    resized_image = cv2.resize(img, (960, 540))
    draw_points(resized_image)
    cv2.imshow("Image Viewer", resized_image)
    cv2.setMouseCallback("Image Viewer", click_event, resized_image)
    print(f"Current image: {img_path}")

# Main loop
while True:
    display_image(current_index)
    
    key = cv2.waitKey(0) & 0xFF
    
    if key == ord('d'):
        # Next image
        current_index = (current_index + 1) % len(image_files)
        points = []
        display_image(current_index)
    elif key == ord('a'):
        # Previous image
        current_index = (current_index - 1) % len(image_files)
        points = []
        display_image(current_index)
    elif key == ord('r'):
        # Reset points list
        points = []
        print("Points list has been reset.")
        display_image(current_index)  # Update the display to remove the points
    elif key == 27:  # ESC key
        break

cv2.destroyAllWindows()
