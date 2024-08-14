import cv2, time

def fetch_single_frame(username:str = None, password:str = None, camera_ip_address:str = None):
    start_time = time.time()
    url = f'rtsp://{username}:{password}@{camera_ip_address}/profile2/media.smp'
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    while True:      
        ret, frame = cap.read()
        if ret:
            cv2.imshow('frame', frame)
        else:
            print("Failed to fetch frame from the stream.")
        
        # time.sleep(1)

username = input("Enter username: ")
password = input("Enter password: ")
camera_ip_address = input("Enter camera IP address: ")
fetch_single_frame(username, password, camera_ip_address)

