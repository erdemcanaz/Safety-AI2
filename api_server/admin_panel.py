import uuid, os, time, pprint, requests, datetime
from pathlib import Path
import cv2, numpy as np
import SQL_module
import preferences

class AdminPanel:       

    def __init__(self, db_path:str = None, delete_existing_db:bool = False):
        if db_path is None:
            raise ValueError("db_path cannot be None")
        self.database_manager = SQL_module.DatabaseManager(db_path = db_path, delete_existing_db=delete_existing_db)
        time.sleep(1)
        
    def create_admin_user(self):
        username = input("Enter username:".ljust(50))
        plain_password = input("Enter plain password".ljust(50))
        personal_fullname = input("Enter personal fullname".ljust(50))

        AUTHORIZATIONS = [
            'MENAGE_USERS',
            'ISG_UI',
            'QUALITY_UI',
            'SECURITY_UI',
            'EDIT_RULES',
            'REPORT_VIOLATIONS',
            'SUMMARY_PAGE',
            'UPDATE_CAMERAS',
            'IOT_DEVICES'
        ]

        self.database_manager.create_user(username=username, personal_fullname=personal_fullname, plain_password=plain_password)
        user_uuid=self.database_manager.get_user_by_username(username=username)
        for authorization_name in AUTHORIZATIONS:
            self.database_manager.authorize_user(user_uuid=user_uuid, authorization_name=authorization_name)

        print("Admin user is created succesfully")
        time.sleep(2)

    def camera_info_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Create camera info",
            "2": "Update camera info attribute",
            "3": "Fetch all camera info",
            "4": "Fetch camera info by uuid",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__camera_info_table_create_camera_info()
            elif chosen_task == "2":
                self.__camera_info_table_update_camera_info_attribute()
            elif chosen_task == "3":
                self.__camera_info_table_fetch_all_camera_info()
            elif chosen_task == "4":
                self.__fetch_camera_info_by_uuid()
    
    def __camera_info_table_create_camera_info(self):
        # Define the length of the longest prompt
        prompt_length = 50

        camera_uuid = str(uuid.uuid4())       
        print(f"\n{'Camera UUID:':<{prompt_length}}{camera_uuid}")

        camera_ip_address = input("Please enter the camera IP address:".ljust(prompt_length))
        NVR_ip_address = input("Please enter the NVR IP address:".ljust(prompt_length))
        camera_region = input("Please enter the camera region:".ljust(prompt_length))
        camera_description = input("Please enter the camera description:".ljust(prompt_length))
        username = input("Please enter the username:".ljust(prompt_length))
        password = input("Please enter the password:".ljust(prompt_length))
        stream_path = input("Please enter the stream path:".ljust(prompt_length))
        camera_status = input("Please enter the camera status (active/inactive):".ljust(prompt_length))
        self.database_manager.create_camera_info(camera_uuid=camera_uuid, camera_ip_address=camera_ip_address, NVR_ip_address=NVR_ip_address, camera_region=camera_region, camera_description=camera_description, username=username, password=password, stream_path=stream_path, camera_status=camera_status)
        
        print("Camera info created successfully")
        time.sleep(2)
        

        pass
    
    def __camera_info_table_update_camera_info_attribute(self):
        # Define the length of the longest prompt
        prompt_length = 50
        attributes_list = ['camera_region', 'camera_description', 'NVR_ip_address', 'username', 'password', 'stream_path', 'camera_status']

        print()        
        camera_uuid = input("Please enter the camera UUID:".ljust(prompt_length))
        for index, attribute in enumerate(attributes_list):
            print(f"{index}: {attribute}")
        choosen_attribute_index = int(input("Please select the attribute to update:".ljust(prompt_length)))
        choosen_attribute = attributes_list[choosen_attribute_index]
        choosen_value = input(f"Please enter the new value for {choosen_attribute}:".ljust(prompt_length))

        self.database_manager.update_camera_info_attribute(camera_uuid=camera_uuid, attribute=choosen_attribute, value=choosen_value)     

        print("Camera info updated successfully")
        time.sleep(2)
    
    def __camera_info_table_fetch_all_camera_info(self):
        cameras = self.database_manager.fetch_all_camera_info()
        pprint.pprint(cameras)
        print("Fetched all camera info successfully")
        input("Press any key to continue...")

    def __fetch_camera_info_by_uuid(self):
        camera_uuid = input("\nPlease enter the camera UUID:")
        camera = self.database_manager.fetch_camera_info_by_uuid(camera_uuid=camera_uuid)
        pprint.pprint(camera)
        print("Fetched camera info successfully")
        input("Press any key to continue...")

    def image_paths_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Save encrypted image and insert path to table",
            "2": "Get encrypted image by uuid",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__save_encrypted_image_and_insert_path_to_table()
            elif chosen_task == "2":
                self.__get_encrypted_image_by_uuid()

    def __save_encrypted_image_and_insert_path_to_table(self):
        # Define the length of the longest prompt
        prompt_length = 50

        current_folder = Path(__file__).resolve().parent
        print(f"\nCurrent folder: {current_folder}")
        relative_folder_path = input("Please enter the relative folder path:".ljust(prompt_length))
        if relative_folder_path[0] == "\\" or relative_folder_path[0] == "/": relative_folder_path = relative_folder_path[1:]
        save_folder = current_folder / relative_folder_path
        print(f"\nSave folder: {save_folder}")

        image_uuid = str(uuid.uuid4())
        print(f"{'Image UUID:':<{prompt_length}}{image_uuid}")
        image_category = input("Image category:".ljust(prompt_length))

        image_url = input("Please enter an image url to be saved:".ljust(prompt_length))
        response = requests.get(image_url)
        if response.status_code == 200:
            image_array = np.frombuffer(response.content, np.uint8)
            downloaded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            cv2.imshow("Downloaded Image", downloaded_image)
            cv2.waitKey(2500)
            cv2.destroyAllWindows()
        else:
            print("Failed to download the image. Please check the URL and try again.")
            time.sleep(2)
            return
        
        self.database_manager.save_encrypted_image_and_insert_path_to_table(save_folder=save_folder, image = downloaded_image, image_uuid=image_uuid, image_category=image_category)
        print("Image saved and path inserted to table successfully")
        time.sleep(2)

    def __get_encrypted_image_by_uuid(self):
        image_uuid = input("\nPlease enter the image UUID:")
        image_dict = self.database_manager.get_encrypted_image_by_uuid(image_uuid=image_uuid)
        pprint.pprint(image_dict)
        image = image_dict.get("image")
        if image is not None:
            cv2.imshow("Encrypted Image", image)
            cv2.waitKey()
            cv2.destroyAllWindows()
        else:
            print("No image found with the given UUID")
            time.sleep(2)

    def last_frames_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Update last camera frame by camera uuid",
            "2": "Get last camera frame by camera uuid",
            "3": "Get all last camera frame info without BLOB",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__update_last_camera_frame_by_camera_uuid()
            elif chosen_task == "2":
                self.__get_last_camera_frame_by_camera_uuid()
            elif chosen_task == "3":
                self.__get_all_last_camera_frame_info_without_BLOB()

    def __update_last_camera_frame_by_camera_uuid(self):
        # Define the length of the longest prompt
        prompt_length = 50

        #camera_uuid:str= None, camera_ip:str=None, is_violation_detected:bool=None, is_person_detected:bool=None, camera_region:str=None, last_frame:np.ndarray=None)-> bool:
        camera_uuid = input("Please enter the camera UUID:".ljust(prompt_length))
        is_violation_detected = True if input("Violation detected? (y/n):".ljust(prompt_length)) == "y" else False
        is_person_detected = True if input("Person detected? (y/n):".ljust(prompt_length)) == "y" else False
       
        image_url = input("Please enter an image url to be saved:".ljust(prompt_length))
        response = requests.get(image_url)
        if response.status_code == 200:
            image_array = np.frombuffer(response.content, np.uint8)
            downloaded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            cv2.imshow("Downloaded Image", downloaded_image)
            cv2.waitKey(2500)
            cv2.destroyAllWindows()
        else:
            print("Failed to download the image. Please check the URL and try again.")
            time.sleep(2)
            return
        
        self.database_manager.update_last_camera_frame_as_b64string_by_camera_uuid(camera_uuid=camera_uuid, last_frame=downloaded_image, is_person_detected= is_person_detected, is_violation_detected= is_violation_detected)

        print("Last camera frame updated successfully")
        time.sleep(2)

    def __get_last_camera_frame_by_camera_uuid(self):
        camera_uuid = input("\nPlease enter the camera UUID:")
        last_frame_dict = self.database_manager.get_last_camera_frame_by_camera_uuid(camera_uuid=camera_uuid, convert_b64_to_cv2frame = True)
        
        if last_frame_dict is None:
            print("No last frame found with the given UUID")
            time.sleep(2)
            return
        
        last_frame = last_frame_dict.get("decoded_last_frame")    
        cv2.imshow("Last Frame", last_frame)
        cv2.waitKey()
        cv2.destroyAllWindows()     

    def __get_all_last_camera_frame_info_without_BLOB(self):
        last_frames = self.database_manager.get_all_last_camera_frame_info_without_BLOB()
        pprint.pprint(last_frames)
        print("Fetched all last camera frame info without BLOB successfully")
        input("Press any key to continue...")

    def camera_counts_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Update camera counts by camera uuid",
            "2": "Get camera counts by camera uuid",
            "3": "Get all camera counts",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__update_camera_counts_by_camera_uuid()
            elif chosen_task == "2":
                self.__get_camera_counts_by_camera_uuid()
            elif chosen_task == "3":
                self.__fetch_all_camera_counts()

    def __update_camera_counts_by_camera_uuid(self):
        # Define the length of the longest prompt
        prompt_length = 50

        camera_uuid = input("Please enter the camera UUID:".ljust(prompt_length))
        count_type = input("Please enter the count type:".ljust(prompt_length))
        delta_count = int(input("Please enter the delta-count:".ljust(prompt_length)))

        self.database_manager.update_count(camera_uuid=camera_uuid, count_type=count_type, delta_count=delta_count)

        print("Camera counts updated successfully")
        time.sleep(2)

    def __get_camera_counts_by_camera_uuid(self):
        camera_uuid = input("\nPlease enter the camera UUID:")
        camera_counts = self.database_manager.get_counts_by_camera_uuid(camera_uuid=camera_uuid)
        pprint.pprint(camera_counts)
        print("Fetched camera counts successfully")
        input("Press any key to continue...")

    def __fetch_all_camera_counts(self):
        list_of_dicts = self.database_manager.fetch_all_camera_counts()
        pprint.pprint(list_of_dicts)
        print("\nFetched all camera counts successfully")
        input("Press any key to continue...")
    
    def user_info_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Create User",
            "2": "Authenticate User",
            "3": "Get User by Username",
            "4": "Get User by UUID",
            "5": "Update User Password by UUID",
            "6": "Fetch all user info table"
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__create_user()
            elif chosen_task == "2":
                self.__authenticate_user()
            elif chosen_task == "3":
                self.__get_user_by_username()
            elif chosen_task == "4":
                self.__get_user_by_uuid()
            elif chosen_task == "5":
                self.__update_user_password_by_uuid()
            elif chosen_task == "6":
                self.__fetch_all_user_info()
         
    def __create_user(self):
        username = input("Enter username:".ljust(50))
        plain_password = input("Enter plain password".ljust(50))
        personal_fullname = input("Enter personal fullname".ljust(50))

        self.database_manager.create_user(username=username, personal_fullname=personal_fullname, plain_password=plain_password)
        print("User is created succesfully")
        time.sleep(2)

    def __get_user_by_username(self):
        username = input("Enter username:".ljust(50))
        user_dict = self.database_manager.get_user_by_username(username= username)
        pprint.pprint(user_dict)
        input("Press any key to continue...")

    def __get_user_by_uuid(self):
        user_uuid = input("Enter user uuid:".ljust(50))
        user_dict = self.database_manager.get_user_by_uuid(uuid = user_uuid)
        pprint.pprint(user_dict)
        input("Press any key to continue...")

    def __update_user_password_by_uuid(self):
        user_uuid = input("Enter user uuid:".ljust(50))
        new_plain_password = input("Enter new plain password:".ljust(50))
        self.database_manager.update_user_password_by_uuid(user_uuid=user_uuid, new_plain_password= new_plain_password)
        print("Password is succesfully updated")
        time.sleep(2)

    def __authenticate_user(self):
        username = input("Enter username:".ljust(50))
        plain_password = input("Enter plain password:".ljust(50))
        is_authenticated = self.database_manager.authenticate_user(username=username, plain_password=plain_password)
        if is_authenticated:
            print("+++++++ AUTHENTICATED +++++++")
        else:
            print("------- NOT AUTHENTICATED --------")

        time.sleep(2.5)

    def __fetch_all_user_info(self):
        list_of_dicts = self.database_manager.fetch_all_user_info()
        pprint.pprint(list_of_dicts)
        print("\nFetched all user info successfully")
        input("Press any key to continue...")

    def authorizations_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Authorize User",
            "2": "Remove Authorization",
            "3": "Fetch user authorizations",
            "4": "Fetch all authorizations",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__authorize_user()
            elif chosen_task == "2":
                self.__remove_authorization()
            elif chosen_task == "3":
                self.__fetch_user_authorizations()
            elif chosen_task == "4":
                self.__fetch_all_authorizations()

    def __authorize_user(self):
        user_uuid = input("Enter user UUID:".ljust(50))
        authorization_name = input("Enter authorization name:".ljust(50))
        self.database_manager.authorize_user(user_uuid=user_uuid, authorization_name=authorization_name)
        print("User is authorized succesfully")
        time.sleep(2)

    def __remove_authorization(self):
        authorization_uuid = input("Enter Authorization UUID:".ljust(50))
        self.database_manager.remove_authorization(authorization_uuid= authorization_uuid)
        print("Authorization is removed succesfully")
        time.sleep(2)

    def __fetch_user_authorizations(self):
        user_uuid = input("Enter user UUID:".ljust(50))
        list_of_dicts = self.database_manager.fetch_user_authorizations(user_uuid=user_uuid)
        pprint.pprint(list_of_dicts)
        print("\nFetched user authorizations successfully")
        input("Press any key to continue...")

    def __fetch_all_authorizations(self):
        list_of_dicts = self.database_manager.fetch_all_authorizations()
        pprint.pprint(list_of_dicts)
        print("\nFetched all authorizations successfully")
        input("Press any key to continue...")

    def shift_counts_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Update Shift Count",
            "2": "Get Shift Counts Between Dates",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__update_shift_count()
            elif chosen_task == "2":
                self.__get_shift_counts_between_dates()

    def __update_shift_count(self):
        camera_uuid = input("Enter Camera UUID:".ljust(50))
        count_type = input("Enter Count Type:".ljust(50))
        shift_date_ddmmyyyy = input("Enter Shift Date (dd.mm.yyyy)".ljust(50))
        shift_no = input("Enter Shift No:".ljust(50))
        delta_count = int(input("Enter delta-count:".ljust(50)))

        self.database_manager.update_shift_count(camera_uuid=camera_uuid, count_type=count_type, shift_date_ddmmyyyy=shift_date_ddmmyyyy, shift_no= shift_no, delta_count= delta_count)
        print("Shift count is updated succesfully")
        time.sleep(2)

    def __get_shift_counts_between_dates(self):
        start_date_ddmmyyyy = input("Enter Fetch Start Date (dd.mm.yyyy)".ljust(50))
        end_date_ddmmyyyy = input("Enter Fetch End Date (dd.mm.yyyy)".ljust(50))
        related_counts = self.database_manager.get_shift_counts_between_dates(start_date_ddmmyyyy=start_date_ddmmyyyy,end_date_ddmmyyyy=end_date_ddmmyyyy)
        pprint.pprint(related_counts)
        print("Related shift counts are fetched")
        input("Press any key to continue...")
        
    def rules_info_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Create Rule",
            "2": "Fetch Rules by Camera UUID",
            "3": "Fetch All Rules",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__create_rule()
            elif chosen_task == "2":
                self.__fetch_rules_by_camera_uuid()
            elif chosen_task == "3":
                self.__fetch_all_rules()

    def __create_rule(self):
        #    def create_rule(self, camera_uuid:str=None, rule_department:str=None, rule_type:str=None, evaluation_method:str=None, threshold_value:float=None, rule_polygon:str=None)-> bool:

        camera_uuid = input("Enter Camera UUID:".ljust(50))
        rule_department = input("Enter Rule Department:".ljust(50))
        rule_type = input("Enter Rule Type:".ljust(50))
        evaluation_method = input("Enter Evaluation Method:".ljust(50))
        threshold_value = float(input("Enter Threshold Value:".ljust(50)))
        rule_polygon = input("Enter Rule Polygon:".ljust(50))

        self.database_manager.create_rule(camera_uuid=camera_uuid, rule_department=rule_department, rule_type=rule_type, evaluation_method=evaluation_method, threshold_value=threshold_value, rule_polygon=rule_polygon)
        print("Rule is created succesfully")
        time.sleep(2)
    
    def __fetch_rules_by_camera_uuid(self):
        camera_uuid = input("Enter Camera UUID:".ljust(50))
        list_of_dicts = self.database_manager.fetch_rules_by_camera_uuid(camera_uuid=camera_uuid)
        pprint.pprint(list_of_dicts)
        print("\nFetched rules successfully")
        input("Press any key to continue...")

    def __fetch_all_rules(self):
        list_of_dicts = self.database_manager.fetch_all_rules()
        pprint.pprint(list_of_dicts)
        print("\nFetched all rules successfully")
        input("Press any key to continue...")

    def reported_violations_table(self):
        TASKS = {
            "0": "Previous Menu",
            "1": "Create a Reported Violation",
            "2": "Fetch Violations Between Dates",
            "3": "Fetch Reported Violations by Violation UUID",
        }
        while True:
            os.system(preferences.CLEAR_TERMINAL_COMMAND)
            for key, value in TASKS.items(): print(f"{key}: {value}")
            chosen_task = input("Please select a task to perform:".ljust(50))
            if chosen_task == "0":
                break
            elif chosen_task == "1":
                self.__create_reported_violation()
            elif chosen_task == "2":
                self.__fetch_violations_between_dates()
            elif chosen_task == "3":
                self.__fetch_reported_violation_by_violation_uuid()

    def __create_reported_violation(self):
        #     def create_reported_violation(self, camera_uuid:str=None, violation_frame:np.ndarray=None, violation_date:datetime.datetime=None, violation_type:str=None, violation_score:float=None, region_name:str=None):
        camera_uuid = input("Enter Camera UUID:".ljust(50))
        violation_date = input("Enter Violation Date (dd.mm.yyyy HH:MM):".ljust(50))
        violation_date = datetime.datetime.strptime(violation_date, "%d.%m.%Y %H:%M")
        violation_type = input("Enter Violation Type:".ljust(50))
        violation_score = float(input("Enter Violation Score:".ljust(50)))
        region_name = input("Enter Region Name:".ljust(50))

        image_url = input("Please enter an image url to be saved:".ljust(50))
        response = requests.get(image_url)
        if response.status_code == 200:
            image_array = np.frombuffer(response.content, np.uint8)
            downloaded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            cv2.imshow("Downloaded Image", downloaded_image)
            cv2.waitKey(2500)
            cv2.destroyAllWindows()
        else:
            print("Failed to download the image. Please check the URL and try again.")
            time.sleep(2)
            return
        

        save_folder = Path(__file__).resolve().parent / f"images/violations/{violation_date.strftime('%Y_%m_%d')}"
        self.database_manager.create_reported_violation(camera_uuid=camera_uuid, violation_frame=downloaded_image, violation_date=violation_date, violation_type=violation_type, violation_score=violation_score, region_name=region_name, save_folder = save_folder)
        print("Reported violation is created succesfully")
        time.sleep(2)

    def __fetch_violations_between_dates(self):
        start_date_ddmmyyyy = input("Enter Fetch Start Date (dd.mm.yyyy)".ljust(50))
        end_date_ddmmyyyy = input("Enter Fetch End Date (dd.mm.yyyy)".ljust(50))
        start_date = datetime.datetime.strptime(start_date_ddmmyyyy, "%d.%m.%Y")
        end_date = datetime.datetime.strptime(end_date_ddmmyyyy, "%d.%m.%Y")

        list_of_dicts = self.database_manager.fetch_reported_violations_between_dates(start_date=start_date, end_date=end_date)
        pprint.pprint(list_of_dicts)
        print("\nFetched violations successfully")
        input("Press any key to continue...")

    def __fetch_reported_violation_by_violation_uuid(self):
        violation_uuid = input("Enter Violation UUID:".ljust(50))
        violation_dict = self.database_manager.fetch_reported_violation_by_violation_uuid(violation_uuid=violation_uuid)
        pprint.pprint(violation_dict)
        input("Press any key to continue...")
      
