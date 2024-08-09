# Built-in imports
import pprint, time, sys, os, requests
import numpy as np
import cv2

# Local imports
project_directory = os.path.dirname(os.path.abspath(__file__))
modules_directory = os.path.join(project_directory, 'modules')
sys.path.append(modules_directory) # Add the modules directory to the system path so that imports work
from pages import login_page, server_failure_page, user_not_found_page
from modules import picasso

class User():
    def __init__(self, server_ip_address:str=None):
        self.USERNAME = None
        self.PASSWORD = None
        self.JWT_TOKEN = None
        self.TOKEN_STATUS_CODE = None
        self.IS_AUTHENTICATED = False  
        self.SERVER_IP_ADDRESS = server_ip_address   

    def get_username(self)->str:
        return self.USERNAME if self.USERNAME is not None else ""
    
    def set_username(self, new_username:str=None):
        self.USERNAME = new_username

    def get_password(self)->str:
        return self.PASSWORD if self.PASSWORD is not None else ""
    
    def set_password(self, new_password:str=None):
        self.PASSWORD = new_password

    def get_acces_token(self) -> bool:
        payload = {'username': self.USERNAME, 'password': self.PASSWORD}
        response = requests.post(f"http://{self.SERVER_IP_ADDRESS}/get_token", data=payload, timeout=1)
        acces_token = response.json().get("access_token")

        self.TOKEN_STATUS_CODE = response.status_code
        if response.status_code == 200:
            self.IS_AUTHENTICATED = True
            self.JWT_TOKEN = acces_token

        return self.IS_AUTHENTICATED,  self.TOKEN_STATUS_CODE

class MouseInput():
    def __init__(self):
        self.last_mouse_position = None
        self.last_click_position = None

    def get_last_mouse_position(self):
        return self.last_mouse_position
    
    def set_last_mouse_position(self, x, y):
        self.last_mouse_position = (x, y)
    
    def clear_last_mouse_position(self):
        self.last_mouse_position = None
        
    def get_last_leftclick_position(self):
        return self.last_click_position
    
    def set_last_leftclick_position(self, x, y):
        self.last_click_position = (x, y)
    
    def clear_last_leftclick_position(self):
        self.last_click_position = None
        
# SETUP ================================================================================================================
DYNAMIC_USER = User(server_ip_address = input("Enter the server IP address: "))
DYNAMIC_MOUSE_INPUT = MouseInput()

CV2_WINDOW_NAME = "Safety-AI Client"
cv2.namedWindow(CV2_WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(CV2_WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

def mouse_callback(event, x, y, flags, param):
    global DYNAMIC_MOUSE_INPUT

    if event == cv2.EVENT_MOUSEMOVE:
        DYNAMIC_MOUSE_INPUT.set_last_mouse_position(x=x, y=y)
    elif event == cv2.EVENT_LBUTTONDOWN:
        DYNAMIC_MOUSE_INPUT.set_last_leftclick_position(x=x, y=y)
    
cv2.setMouseCallback(CV2_WINDOW_NAME, mouse_callback)

DYNAMIC_PROGRAM_STATE = [0,0,0] #page no, page state, other if required -> login page: [0,0,0]
DYNAMIC_PAGE_DEALER = None

# MAIN LOOP ============================================================================================================
while True:
    ui_frame = np.ones((1080, 1920, 3), dtype=np.uint8) * 255  # 255 for white
    if DYNAMIC_PROGRAM_STATE[0] == 0: #PRESS ANY KEY TO CONTINUE  
        picasso.draw_image_on_frame(frame=ui_frame, image_name="press_key_page_template", x=0, y=0, width=1920, height=1080, maintain_aspect_ratio=True)
        cv2.imshow(CV2_WINDOW_NAME, ui_frame)
        pressed_key = cv2.waitKey(0) & 0xFF
        if pressed_key == 27: #ESC
            break
        else:
            DYNAMIC_PROGRAM_STATE = [1,0,0] # Direct to login page
    elif DYNAMIC_PROGRAM_STATE[0] == 1: # LOGIN PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, login_page.LoginPage):
            DYNAMIC_PAGE_DEALER = login_page.LoginPage()            
        DYNAMIC_PAGE_DEALER.do_page(program_state = DYNAMIC_PROGRAM_STATE, cv2_window_name = CV2_WINDOW_NAME, ui_frame = ui_frame, active_user = DYNAMIC_USER, mouse_input = DYNAMIC_MOUSE_INPUT)
    
    elif DYNAMIC_PROGRAM_STATE[0] == 2: # SERVER FAILURE PAGE        
        if not isinstance(DYNAMIC_PAGE_DEALER, server_failure_page.ServerFailurePage):
            DYNAMIC_PAGE_DEALER = server_failure_page.ServerFailurePage()
            
        DYNAMIC_PAGE_DEALER.do_page(program_state = DYNAMIC_PROGRAM_STATE, cv2_window_name = CV2_WINDOW_NAME, ui_frame = ui_frame, active_user = DYNAMIC_USER, mouse_input = DYNAMIC_MOUSE_INPUT)
   
    elif DYNAMIC_PROGRAM_STATE[0] == 3: # USER NOT FOUND PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, user_not_found_page.UserNotFound):
            DYNAMIC_PAGE_DEALER = user_not_found_page.UserNotFound()
            
        DYNAMIC_PAGE_DEALER.do_page(program_state = DYNAMIC_PROGRAM_STATE, cv2_window_name = CV2_WINDOW_NAME, ui_frame = ui_frame, active_user = DYNAMIC_USER, mouse_input = DYNAMIC_MOUSE_INPUT)

cv2.destroyAllWindows()



