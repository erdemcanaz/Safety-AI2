import cv2, time

def fetch_single_frame(username:str = None, password:str = None, camera_ip_address:str = None):

    while True:
        start_time = time.time()
        url = f'rtsp://{username}:{password}@{camera_ip_address}/profile2/media.smp'

        # Try using FFmpeg backend first
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

        # If FFmpeg fails, try GStreamer
        if not cap.isOpened():
            cap = cv2.VideoCapture(url, cv2.CAP_GSTREAMER)

        # If still not opened, raise an error
        if not cap.isOpened():
            raise Exception("Failed to open video stream with both FFmpeg and GStreamer backends.")

        buffer_size_in_frames = 4  # Slightly increase buffer size
        cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)

        init_time = time.time()
        print(f"Video stream opened in {init_time - start_time:.2f} seconds")

        ret, frame = cap.read()
        if ret:
            cv2.imshow('frame', frame)
            print(f"Frame fetched in {time.time() - init_time:.2f} seconds")
            cv2.waitKey(0)  # Wait for a key press to close the window
        else:
            print("Failed to fetch frame from the stream.")

username = input("Enter username: ")
password = input("Enter password: ")
camera_ip_address = input("Enter camera IP address: ")
fetch_single_frame(username, password, camera_ip_address)

