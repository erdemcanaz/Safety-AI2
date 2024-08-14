import cv2, time

def fetch_single_frame(username:str = None, password:str = None, camera_ip_address:str = None):

    cap = None
    try:
        while True:
            start_time = time.time()
            url = f'rtsp://{username}:{password}@{camera_ip_address}/{"profile2/media.smp"}'
            cap = cv2.VideoCapture(url, cv2.CAP_GSTREAMER)
            buffer_size_in_frames = 1
            cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)
            init_time = time.time()
            print(f"video stream opened in {init_time-start_time} seconds")
            ret, frame = cap.read()
            if ret:
                cv2.imshow('frame', frame)
                print(f"Frame fetched in {time.time() - start_time} seconds")
            time.sleep(5)
    except Exception as e:
        if cap is not None: cap.release()

username = input("Enter username: ")
password = input("Enter password: ")
camera_ip_address = input("Enter camera IP address: ")
fetch_single_frame(username, password, camera_ip_address)

