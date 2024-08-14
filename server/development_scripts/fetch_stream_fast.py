import cv2, time

def fetch_single_frame_hundred_times(username:str = None, password:str = None, camera_ip_address:str = None):
    url = f'rtsp://{username}:{password}@{camera_ip_address}/{"profile2/media.smp"}'
    cap = cv2.VideoCapture(url)
    buffer_size_in_frames = 1
    cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size_in_frames)

    for i in range(100):
        
        start_time = time.time()
        ret, frame = cap.read()
        if ret:
            print(f"Frame {i:<2} read in {time.time() - start_time:.3f} seconds")
            cv2.imshow('frame', frame)
            wait_key = cv2.waitKey(1000)

    cap.release()

username = input("Enter username: ")
password = input("Enter password: ")
camera_ip_address = input("Enter camera IP address: ")
fetch_single_frame_hundred_times(username, password, camera_ip_address)