if __name__ == "__main__":
    print("connecting to database ", preferences.SQL_DATABASE_PATH)
    should_delete_existing_db = True if input("Overwrite existing database? (write 'overwrite'):".ljust(50)) == "overwrite" else False
    admin_panel = AdminPanel(db_path=preferences.SQL_DATABASE_PATH, delete_existing_db=should_delete_existing_db)

    TASKS = {
        "0": "Exit",
        "1": "Camera Info Table",
        "2": "Image Paths Table",
        "3": "Last Frames Table",
        "4": "Counts Table",
        "5": "User Info Table",
        "6": "Authorizations Table",
        "7": "Shift Counts Table",
        "8": "Rules Info Table",
        "9": "Reported Violations Table",
        "10": "Create Admin User"
    }
    while True:
        os.system(preferences.CLEAR_TERMINAL_COMMAND)
        for key, value in TASKS.items(): print(f"{key}: {value}")
        chosen_task = input("Please select a table to work with:".ljust(50))

        if chosen_task == "0":
            break
        elif chosen_task == "1":
            admin_panel.camera_info_table()
        elif chosen_task == "2":
            admin_panel.image_paths_table()
        elif chosen_task == "3":
            admin_panel.last_frames_table()
        elif chosen_task == "4":
            admin_panel.camera_counts_table()
        elif chosen_task == "5":
            admin_panel.user_info_table()
        elif chosen_task == "6":
            admin_panel.authorizations_table()
        elif chosen_task == "7":
            admin_panel.shift_counts_table() 
        elif chosen_task == "8":
            admin_panel.rules_info_table()
        elif chosen_task == "9":
            admin_panel.reported_violations_table()
        elif chosen_task == "10":
            admin_panel.create_admin_user()
        else:
            print("Invalid choice. Please try again.")
            time.sleep(2)     