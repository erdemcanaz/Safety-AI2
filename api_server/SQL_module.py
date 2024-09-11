import sqlite3, base64, numpy as np, cv2, pprint, uuid, datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os, re, hashlib, time

import PREFERENCES

# (+ 1)     camera_info_table
# (+ 1.1)   last_frames table
# (+ 1.2)   reported_violations
# (+ 1.2.1) image_paths table
# (+ 1.3)   counts_table
# (+ 1.4)   rules_info_table
# (+ 1.5)   shift_counts_table
# (+ 2)     user_info_table
# (+ 2.1)   authorizations_table

class DatabaseManager:
    DEVICE_SECRET_KEY = b"G4ECs6lRrm6HXbtBdMwFoLA18iqF1mMT" # Note that this is an UTF8 encoded byte string. Will be changed in the future, developers should not use this key in production

    def __init__(self, db_path=None, delete_existing_db=False):
        if db_path is None:
            raise ValueError('db_name is required')
        
        if delete_existing_db and os.path.exists(db_path):
            os.remove(db_path) if os.path.exists(db_path) else None
            print(f"#{db_path} is recreated")

        print(f"Connecting to {db_path}")
        self.conn = sqlite3.connect(db_path) # creates a new database if it doesn't exist
        self.ensure_image_paths_table_exists()
        self.ensure_last_frames_table_exists()
        self.ensure_camera_counts_table_exists()
        self.ensure_camera_info_table_exists()
        self.ensure_user_info_table_exists()
        self.ensure_authorization_table_exists()
        self.ensure_shift_counts_table_exists()
        self.ensure_rules_info_table_exists()
        self.ensure_reported_violations_table_exists()

    def close(self):
        self.conn.close()

    # REPORTED_VIOLATIONS TABLE FUNCTIONS
    def ensure_reported_violations_table_exists(self):
        # ========================================================================================================
        # A table to store the reported violations
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # camera_uuid           : is a unique identifier for the camera
        # image_uuid            : is a unique identifier for the image
        # violation_type        : is the type of violation. It can be 'hardhat_violation', 'restricted_area_violation' etc.
        # violation_polygon_str : is the polygon to indicate the area of the violation. "x0n,y0n,x1n,y1n,x2n,y2n,...,xmn,ymn"
        # ========================================================================================================
       
        query = '''
        CREATE TABLE IF NOT EXISTS reported_violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            violation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            violation_uuid TEXT NOT NULL,
            region_name TEXT NOT NULL,
            violation_type TEXT NOT NULL,
            violation_score REAL NOT NULL,
            camera_uuid TEXT NOT NULL,
            image_uuid TEXT NOT NULL
        )
        '''
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_reported_violations
            AFTER UPDATE ON reported_violations
            FOR EACH ROW
            BEGIN
                UPDATE reported_violations 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
        '''

        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()

    def create_reported_violation(self, camera_uuid:str=None, violation_frame:np.ndarray=None, violation_date:datetime.datetime=None, violation_type:str=None, violation_score:float=None, region_name:str=None, save_folder:str=None):
        #def save_encrypted_image_and_insert_path_to_table(self, save_folder:str=None, image:np.ndarray = None, image_category:str = "no-category", image_uuid:str=None)-> str:
        # Save the violation frame as a base64 encoded string and insert the path to the table
        violation_uuid = str(uuid.uuid4())
        image_uuid = str(uuid.uuid4())
        self.save_encrypted_image_and_insert_path_to_table(save_folder=save_folder, image=violation_frame, image_category='violation_frame', image_uuid=image_uuid)
        
        # Insert the violation to the table
        query = '''
        INSERT INTO reported_violations (violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid))
        self.conn.commit()

    def create_reported_violation_v2(self, camera_uuid:str=None, violation_frame_b64:str=None, violation_date_ddmmyyy_hhmmss:str=None, violation_type:str=None, violation_score:float=None, region_name:str=None, save_folder:str=None):
        #def save_encrypted_image_and_insert_path_to_table(self, save_folder:str=None, image:np.ndarray = None, image_category:str = "no-category", image_uuid:str=None)-> str:
        # Save the violation frame as a base64 encoded string and insert the path to the table
        violation_uuid = str(uuid.uuid4())
        image_uuid = str(uuid.uuid4())

        cv2_violation_frame = cv2.imdecode(np.frombuffer(base64.b64decode(violation_frame_b64), np.uint8), cv2.IMREAD_COLOR)
        violation_datetime = datetime.datetime.strptime(violation_date_ddmmyyy_hhmmss, "%d.%m.%Y %H:%M:%S")        
        self.save_encrypted_image_and_insert_path_to_table(save_folder=save_folder, image=cv2_violation_frame, image_category='violation_frame', image_uuid=image_uuid)
        
        # Insert the violation to the table
        query = '''
        INSERT INTO reported_violations (violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (violation_uuid, violation_datetime, region_name, violation_type, violation_score, camera_uuid, image_uuid))
        self.conn.commit()
        return {
            "violation_uuid": violation_uuid,
            "violation_date": violation_datetime,
            "region_name": region_name,
            "violation_type": violation_type,
            "violation_score": violation_score,
            "camera_uuid": camera_uuid,
            "image_uuid": image_uuid
        }
        
    def fetch_reported_violations_between_dates(self, start_date: datetime.datetime = None, end_date: datetime.datetime = None, query_limit: int = 9999) -> list:
        query = '''
        SELECT violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid
        FROM reported_violations
        WHERE violation_date BETWEEN ? AND ?
        ORDER BY violation_date DESC
        LIMIT ?
        '''
        
        # Execute the query with start_date, end_date, and limit parameters
        cursor = self.conn.execute(query, (start_date, end_date, query_limit))
        rows = cursor.fetchall()
        
        if not rows:
            return []
        
        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        
        return result

    def fetch_reported_violation_by_violation_uuid(self, violation_uuid:str=None)-> dict:
        query = '''
        SELECT violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid FROM reported_violations WHERE violation_uuid = ?
        '''
        cursor = self.conn.execute(query, (violation_uuid,))
        row = cursor.fetchone()
        if row is None:
            return None

        column_names = [description[0] for description in cursor.description]
        return dict(zip(column_names, row))
    
    # RULES_INFO_TABLE FUNCTIONS
    def ensure_rules_info_table_exists(self):
        # ========================================================================================================
        # A table to store the rules for the cameras
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # camera_uuid           : is a unique identifier for the camera
        # rule_uuid             : is a unique identifier for the rule
        # rule_department       : for example HSE, QUALITY, SECURITY etc.
        # rule_type             : for example hardhat_violation, restricted_area_violation etc.
        # evaluation_method     : There can be multiple methods to evaluate the same rule. This indicates the method to be used
        # threshold_value       : is the threshold value to evaluate the rule
        # rule_polygon_str      : is the polygon to indicate the area rule is applied. "x0n,y0n,x1n,y1n,x2n,y2n,...,xmn,ymn"
        # ========================================================================================================
        
        query = '''
        CREATE TABLE IF NOT EXISTS rules_info_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            camera_uuid TEXT NOT NULL,
            rule_uuid TEXT NOT NULL,
            rule_department TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            evaluation_method TEXT NOT NULL,
            threshold_value REAL NOT NULL,
            rule_polygon TEXT NOT NULL
        )
        '''
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_rules_info_table
            AFTER UPDATE ON rules_info_table
            FOR EACH ROW
            BEGIN
                UPDATE rules_info_table 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
        '''        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()
    
    def create_rule(self, camera_uuid:str=None, rule_department:str=None, rule_type:str=None, evaluation_method:str=None, threshold_value:float=None, rule_polygon:str=None):
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        # Ensure a camera with the provided camera_uuid exists
        camera_info = self.fetch_camera_info_by_uuid(camera_uuid=camera_uuid)
        if camera_info is None:
            raise ValueError('No camera found with the provided camera_uuid')
        
        # Ensure rule_department is proper
        if rule_department not in PREFERENCES.DEFINED_DEPARTMENTS:
            raise ValueError('Invalid rule_department provided')
        
        # Ensure rule_type is proper
        if rule_type not in PREFERENCES.DEFINED_RULES.keys():
            raise ValueError('Invalid rule_type provided')
        
        # Ensure evaluation_method is proper
        if evaluation_method not in PREFERENCES.DEFINED_RULES[rule_type]:
            raise ValueError('Invalid evaluation_method provided')
                
        # Ensure threshold_value is proper
        if not isinstance(threshold_value, (int, float)):
            raise ValueError('Invalid threshold_value provided')
    
        if not 0 <= threshold_value <= 1:
            raise ValueError('Invalid threshold_value provided, should be between 0 and 1')
        
        # Ensure rule_polygon is proper
        rule_polygon_list = rule_polygon.split(',')
        if len(rule_polygon_list) % 2 != 0:
            raise ValueError('Invalid rule_polygon provided')
        for i in range(0, len(rule_polygon_list), 2):
            float(rule_polygon_list[i]), float(rule_polygon_list[i+1]) # Check if they are floatable
            if float(rule_polygon_list[i]) < 0 or float(rule_polygon_list[i]) > 1 or float(rule_polygon_list[i+1]) < 0 or float(rule_polygon_list[i+1]) > 1:
                raise ValueError('Invalid rule_polygon provided, should be normalized')
                  
        # Generate a UUID for the rule
        rule_uuid = str(uuid.uuid4())
        
        query = '''
        INSERT INTO rules_info_table (camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value, rule_polygon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value, rule_polygon))
        self.conn.commit()

        return {
            "camera_uuid": camera_uuid,
            "rule_uuid": rule_uuid,
            "rule_department": rule_department,
            "rule_type": rule_type,
            "evaluation_method": evaluation_method,
            "threshold_value": threshold_value,
            "rule_polygon": rule_polygon
        }
        
    def delete_rule_by_rule_uuid(self, rule_uuid:str=None)-> bool:
        query = '''
        DELETE FROM rules_info_table WHERE rule_uuid = ?
        '''
        self.conn.execute(query, (rule_uuid,))
        self.conn.commit()

        return {
            "rule_uuid": rule_uuid
        }
    
    def fetch_rules_by_camera_uuid(self, camera_uuid:str=None)-> list:
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        query = '''
        SELECT date_created, date_updated, camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value, rule_polygon FROM rules_info_table WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        rows = cursor.fetchall()
        if rows is None:
            return []

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return result

    def fetch_all_rules(self)-> list:
        query = '''
        SELECT date_created, date_updated, camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value, rule_polygon FROM rules_info_table
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        if rows is None:
            return None

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return result
    
    # CAMERA_INFO_TABLE FUNCTIONS
    def ensure_camera_info_table_exists(self):
        # ========================================================================================================
        # A table to store the information of the cameras
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # camera_uuid           : is a unique identifier for the camera
        # camera_ip_address     : is the IP address of the camera
        # camera_region         : is the region of the camera
        # camera_description    : is the description of the camera
        # NVR_ip_address        : is the IP address of the NVR
        # username              : is the username to access the camera
        # password              : is the password to access the camera
        # stream_path           : is the path to the video stream
        # camera_status         : is the status of the camera. It can be 'active', 'inactive'
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS camera_info_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            camera_uuid TEXT NOT NULL,
            camera_ip_address TEXT NOT NULL,
            camera_region TEXT NOT NULL,
            camera_description TEXT NOT NULL,
            NVR_ip_address TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            stream_path TEXT NOT NULL,
            camera_status TEXT NOT NULL
        )
        '''

        self.conn.execute(query)
        self.conn.commit()

    def create_camera_info(self, camera_uuid:str=None, camera_ip_address:str=None, NVR_ip_address:str = None, camera_region:str=None, camera_description:str=None, username:str=None, password:str=None, stream_path:str=None, camera_status:str=None)-> dict:
        if camera_uuid is None:
            camera_uuid = str(uuid.uuid4())
        # Check if the camera_uuid is valid or not
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        # Check IP is valid or not
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', camera_ip_address):
            raise ValueError('Invalid IP address provided')
        
        if NVR_ip_address is None:
            NVR_ip_address = ""
        elif not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', NVR_ip_address):
            raise ValueError('Invalid NVR-IP address provided')
        
        # Check if the camera_status is valid or not
        if camera_status not in PREFERENCES.DEFINED_CAMERA_STATUSES:
            raise ValueError("Invalid camera_status provided. Valid values are 'active' or 'inactive'")
        
        # Check if username and password are provided
        if username is None or password is None:
            raise ValueError('Username and password are required')
                
        # Format the camera_description and camera_region
        camera_description = "" if camera_description == None else camera_description
        camera_region = "" if camera_region == None else camera_region
        print(f" camera description: {camera_description}, camera region: {camera_region}")


        # Check if the camera_uuid is unique or not
        query = '''
        SELECT id FROM camera_info_table WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        row = cursor.fetchone()
        if row is not None:
            raise ValueError('camera_uuid already exists')
        
        # Check if the camera_ip_address is unique or not
        query = '''
        SELECT id FROM camera_info_table WHERE camera_ip_address = ?
        '''
        cursor = self.conn.execute(query, (camera_ip_address,))
        row = cursor.fetchone()
        if row is not None:
            raise ValueError('camera_ip_address already exists')
        
        query = '''
        INSERT INTO camera_info_table (camera_uuid, camera_ip_address, NVR_ip_address, camera_region, camera_description, username, password, stream_path, camera_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''    
        self.conn.execute(query, (camera_uuid, camera_ip_address, NVR_ip_address, camera_region, camera_description, username, password, stream_path, camera_status))
        self.conn.commit()

        return {
            "camera_uuid": camera_uuid,
            "camera_ip_address": camera_ip_address,
            "NVR_ip_address": NVR_ip_address,
            "camera_region": camera_region,
            "camera_description": camera_description,
            "username": username,
            "password": password,
            "stream_path": stream_path,
            "camera_status": camera_status
        }

    def update_camera_info_attribute(self, camera_uuid:str=None, attribute:str=None, value:str=None)-> bool:
        # Check if the camera_uuid is valid or not
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        # Check if the attribute is valid or not
        if attribute not in ['camera_ip_address', 'camera_region', 'camera_description', 'NVR_ip_address', 'username', 'password', 'stream_path', 'camera_status']:
            raise ValueError(f'Invalid attribute provided {attribute}')
        
        # Check whether camera_region attribute is properly formatted
        if not isinstance(value, str):
            raise ValueError('Attribute value must be a string')
               
        if attribute == 'NVR_ip':
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
                raise ValueError('Invalid IP address provided')
            
        if attribute == 'camera_ip_address':
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
                raise ValueError('Invalid IP address provided')
            
            # Check if the camera_ip_address is unique or not
            query = '''
            SELECT id FROM camera_info_table WHERE camera_ip_address = ?
            '''
            cursor = self.conn.execute(query, (value,))
            row = cursor.fetchone()
            if row is not None:
                raise ValueError('camera_ip_address already exists')
        
        if attribute == 'camera_status' and value not in ['active', 'inactive']:
            raise ValueError("Invalid camera_status provided. Valid values are 'active' or 'inactive'")

        print(f"Updating {attribute} to {value} for camera_uuid {camera_uuid}")
        query = f'''
        UPDATE camera_info_table 
        SET {attribute} = ?, date_updated = CURRENT_TIMESTAMP 
        WHERE camera_uuid = ?
        '''
        self.conn.execute(query, (value, camera_uuid))
        self.conn.commit()

    def delete_camera_info_by_uuid(self, camera_uuid:str=None)-> bool:
        # Check if the camera_uuid is valid or not
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        query = '''
        DELETE FROM camera_info_table WHERE camera_uuid = ?
        '''
        self.conn.execute(query, (camera_uuid,))
        self.conn.commit()

        return {
            "camera_uuid": camera_uuid
        }
    
    def fetch_all_camera_info(self)-> list:
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip_address, camera_region, camera_description, NVR_ip_address, username, password, stream_path, camera_status FROM camera_info_table
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        
        # Get column names from cursor description
        column_names = [description[0] for description in cursor.description]
        
        # Convert each row to a dictionary
        result = [dict(zip(column_names, row)) for row in rows]
        
        keys_to_delete = []
        for d in result:
            for key in keys_to_delete:
                d.pop(key, None)  # Use pop with default to avoid KeyError if key is not present
                
        return result
    
    def fetch_camera_info_by_uuid(self, camera_uuid:str = None) -> dict:
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip_address, camera_region, camera_description, NVR_ip_address, username, password, stream_path, camera_status FROM camera_info_table WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        else:
            # Get column names from cursor description
            column_names = [description[0] for description in cursor.description]
            
            # Create a dictionary using the column names and row data
            return dict(zip(column_names, row))
            
    # IMAGE_PATHS TABLE FUNCTIONS
    def ensure_image_paths_table_exists(self):
        # ========================================================================================================
        # A table to store image encrpytion keys and encrypted images paths
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # image_uuid            : is a unique identifier for the image
        # encryption_key        : is the key used to encrypt the image
        # encrypted_image_path  : is the path to the encrypted image
        # is_deleted            : is a flag to indicate if the encrypted image has been deleted. 0 means not deleted, 1 means deleted
        # image_category        : is a string to categorize the image. It can be anything like 'hard_hat_dataset', 'violation', etc.
        # ========================================================================================================       

        query = '''
        CREATE TABLE IF NOT EXISTS image_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_uuid TEXT NOT NULL,
            encryption_key TEXT NOT NULL,
            encrypted_image_path TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            image_category TEXT NOT NULL DEFAULT 'no-category'
        )
        '''

        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_image_paths
            AFTER UPDATE ON image_paths
            FOR EACH ROW
            BEGIN
                UPDATE image_paths 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''

        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()

    def save_encrypted_image_and_insert_path_to_table(self, save_folder:str=None, image:np.ndarray = None, image_category:str = "no-category", image_uuid:str=None):
        # Ensure image is proper
        if image is None or not isinstance(image, np.ndarray):
            raise ValueError('No image was provided or the image is not a NumPy array')
        
        # Ensure image is encoded properly as a JPEG image. It takes less space than PNG with minimal data loss
        success, encoded_image = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError('Failed to encode image')
                
        # Ensure image_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(image_uuid):
            raise ValueError('Invalid image_uuid provided')
        
        # Ensure image folder exists
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # Ensure UUID is unique
        # NOTE: This is not checked. First encountered UUID is used. This is not a good practice but simpler. It is responsibility of the caller to ensure UUID is unique.

        # Save the encrypted image as a file to the save_folder   
        random_key = os.urandom(32)
        composite_key = hashlib.sha256(random_key + DatabaseManager.DEVICE_SECRET_KEY).digest()     
        iv = os.urandom(16)

        # Create a Cipher object using the key and IV
        cipher = Cipher(algorithms.AES(composite_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(encoded_image.tobytes()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()        
        iv_plus_encrypted_data =  iv + encrypted_data # Append the IV. 

        encrypted_image_path = os.path.join(save_folder, f'{image_uuid}.bin')
        with open(encrypted_image_path, 'wb') as file:
            file.write(iv_plus_encrypted_data)       
        
        # Insert the image path to the table
        query = '''
        INSERT INTO image_paths (image_uuid, encryption_key, encrypted_image_path, is_deleted, image_category)
        VALUES (?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (image_uuid, random_key, encrypted_image_path, 0,  image_category))
        self.conn.commit() # Success
        return image_uuid

    def get_encrypted_image_by_uuid(self, image_uuid: str, get_b64_image_only:bool = False) -> np.ndarray:
        # Retrieve the encrypted image path and random key from the database
        query = '''
        SELECT image_uuid, encryption_key, encrypted_image_path, is_deleted, image_category FROM image_paths WHERE image_uuid = ?
        '''
        cursor = self.conn.execute(query, (image_uuid,))
        row = cursor.fetchone()

        # No image found with the provided image_uuid
        if row is None: 
            raise ValueError('No image path entry found with the provided image_uuid')
        
        # Unpack the row data
        retrieved_image_uuid, random_key, encrypted_image_path, is_deleted, image_category = row
        if is_deleted:
            raise ValueError('Encrypted image file with the provided image_uuid is deleted and cannot be retrieved')
       
        # Ensure the encrypted image file exists, if not, mark the image as deleted in the database
        if not os.path.exists(encrypted_image_path):
            update_query = '''
            UPDATE image_paths SET is_deleted = 1 WHERE image_uuid = ?
            '''
            self.conn.execute(update_query, (image_uuid,))
            self.conn.commit()
            raise ValueError('Encrypted image file not found with the provided image_uuid, will be marked as deleted in the database')
        
        # It is checked that the file exists, so read the encrypted data
        with open(encrypted_image_path, 'rb') as file:
            encrypted_data = file.read()            

        # Re-create the composite key using the random key and the device-specific secret key
        composite_key = hashlib.sha256(random_key + DatabaseManager.DEVICE_SECRET_KEY).digest()

        # Extract the IV from the encrypted data
        iv = encrypted_data[:16]
        encrypted_image_data = encrypted_data[16:]

        # Create a Cipher object using the composite key and IV
        cipher = Cipher(algorithms.AES(composite_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        padded_data = decryptor.update(encrypted_image_data) + decryptor.finalize()

        # Unpad the decrypted data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        image_data = unpadder.update(padded_data) + unpadder.finalize()

        # Decode the byte data back into an image
        image_array = np.frombuffer(image_data, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Ensure the image is proper
        if image is None:
            return None

        # Return both the image and the row data as a dictionary
        return {
            "image_uuid": retrieved_image_uuid,
            "encrypted_image_path": encrypted_image_path,
            "image_b64": base64.b64encode(image_data).decode('utf-8'),
            "image": image if not get_b64_image_only else None,
            "is_deleted": is_deleted,
            "image_category": image_category
        }
        
    # LAST_FRAMES TABLE FUNCTIONS
    def ensure_last_frames_table_exists(self):
        # ========================================================================================================
        # A table to store the last frames of the video streams
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # camera_uuid           : is a unique identifier for the camera
        # camera_ip             : is the IP address of the camera
        # camera_region         : is the region of the camera
        # is_violation_detected : is a flag to indicate if a violation was detected in the last frame. 0 means no violation detected, 1 means violation detected
        # is_person_detected    : is a flag to indicate if a person was detected in the last frame. 0 means no person detected, 1 means person detected
        # last_frame_b64        : is the last frame of the video stream in base64 encoded format
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS last_frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            camera_uuid TEXT NOT NULL,
            camera_ip TEXT NOT NULL,
            camera_region TEXT NOT NULL,
            is_violation_detected INTEGER DEFAULT 0,
            is_person_detected INTEGER DEFAULT 0,
            last_frame_b64 BLOB NOT NULL
        )
        '''        
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_last_frames
            AFTER UPDATE ON last_frames
            FOR EACH ROW
            BEGIN
                UPDATE last_frames 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''
        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()

    def update_last_camera_frame_as_b64string_by_camera_uuid(self, camera_uuid:str= None, is_violation_detected:bool=None, is_person_detected:bool=None, last_frame:np.ndarray=None)-> bool:
        # Ensure image is proper
        if last_frame is None or not isinstance(last_frame, np.ndarray):
            raise ValueError('No image was provided or the image is not a NumPy array')
        
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        camera_info = self.fetch_camera_info_by_uuid(camera_uuid= camera_uuid)
        if camera_info is None:
            raise ValueError('No camera found with the provided camera_uuid')
        
        # Ensure image is encoded properly as a JPEG image. It takes less space than PNG with minimal data loss
        success, encoded_image = cv2.imencode('.jpg', last_frame)
        if not success:
            raise ValueError('Failed to encode image')    
        base64_encoded_image = base64.b64encode(encoded_image.tobytes()) 

        # Save the last frame of the camera to the database as BLOB    
        query = '''
        SELECT id FROM last_frames WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        row = cursor.fetchone()
        if row is None:
            query = '''
            INSERT INTO last_frames (camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected, last_frame_b64)
            VALUES (?, ?, ?, ?, ?, ?)
            '''
            self.conn.execute(query, (camera_uuid, camera_info["camera_ip_address"], camera_info["camera_region"], int(is_violation_detected), int(is_person_detected), sqlite3.Binary(base64_encoded_image))
            )
        else:
            is_person_detected = 1 if is_person_detected else 0
            query = '''
            UPDATE last_frames SET is_violation_detected = ?, is_person_detected = ?, last_frame_b64 = ? WHERE camera_uuid = ?
            '''
            self.conn.execute(query, (int(is_violation_detected), int(is_person_detected), sqlite3.Binary(base64_encoded_image), camera_uuid))
        self.conn.commit()
        return {
            "camera_uuid": camera_uuid,
            "is_violation_detected": is_violation_detected,
            "is_person_detected": is_person_detected
        }

    def get_last_camera_frame_by_camera_uuid(self, camera_uuid:str = None, convert_b64_to_cv2frame:bool=False)-> np.ndarray:

        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        # Retrieve the last frame of the camera from the database
        query = '''
        SELECT camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected, last_frame_b64 FROM last_frames WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        row = cursor.fetchone()

        # No image found with the provided camera_uuid
        if row is None: 
            return None
        
        # Unpack the row data
        retrieved_camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected, last_frame_b64 = row
       
        # keep the image as a base64 encoded string
        return {
            "camera_uuid": retrieved_camera_uuid,
            "camera_ip": camera_ip,
            "camera_region": camera_region,
            "is_violation_detected": is_violation_detected,
            "is_person_detected": is_person_detected,
            "last_frame_b64": last_frame_b64,
            "decoded_last_frame": cv2.imdecode(np.frombuffer(base64.b64decode(last_frame_b64), dtype=np.uint8), cv2.IMREAD_COLOR) if convert_b64_to_cv2frame else None # Decode the base64 string to a NumPy array if needed
        }
        # Succes
        
    def get_all_last_camera_frame_info_without_BLOB(self) -> list:
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected FROM last_frames
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()

        # Get column names from cursor description
        column_names = [description[0] for description in cursor.description]
        
        # Convert each row to a dictionary
        result = [dict(zip(column_names, row)) for row in rows]
        
        return result
              
    # COUNTS_TABLE TABLE FUNCTIONS
    def ensure_camera_counts_table_exists(self):
        # ========================================================================================================
        # A table to store the integer counts of anything useful. It can be people, violations, processed images etc.
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # camera_uuid           : is a unique identifier for the camera
        # camera_ip             : is the IP address of the camera
        # count_type            : is the type of count. It can be 'people' or 'violations' etc.
        # total_count           : is the total count of the type of count
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS counts_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            camera_uuid TEXT NOT NULL,
            camera_ip TEXT NOT NULL,
            count_type TEXT NOT NULL,
            total_count INTEGER NOT NULL
        )
        '''

        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_camera_counts
            AFTER UPDATE ON counts_table
            FOR EACH ROW
            BEGIN
                UPDATE counts_table 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''
        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()

    def update_count(self, camera_uuid:str=None, count_type:str=None, delta_count:int=None)-> bool:
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
                
        # Ensure delta_count is proper
        if not isinstance(delta_count, int):
            raise ValueError('Invalid delta_count provided')
               
        previous_value = 0
        query = '''
        SELECT total_count FROM counts_table WHERE camera_uuid = ? AND count_type = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid, count_type))
        row = cursor.fetchone()
        if row is not None:
            previous_value = row[0]
            query = '''
            UPDATE counts_table SET total_count = ? WHERE camera_uuid = ? AND count_type = ?
            '''
            self.conn.execute(query, (previous_value + delta_count, camera_uuid, count_type))
        else:
            camera_info = self.fetch_camera_info_by_uuid(camera_uuid= camera_uuid)
            if camera_info is None:
                raise ValueError('No camera found with the provided camera_uuid')
            query = '''
            INSERT INTO counts_table (camera_uuid, camera_ip, count_type, total_count)
            VALUES (?, ?, ?, ?)
            '''
            self.conn.execute(query, (camera_uuid, camera_info["camera_ip_address"], count_type, delta_count))

        self.conn.commit()
        return {
            "camera_uuid": camera_uuid,
            "count_type": count_type,
            "previous_value": previous_value,
            "delta_count": delta_count,
        }
        
    def get_counts_by_camera_uuid(self, camera_uuid:str=None)-> int:
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip, count_type, total_count FROM counts_table WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid))
        rows= cursor.fetchall()
        if rows is None:
            return []

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return result

    def fetch_all_counts(self)-> list:
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip, count_type, total_count FROM counts_table
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        if rows is None:
            return []

        column_names = [description[0] for description in cursor.description]
        return [dict(zip(column_names, row)) for row in rows]

    # USER INFO TABLE FUNCTIONS
    def ensure_user_info_table_exists(self):
        # ========================================================================================================
        # A table to store the last frames of the video streams
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # user_uuid             : is a unique identifier for the user
        # username              : is the username of the user
        # personal_fullname     : is the full name of the user
        # hashed_password       : is the hashed password of the user
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_uuid TEXT NOT NULL,
            username TEXT NOT NULL,
            personal_fullname TEXT NOT NULL,
            hashed_password TEXT NOT NULL
        )
        '''        
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_user_info
            AFTER UPDATE ON user_info
            FOR EACH ROW
            BEGIN
                UPDATE user_info 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''
        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()

    def create_user(self, username:str=None, personal_fullname:str=None, plain_password:str=None)-> bool:
        print(f"username: {username}, personal_fullname: {personal_fullname}, plain_password: '{plain_password}', {len(plain_password)}")
        # Ensure username is proper
        if not isinstance(username, str) or len(username) == 0:
            raise ValueError('Invalid username provided')
        
        # Ensure personal_fullname is proper
        if not isinstance(personal_fullname, str) or len(personal_fullname) == 0:
            raise ValueError('Invalid personal_fullname provided')
        
        # Ensure password is proper
        if not isinstance(plain_password, str) or len(plain_password) == 0:
            raise ValueError('Invalid password provided')
        
        # Ensure username is unique
        query = '''
        SELECT id FROM user_info WHERE username = ?
        '''
        cursor = self.conn.execute(query, (username,))
        row = cursor.fetchone()
        if row is not None:
            raise ValueError('Username already exists')
        
        # Generate a UUID for the user
        user_uuid = str(uuid.uuid4())
        
        # Hash the password
        hashed_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        
        query = '''
        INSERT INTO user_info (user_uuid, username, personal_fullname, hashed_password)
        VALUES (?, ?, ?, ?)
        '''
        self.conn.execute(query, (user_uuid, username, personal_fullname, hashed_password))
        self.conn.commit()

        return {
            "user_uuid": user_uuid,
            "username": username,
            "personal_fullname": personal_fullname,            
        }

    def authenticate_user(self, username:str=None, plain_password:str=None)->bool:
        hashed_password_candidate = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        try:
            user_dict = self.get_user_by_username(username=username)
            if user_dict["hashed_password"] == hashed_password_candidate:
                return True
            else:
                return False
        except Exception as e:
            print("Exception:", str(e))
            return False
        
    def get_user_by_username(self, username:str=None)-> dict:
        # Ensure username is proper
        if not isinstance(username, str) or len(username) == 0:
            raise ValueError('Invalid username provided')
        
        query = '''
        SELECT date_created, date_updated, user_uuid, username, personal_fullname, hashed_password FROM user_info WHERE username = ?
        '''
        cursor = self.conn.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return None
        
        column_names = [description[0] for description in cursor.description]
        return dict(zip(column_names, row))
    
    def get_user_by_uuid(self, uuid:str=None):
        query = '''
        SELECT date_created, date_updated, user_uuid, username, personal_fullname, hashed_password FROM user_info WHERE user_uuid = ?
        '''
        cursor = self.conn.execute(query, (uuid,))
        row = cursor.fetchone()
        if row is None:
            return None
        
        column_names = [description[0] for description in cursor.description]
        return dict(zip(column_names, row))

    def update_user_password_by_uuid(self, user_uuid:str=None, new_plain_password:str=None):
        # Ensure password is proper
        if not isinstance(new_plain_password, str) or len(new_plain_password) == 0:
            raise ValueError('Invalid password provided')
        
        # Hash the password
        hashed_password = hashlib.sha256(new_plain_password.encode('utf-8')).hexdigest()
        
        query = '''
        UPDATE user_info SET hashed_password = ? WHERE user_uuid = ?
        '''
        self.conn.execute(query, (hashed_password, user_uuid))
        self.conn.commit()

    def fetch_all_user_info(self):
        query = '''
        SELECT date_created, date_updated, user_uuid, username, personal_fullname, hashed_password FROM user_info
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        if rows is None:
            return []

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return result

    # AUTHORIZATION TABLE FUNCTIONS
    def ensure_authorization_table_exists(self):
        # ========================================================================================================
        # A table to store the authorizations of the users. One user can be linked to multiple authorizations
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # user_uuid             : is a unique identifier for the user
        # authorization_uuid    : is a unique identifier for the authorization
        # authorization_name    : is the name of the authorization
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS authorization_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_uuid TEXT NOT NULL,
            authorization_uuid TEXT NOT NULL,
            authorization_name TEXT NOT NULL
        )
        '''
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_authorization_table
            AFTER UPDATE ON authorization_table
            FOR EACH ROW
            BEGIN
                UPDATE authorization_table 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
        '''
        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()
        
        self.conn.execute(query)
        self.conn.commit()
    
    def authorize_user(self, user_uuid:str=None, authorization_name:str=None):
        # Ensure user_uuid is proper
        if not isinstance(user_uuid, str) or len(user_uuid) == 0:
            raise ValueError('Invalid user_uuid provided')
        
        # Ensure authorization_name is proper
        if not isinstance(authorization_name, str) or len(authorization_name) == 0:
            raise ValueError('Invalid authorization_name provided')
        
        if not authorization_name in PREFERENCES.DEFINED_AUTHORIZATIONS:
            raise ValueError("Invalid 'authorization_name' provided")
        
        # Ensure user exists
        user_info = self.get_user_by_uuid(uuid=user_uuid)
        if user_info is None:
            raise ValueError('No user found with the provided user_uuid')
        
        query = '''
        INSERT INTO authorization_table (user_uuid, authorization_name, authorization_uuid)
        VALUES (?, ?, ?)
        '''
        self.conn.execute(query, (user_uuid, authorization_name, str(uuid.uuid4())))
        self.conn.commit()

    def remove_authorization(self, authorization_uuid:str = None):
        query = '''
        DELETE FROM authorization_table WHERE authorization_uuid = ?
        '''
        self.conn.execute(query, (authorization_uuid,))
        self.conn.commit()

    def fetch_user_authorizations(self, user_uuid:str=None):
        # Ensure user_uuid is proper
        if not isinstance(user_uuid, str) or len(user_uuid) == 0:
            raise ValueError('Invalid user_uuid provided')
        
        query = '''
        SELECT date_created, date_updated, user_uuid, authorization_uuid, authorization_name FROM authorization_table WHERE user_uuid = ?
        '''
        cursor = self.conn.execute(query, (user_uuid,))
        rows = cursor.fetchall()
        if rows is None:
            return []

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return result

    def fetch_all_authorizations(self):
        query = '''
        SELECT date_created, date_updated, user_uuid, authorization_uuid, authorization_name FROM authorization_table
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        if rows is None:
            return []

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return result

    # SHIFT COUNTS TABLE
    def ensure_shift_counts_table_exists(self):
        # ========================================================================================================
        # A table to store the integer counts of a SHIFT anything useful. It can be people, violations, processed images etc.
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
        # date_created          : is the date and time the record was created
        # date_updated          : is the date and time the record was last updated
        # shift_date_ddmmyyyy   : is the date of the shift in the format of 'dd.mm.yyyy'
        # shift_no              : is the number of the shift. It can be '0','1','2'
        # camera_uuid           : is a unique identifier for the camera
        # camera_ip             : is the IP address of the camera
        # count_type            : is the type of count. It can be 'people' or 'violations' etc.
        # total_count           : is the total count of the type of count
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS shift_counts_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shift_date_ddmmyyyy TEXT NOT NULL,
            shift_no TEXT NOT NULL,
            camera_uuid TEXT NOT NULL,
            camera_ip TEXT NOT NULL,
            count_type TEXT NOT NULL,
            total_count INTEGER NOT NULL
        )
        '''

        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_shift_counts
            AFTER UPDATE ON shift_counts_table
            FOR EACH ROW
            BEGIN
                UPDATE shift_counts_table 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''
        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()

    def update_shift_count(self, camera_uuid:str=None, count_type:str=None, shift_date_ddmmyyyy:str = None, shift_no:str=None, delta_count:int=None)-> bool:
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
                
        # Ensure delta_count is proper
        if not isinstance(delta_count, int):
            raise ValueError('Invalid delta_count provided')
               
        previous_value = 0
        query = '''
        SELECT total_count FROM shift_counts_table WHERE camera_uuid = ? AND count_type = ? AND shift_date_ddmmyyyy = ? AND shift_no = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid, count_type, shift_date_ddmmyyyy, shift_no))
        row = cursor.fetchone()
        if row is not None:
            previous_value = row[0]
            query = '''
            UPDATE shift_counts_table SET total_count = ? WHERE camera_uuid = ? AND count_type = ?
            '''
            self.conn.execute(query, (previous_value + delta_count, camera_uuid, count_type))
        else:
            camera_info = self.fetch_camera_info_by_uuid(camera_uuid= camera_uuid)
            if camera_info is None:
                raise ValueError('No camera found with the provided camera_uuid')
            query = '''
            INSERT INTO shift_counts_table (camera_uuid, camera_ip, count_type, shift_date_ddmmyyyy, shift_no, total_count)
            VALUES (?, ?, ?, ?, ?, ?)
            '''
            self.conn.execute(query, (camera_uuid, camera_info["camera_ip_address"], count_type, shift_date_ddmmyyyy, str(shift_no), delta_count))

        self.conn.commit()
        return {
            "camera_uuid": camera_uuid,
            "count_type": count_type,
            "shift_date_ddmmyyyy": shift_date_ddmmyyyy,
            "shift_no": shift_no,
            "previous_value": previous_value,
            "delta_count": delta_count,
        }

    def get_shift_counts_between_dates(self, start_date: datetime.datetime=None, end_date: datetime.datetime=None) -> list:
        # One can fetch for a relatively elastic start and end date with additional entries, then post-filter the results in the application
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip, shift_date_ddmmyyyy, shift_no, count_type, total_count 
        FROM shift_counts_table 
        WHERE date_updated BETWEEN ? AND ?
        '''
        cursor = self.conn.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        # Convert each row to a dictionary
        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]

        return result