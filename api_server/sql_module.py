import sqlite3, base64, numpy as np, cv2, pprint, uuid, datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os, re, hashlib, time, sys, pprint
from pathlib import Path
import PREFERENCES

class SQLManager:

    def __init__(self, db_path=None, verbose=False, overwrite_existing_db=False): 
        self.last_time_old_violations_cleaned_up = 0 #time.time(), so that it is cleaned up during the first run
        self.DB_PATH = db_path
        self.VERBOSE = verbose     

        #check if the database exists and delete it if it does before creating a new one
        if overwrite_existing_db and os.path.exists(db_path):
            os.remove(db_path) if os.path.exists(db_path) else None
            if self.VERBOSE: print(f"Deleted and recreated database at '{db_path}'")

        #check if the path folder exists, if not, create it 
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            if self.VERBOSE: print(f"Created the parent folder(s) for the database at '{os.path.dirname(db_path)}'")

        #NOTE: creates a new database if it doesn't exist
        self.conn = sqlite3.connect(self.DB_PATH) 

        #Ensure required tables exist
        self.__ensure_user_info_table_exists()
        self.__ensure_authorization_table_exists()
        self.__ensure_camera_info_table_exists()
        self.__ensure_counts_table_exists()
        self.__ensure_rules_info_table_exists()
        self.__ensure_camera_last_frames_table_exists()
        self.__ensure_image_paths_table_exists()
        self.__ensure_reported_violations_table_exists()
        self.__ensure_iot_devices_table_exists()
        self.__ensure_iot_device_and_rule_relations_table_exists()

        #Ensure a user is registered for the safety AI | first user !
        self.__create_safety_ai_user() 
        #Ensure a user is registered for the admin     | second user !
        self.__create_admin_user()
        self.__sync_encrypted_images_and_image_paths_table() # Delete the encrypted images that are not in the table, and delete the image paths with no corresponding encrypted image
        self.__delete_timeouted_violations() # Delete the violations and images that are older than PREFERENCES.VIOLATIONS_AND_IMAGES_TIME_TO_LIVE_DAYS

        #Initialize image folders
        self.DATA_FOLDER_PATH_LOCAL = PREFERENCES.DATA_FOLDER_PATH_LOCAL
        self.DATA_FOLDER_PATH_EXTERNAL = PREFERENCES.DATA_FOLDER_PATH_EXTERNAL 
        print(f"DATA_FOLDER_PATH_LOCAL: {self.DATA_FOLDER_PATH_LOCAL}")
        print(f"DATA_FOLDER_PATH_EXTERNAL: {self.DATA_FOLDER_PATH_EXTERNAL}")
   
    def close(self):
        self.conn.close()
    
    @staticmethod
    def delete_database():   
        db_path = PREFERENCES.SQL_DATABASE_FILE_PATH_LOCAL
        local_database_backups_folder_path = PREFERENCES.DATA_FOLDER_PATH_LOCAL / PREFERENCES.MUST_EXISTING_DATA_SUBFOLDER_PATHS['api_server_database_backups']
        if PREFERENCES.check_if_folder_accesible(folder_path=local_database_backups_folder_path):
            backup_db_path = local_database_backups_folder_path / f"{db_path.stem}_backup_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}{db_path.suffix}"
            os.rename(db_path, backup_db_path)
            print(f"Backed up database at '{backup_db_path}'")
        os.remove(db_path) if os.path.exists(db_path) else None
        print(f"Deleted database at '{db_path}'")

    @staticmethod
    def encode_frame_for_url_body_b64_string(np_ndarray: np.ndarray = None):
        if np_ndarray is None or not isinstance(np_ndarray, np.ndarray):
            raise ValueError('Invalid np_ndarray provided')
        
        success, encoded_image = cv2.imencode('.jpg', np_ndarray)
        if not success:
            raise ValueError('Failed to encode image')
        base64_encoded_jpg_image_string = base64.b64encode(encoded_image.tobytes()).decode('utf-8')

        return base64_encoded_jpg_image_string
    
    @staticmethod
    def decode_url_body_b64_string_to_frame(base64_encoded_image_string: str = None):
        if base64_encoded_image_string is None or not isinstance(base64_encoded_image_string, str):
            raise ValueError('Invalid base64_encoded_jpg_image_string provided')
        
        return cv2.imdecode(np.frombuffer(base64.b64decode(base64_encoded_image_string), dtype=np.uint8), cv2.IMREAD_COLOR)
    
    @staticmethod
    def encode_frame_to_b64encoded_jpg_bytes(np_ndarray: np.ndarray = None):
        if np_ndarray is None or not isinstance(np_ndarray, np.ndarray):
            raise ValueError('Invalid np_ndarray provided')
        
        success, encoded_image = cv2.imencode('.jpg', np_ndarray)
        if not success:
            raise ValueError('Failed to encode image')
        base_64_encoded_jpg_image_bytes = base64.b64encode(encoded_image.tobytes())

        return base_64_encoded_jpg_image_bytes # <class 'bytes'>
    
    @staticmethod
    def encode_frame_to_jpg(np_ndarray: np.ndarray = None):
        if np_ndarray is None or not isinstance(np_ndarray, np.ndarray):
            raise ValueError('Invalid np_ndarray provided')
        
        success, encoded_image = cv2.imencode('.jpg', np_ndarray)
        if not success:
            raise ValueError('Failed to encode image')
        return encoded_image

    @staticmethod
    def decode_b64encoded_jpg_bytes_to_np_ndarray(base_64_encoded_jpg_image_bytes: bytes = None):
        if base_64_encoded_jpg_image_bytes is None or not isinstance(base_64_encoded_jpg_image_bytes, bytes):
            raise ValueError('Invalid base_64_encoded_jpg_image_bytes provided')
        
        return cv2.imdecode(np.frombuffer(base64.b64decode(base_64_encoded_jpg_image_bytes), dtype=np.uint8), cv2.IMREAD_COLOR)
    
    # ================================iot_device_and_rule_relations==============================
    def __ensure_iot_device_and_rule_relations_table_exists(self):
        # =======================================iot_device_and_rule_relations===================================================
        # A table to store the iot devices and their rules
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # relation_uuid         :(str) is a unique identifier for the relation
        # device_uuid           :(str) is a unique identifier for the device        
        # rule_uuid             :(str) is a unique identifier for the rule
        # which_action          :(str) is the action code for the rule (8bit unsigned int)
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS iot_device_and_rule_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            relation_uuid TEXT NOT NULL,
            device_uuid TEXT NOT NULL,
            rule_uuid TEXT NOT NULL,
            which_action TEXT NOT NULL 
        )
        '''
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_iot_device_and_rule_relations
            AFTER UPDATE ON iot_device_and_rule_relations
            FOR EACH ROW
            BEGIN
                UPDATE iot_device_and_rule_relations 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''

        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()
        if self.VERBOSE: print(f"Ensured 'iot_device_and_rule_relations' table exists")
    
    def add_iot_device_and_rule_relation(self, device_uuid:str=None, rule_uuid:str=None, which_action:str = None)-> dict:
        # Ensure device_uuid is proper
        if device_uuid is None or not isinstance(device_uuid, str) or len(device_uuid) == 0:
            raise ValueError('Invalid device_uuid provided')
        
        # Ensure rule_uuid is proper
        if rule_uuid is None or not isinstance(rule_uuid, str) or len(rule_uuid) == 0:
            raise ValueError('Invalid rule_uuid provided')
        
        # Ensure which_action is proper        
        if not 0<=int(which_action)<=255:
            raise ValueError('Invalid which_action provided')
        
        # Ensure the device exists
        query = '''
        SELECT device_uuid, device_name, device_id FROM iot_devices WHERE device_uuid = ?
        '''
        cursor = self.conn.execute(query, (device_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Device not found')
        
        # Ensure the rule exists
        query = '''
        SELECT * FROM rules_info_table WHERE rule_uuid = ?
        '''
        cursor = self.conn.execute(query, (rule_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Rule not found')
               

        # Insert the device-rule relation to the table
        relation_uuid = str(uuid.uuid4())
        query = '''
        INSERT INTO iot_device_and_rule_relations (relation_uuid, device_uuid, rule_uuid, which_action)
        VALUES (?, ?, ?, ? )
        '''
        self.conn.execute(query, (relation_uuid, device_uuid, rule_uuid, str(int(which_action))))
        self.conn.commit()
        return {    
            "relation_uuid": relation_uuid,
            "device_uuid": device_uuid,
            "rule_uuid": rule_uuid,
            "which_action": str(int(which_action))
        }
    
    def fetch_all_iot_device_and_rule_relations(self)-> dict:
        query = '''
        SELECT relation_uuid, device_uuid, rule_uuid, which_action FROM iot_device_and_rule_relations
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return {'all_iot_device_and_rule_relations': []}
        
        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        
        return {'all_iot_device_and_rule_relations':result}
    
    def remove_iot_device_and_rule_relation_by_relation_uuid(self, relation_uuid:str=None)-> dict:
        #check if the relation_uuid is valid
        if relation_uuid is None or not isinstance(relation_uuid, str) or len(relation_uuid) == 0:
            raise ValueError('Invalid relation_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(relation_uuid):
            raise ValueError('Invalid relation_uuid provided')
        
        #check if the relation exists
        query = '''
        SELECT relation_uuid, device_uuid, rule_uuid, which_action FROM iot_device_and_rule_relations WHERE relation_uuid = ?
        '''
        cursor = self.conn.execute(query, (relation_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Relation not found')
        
        relation_row = dict(zip([description[0] for description in cursor.description], row))

        #delete the relation from the table
        query = '''
        DELETE FROM iot_device_and_rule_relations WHERE relation_uuid = ?
        '''
        self.conn.execute(query, (relation_uuid,))
        self.conn.commit()
        return relation_row
    
    # ======================================= iot_device ========================================
    def __ensure_iot_devices_table_exists(self):
        # =======================================iot_devices===================================================
        # A table to store the iot devices
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # device_uuid           :(str) is a unique identifier for the device
        # device_name           :(str) is the name of the device
        # device_id             :(str) is the id of the device, used to send data to the device, do not need to be unique (16 bit unsigned integer)
        # ========================================================================================================
        query ='''
        CREATE TABLE IF NOT EXISTS iot_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            device_uuid TEXT NOT NULL,
            device_name TEXT NOT NULL,
            device_id TEXT NOT NULL
        )
        '''
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_iot_devices
            AFTER UPDATE ON iot_devices
            FOR EACH ROW
            BEGIN
                UPDATE iot_devices 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
        '''        

        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()

        if self.VERBOSE: print(f"Ensured 'iot_devices' table exists")
    
    def create_iot_device(self, device_name:str=None, device_id:str=None)->dict:
        # Ensure device_name is proper
        if device_name is None or not isinstance(device_name, str) or len(device_name) == 0:
            raise ValueError('Invalid device_name provided')
        
        # Ensure device_id is proper
        if device_id is None or not isinstance(device_id, str) or len(device_id) == 0:
            raise ValueError('Invalid device_id provided')
        
        # Ensure device_id is integer castable and 16 bit unsigned integer
        try:
            uint16_t = int(device_id)
            if not 0<=uint16_t<=65535:
                raise ValueError('Invalid device_id provided')
        except:
            raise ValueError('Invalid device_id provided')
        
        # Generate a unique device_uuid
        device_uuid = str(uuid.uuid4())
        
        # Insert the device to the table
        query = '''
        INSERT INTO iot_devices (device_uuid, device_name, device_id)
        VALUES (?, ?, ?)
        '''
        self.conn.execute(query, (device_uuid, device_name, device_id))
        self.conn.commit()
        return {
            "device_uuid": device_uuid,
            "device_name": device_name,
            "device_id": str(int(device_id))
        }
    
    def update_device_by_device_uuid(self, device_uuid:str=None, device_name:str=None, device_id:str=None)-> dict:
        # Ensure device_uuid is proper
        if device_uuid is None or not isinstance(device_uuid, str) or len(device_uuid) == 0:
            raise ValueError('Invalid device_uuid provided')
        
        # Ensure device_name is proper
        if device_name is None or not isinstance(device_name, str) or len(device_name) == 0:
            raise ValueError('Invalid device_name provided')
        
        # Ensure device_id is proper
        if device_id is None or not isinstance(device_id, str) or len(device_id) == 0:
            raise ValueError('Invalid device_id provided')
        
        # Ensure device_id is integer castable and 16 bit unsigned integer
        try:
            uint16_t = int(device_id)
            if not 0<=uint16_t<=65535:
                raise ValueError('Invalid device_id provided')
        except:
            raise ValueError('Invalid device_id provided')
        
        # Ensure the device exists
        query = '''
        SELECT device_uuid, device_name, device_id FROM iot_devices WHERE device_uuid = ?
        '''
        cursor = self.conn.execute(query, (device_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Device not found')
        
        # Update the device in the table
        query = '''
        UPDATE iot_devices SET device_name = ?, device_id = ? WHERE device_uuid = ?
        '''
        self.conn.execute(query, (device_name, device_id, device_uuid))
        self.conn.commit()
        return {
            "device_uuid": device_uuid,
            "device_name": device_name,
            "device_id": str(int(device_id))
        }
    
    def delete_iot_device_by_device_uuid(self, device_uuid:str=None)-> dict:
        #check if the device_uuid is valid
        if device_uuid is None or not isinstance(device_uuid, str) or len(device_uuid) == 0:
            raise ValueError('Invalid device_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(device_uuid):
            raise ValueError('Invalid device_uuid provided')
        
        #check if the device exists
        query = '''
        SELECT device_uuid, device_name, device_id FROM iot_devices WHERE device_uuid = ?
        '''
        cursor = self.conn.execute(query, (device_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Device not found')
        
        device_row = dict(zip([description[0] for description in cursor.description], row))

        #delete the device from the table
        query = '''
        DELETE FROM iot_devices WHERE device_uuid = ?
        '''
        self.conn.execute(query, (device_uuid,))
        self.conn.commit()
        return device_row
    
    def fetch_all_iot_devices(self)-> dict:
        query = '''
        SELECT device_uuid, device_name, device_id FROM iot_devices
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return {'all_iot_devices': []}
        
        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        
        return {'all_iot_devices':result}
    
    # ======================================= reported_violations ========================================
    def __ensure_reported_violations_table_exists(self):
        # ========================================reported_violations==================================================
        # A table to store the reported violations
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # violation_date        :(TIMESTAMP) is the date and time the violation was detected
        # violation_uuid        :(str) is a unique identifier for the violation
        # region_name           :(str) is the name of the region where the violation was detected
        # violation_type        :(str) is the type of violation. It can be 'hardhat_violation', 'restricted_area_violation' etc.
        # violation_score       :(float) is the score of the violation. It can be between 0 and 1
        # camera_uuid           :(str) is a unique identifier for the camera
        # image_uuid            :(str) is a unique identifier for the image
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
        if self.VERBOSE: print(f"Ensured 'reported_violations' table exists")

    def __delete_timeouted_violations(self):
        #Deletes both the violations and violation corresponding images that are older than PREFERENCES.VIOLATIONS_TIME_TO_LIVE_DAYS
        current_time = time.time()
        if current_time - self.last_time_old_violations_cleaned_up < PREFERENCES.VIOLATIONS_CLEANUP_CHECK_INTERVAL_SECONDS:
            return # The time to clean up the old violations and images has not come yet
    
        #Delete the violations and images that are older than PREFERENCES.VIOLATIONS_AND_IMAGES_TIME_TO_LIVE_DAYS
        self.last_time_old_violations_cleaned_up = current_time
        
        print(f"[INFO] Cleaning up the old violations and images that are older than {PREFERENCES.VIOLATIONS_TIME_TO_LIVE_DAYS:.3f} days")
      
        current_date = datetime.datetime.now(datetime.timezone.utc) # Server uses UTC time
        threshold_date = current_date - datetime.timedelta(days=PREFERENCES.VIOLATIONS_TIME_TO_LIVE_DAYS)
        
        query = '''
        SELECT violation_uuid FROM reported_violations WHERE date_created < ?
        '''
        cursor = self.conn.execute(query, (threshold_date,))
        rows = cursor.fetchall()
        print(f"[INFO] Found {len(rows)} violations to delete due to timeout")
        for row in rows:
            violation_uuid = row[0]
            try:
                self.delete_reported_violation_by_violation_uuid(violation_uuid)
                print(f"\t[SUBINFO] Deleted violation with violation_uuid {violation_uuid}")
            except Exception as e:
                print(f"\t[SUBINFO] Error deleting violation with violation_uuid {violation_uuid}: {e}")

    def create_reported_violation(self, camera_uuid:str=None, violation_frame:np.ndarray=None, violation_date:datetime.datetime=None, violation_type:str=None, violation_score:float=None, region_name:str=None)->dict:
        self.__delete_timeouted_violations() # Triggered once in a while to delete the violations and images that are older than PREFERENCES.VIOLATIONS_TIME_TO_LIVE_DAYS

        # Save the violation frame as a base64 encoded string and insert the path to the table
        violation_uuid = str(uuid.uuid4())
        image_uuid = str(uuid.uuid4())

        self.save_encrypted_image_and_insert_path_to_table(image=violation_frame, image_category='violation_frame', image_uuid=image_uuid)
        # succesful save of the violation frame, since no exception was raised

        # Insert the violation to the table
        query = '''
        INSERT INTO reported_violations (violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid))
        self.conn.commit()
        return {
            "violation_uuid": violation_uuid,
            "violation_date": violation_date,
            "region_name": region_name,
            "violation_type": violation_type,
            "violation_score": violation_score,
            "camera_uuid": camera_uuid,
            "image_uuid": image_uuid
        }
    
    def fetch_reported_violations_between_dates(self, start_date: datetime.datetime = None, end_date: datetime.datetime = None, query_limit: int = 9999) -> dict:
        if start_date > end_date:
            raise ValueError('Start date cannot be recent than end date')

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
            return {'fetched_violations': []}
        
        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        
        return {'fetched_violations':result}
    
    def fetch_reported_violation_by_violation_uuid(self, violation_uuid:str=None)-> dict:
        query = '''
        SELECT violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid FROM reported_violations WHERE violation_uuid = ?
        '''
        cursor = self.conn.execute(query, (violation_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('No violation found with the provided violation_uuid')

        column_names = [description[0] for description in cursor.description]
        return dict(zip(column_names, row))
    
    def delete_reported_violation_by_violation_uuid(self, violation_uuid:str=None)-> dict:
        #check if the violation_uuid is valid
        if violation_uuid is None or not isinstance(violation_uuid, str) or len(violation_uuid) == 0:
            raise ValueError('Invalid violation_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(violation_uuid):
            raise ValueError('Invalid violation_uuid provided')
        
        #check if the violation exists
        query = '''
        SELECT violation_uuid, violation_date, region_name, violation_type, violation_score, camera_uuid, image_uuid FROM reported_violations WHERE violation_uuid = ?
        '''
        cursor = self.conn.execute(query, (violation_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Violation not found')
        
        violation_report_row = dict(zip([description[0] for description in cursor.description], row))

        #delete the violation image if it exists
        try:
            self.delete_image_path_and_encrypted_image_by_image_uuid(violation_report_row['image_uuid'])
        except Exception as e:
            pass

        #delete the violation from the table
        query = '''
        DELETE FROM reported_violations WHERE violation_uuid = ?
        '''
        self.conn.execute(query, (violation_uuid,))
        self.conn.commit()
        return violation_report_row
    
    # ========================================= image_paths ==============================================
    def __ensure_image_paths_table_exists(self):
        # =======================================image_paths====================================================
        # A table to store image encrpytion keys and encrypted images paths
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # image_uuid            :(str) is a unique identifier for the image
        # random_key        :(str) is the key used to encrypt the image
        # encrypted_image_path  :(str) is the path to the encrypted image
        # image_category        :(str) is a string to categorize the image. It can be anything like 'hard_hat_dataset', 'violation', etc.
        # ========================================================================================================       

        query = '''
        CREATE TABLE IF NOT EXISTS image_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_uuid TEXT NOT NULL,
            random_key TEXT NOT NULL,
            encrypted_image_path TEXT NOT NULL,
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
        if self.VERBOSE: print(f"Ensured 'image_paths' table exists")

    def __sync_encrypted_images_and_image_paths_table(self):
        # Delete the iamge paths with no corresponding encrypted image
        query = '''
        SELECT image_uuid, encrypted_image_path FROM image_paths
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            image_uuid, encrypted_image_path = row
            if not os.path.exists(Path(encrypted_image_path)):
                query = '''
                DELETE FROM image_paths WHERE image_uuid = ?
                '''
                self.conn.execute(query, (image_uuid,))
                print(f"Deleted image_path row with no corresponding encrypted image: {image_uuid}")
        self.conn.commit()


        # Delete the encrypted images that are not in the table
        all_existing_file_paths_inside_encrypted_images_folder = []
        encrypted_images_key = 'api_server_encrypted_images' # The key for the encrypted images folder hardcoded in the PREFERENCES

        if PREFERENCES.check_if_folder_accesible(folder_path=PREFERENCES.DATA_FOLDER_PATH_EXTERNAL):
            external_encrypted_images_path = PREFERENCES.DATA_FOLDER_PATH_EXTERNAL / PREFERENCES.MUST_EXISTING_DATA_SUBFOLDER_PATHS[encrypted_images_key]
            all_existing_file_paths_inside_encrypted_images_folder.extend(external_encrypted_images_path.rglob('*.bin') 
        )
        if PREFERENCES.check_if_folder_accesible(folder_path=PREFERENCES.DATA_FOLDER_PATH_LOCAL):
            local_encrypted_images_path = PREFERENCES.DATA_FOLDER_PATH_LOCAL / PREFERENCES.MUST_EXISTING_DATA_SUBFOLDER_PATHS[encrypted_images_key]
            all_existing_file_paths_inside_encrypted_images_folder.extend(local_encrypted_images_path.rglob('*.bin')
        )

        # Iterate over all collected file paths        
        for file_path in all_existing_file_paths_inside_encrypted_images_folder:
            str_file_path = str(Path(file_path).resolve())
            query = '''
            SELECT image_uuid FROM image_paths WHERE encrypted_image_path = ?
            '''

            cursor = self.conn.execute(query, (str_file_path,))  # Ensure the path is a string if required by the DB
            row = cursor.fetchone()

            if row is None:
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
        
    def save_encrypted_image_and_insert_path_to_table(self, image:np.ndarray = None, image_category:str = "no-category", image_uuid:str=None) -> dict:
        # Ensure image is proper
        if image is None or not isinstance(image, np.ndarray):
            raise ValueError('No image was provided or the image is not a NumPy array')
        
        # Ensure image_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(image_uuid):
            raise ValueError('Invalid image_uuid provided')
        
        # Ensure image is encoded properly as a JPEG image. It takes less space than PNG with minimal data loss
        encoded_jpg_image = SQLManager.encode_frame_to_jpg(np_ndarray = image)
        
        #decide on whether to save the image to the local or external folder
        is_external_folder_accesible = PREFERENCES.check_if_folder_accesible(folder_path = self.DATA_FOLDER_PATH_EXTERNAL)
        data_directory = self.DATA_FOLDER_PATH_EXTERNAL if is_external_folder_accesible else self.DATA_FOLDER_PATH_LOCAL
        images_directory = data_directory / PREFERENCES.MUST_EXISTING_DATA_SUBFOLDER_PATHS['api_server_encrypted_images']
        image_folder_name = f'date_{datetime.datetime.now().strftime("%Y-%m-%d")}'
        save_folder = images_directory / image_folder_name

        # Ensure the save folder exists
        if not os.path.exists(save_folder):
            os.makedirs(save_folder, exist_ok=True)

        # Ensure UUID is unique
        # NOTE: This is not checked. First encountered UUID is used. This is not a good practice but simpler. It is responsibility of the caller to ensure UUID is unique.

        # Save the encrypted image as a file to the save_folder   
        random_key = os.urandom(32)
        composite_key = hashlib.sha256(random_key + PREFERENCES.SQL_MANAGER_SECRET_KEY).digest()     
        iv = os.urandom(16)

        # Create a Cipher object using the key and IV
        cipher = Cipher(algorithms.AES(composite_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(encoded_jpg_image.tobytes()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()        
        iv_plus_encrypted_data =  iv + encrypted_data # Append the IV. 

        # Save the encrypted image as a file
        encrypted_image_path = save_folder / f'{image_uuid}.bin'
        with open(encrypted_image_path, 'wb') as file:
            file.write(iv_plus_encrypted_data)       
        
        # Since image is saved, insert the image path to the table
        query = '''
        INSERT INTO image_paths (image_uuid, random_key, encrypted_image_path, image_category)
        VALUES (?, ?, ?, ?)
        '''
        self.conn.execute(query, (image_uuid, random_key, str(encrypted_image_path.resolve()),  image_category))
        self.conn.commit() # Success
        return {
            "image_uuid": image_uuid,
            "encrypted_image_path": str(encrypted_image_path.resolve()),
            "image_category": image_category
        }

    def get_encrypted_image_by_image_uuid(self, image_uuid: str) -> dict:

        # Retrieve the encrypted image path and random key from the database, also check if the path with the provided image_uuid exists
        query = '''
        SELECT image_uuid, random_key, encrypted_image_path, image_category FROM image_paths WHERE image_uuid = ?
        '''
        cursor = self.conn.execute(query, (image_uuid,))
        row = cursor.fetchone()
        if row is None: 
            raise ValueError('No image path entry found with the provided image_uuid')
        
        # Unpack the row data
        retrieved_image_uuid, random_key, encrypted_image_path, image_category = row
       
        # Ensure the folder containing the encrypted image file is accessible
        encrypted_image_folder = Path(encrypted_image_path).parent
        if not PREFERENCES.check_if_folder_accesible(folder_path = encrypted_image_folder):
            raise ValueError('The folder containing the encrypted image file is not accessible')
        
        # Ensure the encrypted image file exists, if not, mark the image as deleted in the database and delete the row        
        if not os.path.exists(encrypted_image_path):          
            query = '''
            DELETE FROM image_paths WHERE image_uuid = ?
            '''
            self.conn.execute(query, (retrieved_image_uuid,))
            self.conn.commit()            
            raise ValueError('Encrypted image file not found with the provided image_uuid, will be marked as deleted in the database')
        
        # It is checked that the file exists, so read the encrypted data
        with open(encrypted_image_path, 'rb') as file:
            encrypted_data = file.read()            

        # Re-create the composite key using the random key and the device-specific secret key
        composite_key = hashlib.sha256(random_key + PREFERENCES.SQL_MANAGER_SECRET_KEY).digest()

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
            raise ValueError('Failed to decode the image from the encrypted data')

        # Return both the image and the row data as a dictionary
        return {
            "image_uuid": retrieved_image_uuid,
            "encrypted_image_path": encrypted_image_path,
            "image_category": image_category,
            "frame": image
        }

    def delete_image_path_and_encrypted_image_by_image_uuid(self, image_uuid: str) -> dict:
        # Retrieve the encrypted image path and random key from the database, also check if the path with the provided image_uuid exists
        query = '''
        SELECT image_uuid, random_key, encrypted_image_path, image_category FROM image_paths WHERE image_uuid = ?
        '''
        cursor = self.conn.execute(query, (image_uuid,))
        row = cursor.fetchone()
        if row is None: 
            raise ValueError('No image path entry found with the provided image_uuid')
        
        # Unpack the row data
        retrieved_image_uuid, random_key, encrypted_image_path, image_category = row
       
        # Ensure the folder containing the encrypted image file is accessible
        encrypted_image_folder = Path(encrypted_image_path).parent
        if not PREFERENCES.check_if_folder_accesible(folder_path = encrypted_image_folder):
            raise ValueError('The folder containing the encrypted image file is not accessible')
        
        # Ensure the encrypted image file exists, if not, mark the image as deleted in the database and delete the row
        if os.path.exists(encrypted_image_path):              
            os.remove(encrypted_image_path)

        # Delete the row from the table
        query = '''
        DELETE FROM image_paths WHERE image_uuid = ?
        '''
        self.conn.execute(query, (retrieved_image_uuid,))
        self.conn.commit()

        return {
            "image_uuid": retrieved_image_uuid,
            "encrypted_image_path": encrypted_image_path,
            "image_category": image_category
        }    
   
    # ========================================= camera_last_frames ==============================================

    def __ensure_camera_last_frames_table_exists(self):
        # ========================================================================================================
        # A table to store the last frames of the video streams
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # camera_uuid           :(str) is a unique identifier for the camera
        # camera_ip_address     :(str) is the IP address of the camera
        # camera_region         :(str) is the region of the camera
        # is_violation_detected :(int) is a flag to indicate if a violation was detected in the last frame. 0 means no violation detected, 1 means violation detected
        # is_person_detected    :(int) is a flag to indicate if a person was detected in the last frame. 0 means no person detected, 1 means person detected
        # last_frame_b64_bytes        :(BLOB) is the last frame of the video stream in base64 encoded format
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS camera_last_frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            camera_uuid TEXT NOT NULL,
            camera_ip_address TEXT NOT NULL,
            camera_region TEXT NOT NULL,
            is_violation_detected INTEGER DEFAULT 0,
            is_person_detected INTEGER DEFAULT 0,
            last_frame_b64_bytes BLOB NOT NULL
        )
        '''        
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_camera_last_frames
            AFTER UPDATE ON camera_last_frames
            FOR EACH ROW
            BEGIN
                UPDATE camera_last_frames 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''
        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()
        if self.VERBOSE: print(f"Ensured 'camera_last_frames' table exists")

    def update_last_camera_frame_as_by_camera_uuid(self, camera_uuid:str= None, is_violation_detected:bool=None, is_person_detected:bool=None, last_frame:np.ndarray=None)-> bool:
        # Ensure image is proper
        if last_frame is None or not isinstance(last_frame, np.ndarray):
            raise ValueError('No image was provided or the image is not a NumPy array')
        
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        camera_info = self.fetch_camera_info_by_uuid(camera_uuid= camera_uuid)['camera_info']
        if camera_info is None:
            raise ValueError('No camera found with the provided camera_uuid')
        
        base_64_encoded_jpg_image_bytes = SQLManager.encode_frame_to_b64encoded_jpg_bytes(np_ndarray = last_frame)

        # Save the last frame of the camera to the database as BLOB    
        query = '''
        SELECT id FROM camera_last_frames WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        row = cursor.fetchone()        
        if row is None: # No last frame found with the provided camera_uuid
            query = '''
            INSERT INTO camera_last_frames (camera_uuid, camera_ip_address, camera_region, is_violation_detected, is_person_detected, last_frame_b64_bytes)
            VALUES (?, ?, ?, ?, ?, ?)
            '''
            self.conn.execute(query, (camera_uuid, camera_info["camera_ip_address"], camera_info["camera_region"], int(is_violation_detected), int(is_person_detected), sqlite3.Binary(base_64_encoded_jpg_image_bytes))
            )
        else:
            query = '''
            UPDATE camera_last_frames SET is_violation_detected = ?, is_person_detected = ?, camera_ip_address = ?, last_frame_b64_bytes = ? WHERE camera_uuid = ?
            '''
            self.conn.execute(query, (int(is_violation_detected), int(is_person_detected), camera_info['camera_ip_address'], sqlite3.Binary(base_64_encoded_jpg_image_bytes), camera_uuid))
        
        self.conn.commit()
        return {
            "camera_uuid": camera_uuid,
            "camera_ip": camera_info["camera_ip_address"],
            "camera_region": camera_info["camera_region"],
            "is_violation_detected": is_violation_detected,
            "is_person_detected": is_person_detected,            
        }

    def get_last_camera_frame_by_camera_uuid(self, camera_uuid:str = None)-> np.ndarray:

        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        # Retrieve the last frame of the camera from the database
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip_address, camera_region, is_violation_detected, is_person_detected, last_frame_b64_bytes FROM camera_last_frames WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        row = cursor.fetchone()

        # No image found with the provided camera_uuid
        if row is None: 
            raise ValueError('No image found with the provided camera_uuid')
        
        # Unpack the row data
        date_created, date_updated, retrieved_camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected, base_64_encoded_jpg_image_bytes = row
       
        # keep the image as a base64 encoded string
        return {
            "date_created": date_created, #
            "date_updated": date_updated,
            "camera_uuid": retrieved_camera_uuid,
            "camera_ip_address": camera_ip,
            "camera_region": camera_region,
            "is_violation_detected": is_violation_detected,
            "is_person_detected": is_person_detected,
            "last_frame_np_array": SQLManager.decode_b64encoded_jpg_bytes_to_np_ndarray(base_64_encoded_jpg_image_bytes=base_64_encoded_jpg_image_bytes)
        }
        
    def get_all_last_camera_frame_info_without_frames(self) -> list:
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected FROM camera_last_frames
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()

        # Get column names from cursor description
        column_names = [description[0] for description in cursor.description]
        
        # Convert each row to a dictionary
        result = [dict(zip(column_names, row)) for row in rows]
        
        return result
              
    # ========================================= rules_info_table ==============================================
    def __ensure_rules_info_table_exists(self):
        # =======================================rules_info_table===================================================
        # A table to store the rules for the cameras
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # last_time_triggered   :(TIMESTAMP) is the date and time the rule was last triggered
        # camera_uuid           :(str) is a unique identifier for the camera
        # rule_uuid             :(str) is a unique identifier for the rule
        # rule_department       :(str) for example HSE, QUALITY, SECURITY etc.
        # rule_type             :(str) for example hardhat_violation, restricted_area_violation etc.
        # evaluation_method     :(str) There can be multiple methods to evaluate the same rule. This indicates the method to be used
        # threshold_value       :(str,  [0, 1]) is the threshold value to report a violation to local server
        # fol_threshold_value   :(str,  [0, 1]) is the threshold value to report a violation to the fol server
        # rule_polygon_str      :(str) is the polygon to indicate the area rule is applied. "x0n,y0n,x1n,y1n,x2n,y2n,...,xmn,ymn"
        # ========================================================================================================
        
        query = '''
        CREATE TABLE IF NOT EXISTS rules_info_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_time_triggered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            camera_uuid TEXT NOT NULL,
            rule_uuid TEXT NOT NULL,
            rule_department TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            evaluation_method TEXT NOT NULL,
            threshold_value TEXT NOT NULL,
            fol_threshold_value TEXT NOT NULL,
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
        if self.VERBOSE: print(f"Ensured 'rules_info_table' table exists")

    def create_rule(self, camera_uuid:str=None, rule_department:str=None, rule_type:str=None, evaluation_method:str=None, threshold_value:str=None, fol_threshold_value:str=None, rule_polygon:str=None)->dict:
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
        if threshold_value is None or not isinstance(threshold_value, str) or len(threshold_value) == 0:
            raise ValueError('Invalid threshold_value provided')
        
        if  float(threshold_value) < 0 or float(threshold_value) > 1:
            raise ValueError('Invalid threshold_value provided')
        
        # Ensure fol_threshold_value is proper
        if fol_threshold_value is None or not isinstance(fol_threshold_value, str) or len(fol_threshold_value) == 0:
            raise ValueError('Invalid fol_threshold_value provided')
        
        if  float(fol_threshold_value) < 0 or float(fol_threshold_value) > 1:
            raise ValueError('Invalid fol_threshold_value provided')
                
        # Ensure rule_polygon is proper
        # x0n,y0n,x1n,y1n,x2n,y2n,...,xmn,ymn
        rule_polygon_list = rule_polygon.split(',')
        if len(rule_polygon_list) % 2 != 0 or len(rule_polygon_list) < 6:
            raise ValueError('Invalid rule_polygon provided')
        for i in range(0, len(rule_polygon_list), 2):
            float(rule_polygon_list[i]), float(rule_polygon_list[i+1]) # Check if they are floatable
            if float(rule_polygon_list[i]) < 0 or float(rule_polygon_list[i]) > 1 or float(rule_polygon_list[i+1]) < 0 or float(rule_polygon_list[i+1]) > 1:
                raise ValueError('Invalid rule_polygon provided, should be normalized')
                  
        # Generate a UUID for the rule
        rule_uuid = str(uuid.uuid4())
        query = '''
        INSERT INTO rules_info_table (last_time_triggered, camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value,fol_threshold_value, rule_polygon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, ('1970-01-01 00:00:00', camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value, fol_threshold_value, rule_polygon))
        self.conn.commit()

        return {
            "last_time_triggered": '1970-01-01 00:00:00',
            "camera_uuid": camera_uuid,
            "rule_uuid": rule_uuid,
            "rule_department": rule_department,
            "rule_type": rule_type,
            "evaluation_method": evaluation_method,
            "threshold_value": threshold_value,
            "fol_threshold_value": fol_threshold_value,
            "rule_polygon": rule_polygon
        }
    
    def trigger_rule_by_rule_uuid(self, rule_uuid:str=None)-> dict:
        #check if the rule_uuid is valid
        if rule_uuid is None or not isinstance(rule_uuid, str) or len(rule_uuid) == 0:
            raise ValueError('Invalid rule_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(rule_uuid):
            raise ValueError('Invalid rule_uuid provided')
        
        #check if the rule exists
        query = '''
        SELECT id FROM rules_info_table WHERE rule_uuid = ?
        '''
        cursor = self.conn.execute(query, (rule_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Rule not found')
        
        trigger_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #update the last_time_triggered field
        query = '''
        UPDATE rules_info_table SET last_time_triggered = ? WHERE rule_uuid = ?
        '''
        self.conn.execute(query, (trigger_time, rule_uuid,))
        self.conn.commit()

        return {
            "rule_uuid": rule_uuid,
            "trigger_time": trigger_time
        }
    
    def delete_rule_by_rule_uuid(self, rule_uuid:str=None)-> dict:
        #check if the rule_uuid is valid
        if rule_uuid is None or not isinstance(rule_uuid, str) or len(rule_uuid) == 0:
            raise ValueError('Invalid rule_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(rule_uuid):
            raise ValueError('Invalid rule_uuid provided')
        
        #check if the rule exists
        query = '''
        SELECT id FROM rules_info_table WHERE rule_uuid = ?
        '''
        cursor = self.conn.execute(query, (rule_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Rule not found')

        #delete the rule
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
        if camera_uuid is None or not isinstance(camera_uuid, str) or len(camera_uuid) == 0:
            raise ValueError('Invalid camera_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        query = '''
        SELECT date_created, date_updated, last_time_triggered, camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value, fol_threshold_value, rule_polygon FROM rules_info_table WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        rows = cursor.fetchall()
        if rows is None:
            return {'camera_rules':[]}

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return {'camera_rules':result}
    
    def fetch_all_rules(self)-> list:
        query = '''
        SELECT date_created, date_updated, last_time_triggered, camera_uuid, rule_uuid, rule_department, rule_type, evaluation_method, threshold_value, fol_threshold_value, rule_polygon FROM rules_info_table
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        if rows is None:
            return None

        column_names = [description[0] for description in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return {'all_rules':result}
    
    # ========================================= counts_table ==============================================
    def __ensure_counts_table_exists(self):
        # ======================================== counts_table ====================================================
        # A table to store the integer counts of anything useful. It can be people, violations, processed images etc.
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # count_key             :(str) - how count will be fetched. Can be any arbitrary string but if used for camera, using (camera_uuid_key) is recommended
        # count_subkey          :(str) is the type of count. It can be 'people' or 'violations' etc.
        # total_count           :(str) is the total count of the type of count (considered as float during calculations)
        # ========================================================================================================
        query = '''
        CREATE TABLE IF NOT EXISTS counts_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            count_key TEXT NOT NULL,
            count_subkey TEXT NOT NULL,
            total_count TEXT NOT NULL
        )
        '''

        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_counts_table
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
        if self.VERBOSE: print(f"Ensured 'counts_table' table exists")

    def update_count(self, count_key:str = None, count_subkey:str = None, delta_count:float = None)-> dict:               
        # Ensure delta_count is proper
        if not isinstance(delta_count, int) and not isinstance(delta_count, float):
            raise ValueError('Invalid delta_count provided')
        
        # If count_key is not provided, raise an error
        if count_key is None or not isinstance(count_key, str) or len(count_key) == 0:
            raise ValueError('Invalid count_key provided')
        
        # If count_subkey is not provided, raise an error
        if count_subkey is None or not isinstance(count_subkey, str) or len(count_subkey) == 0:
            raise ValueError('Invalid count_subkey provided')
        
        # Check if the count_key and count_subkey combination exists, else create it by setting the total_count to 0
        query = '''
        SELECT total_count FROM counts_table WHERE count_key = ? AND count_subkey = ?
        '''
        cursor = self.conn.execute(query, (count_key, count_subkey))
        row = cursor.fetchone()
        previous_value = None       
        if row is not None:
            previous_value = float(row[0])
            query = '''
            UPDATE counts_table SET total_count = ? WHERE count_key = ? AND count_subkey = ?
            '''
            self.conn.execute(query, (str(previous_value + delta_count), count_key, count_subkey))

        else:
            previous_value = 0
            query = '''
            INSERT INTO counts_table (count_key, count_subkey, total_count)
            VALUES (?, ?, ?)
            '''
            self.conn.execute(query, (count_key, count_subkey, str(delta_count)))

        self.conn.commit()
        return {
            'count_key': count_key, 
            'count_subkey': count_subkey,
            'previous_count': previous_value,
            'delta_count': delta_count,
            'total_count': previous_value + delta_count
        }
            
    def get_counts_by_count_key(self, count_key:str = None)-> dict:
        # Ensure count_key is proper
        if count_key is None or not isinstance(count_key, str) or len(count_key) == 0:
            raise ValueError('Invalid count_key provided')
        
        query = '''
        SELECT count_subkey, total_count FROM counts_table WHERE count_key = ?
        '''
        cursor = self.conn.execute(query, (count_key,))
        rows = cursor.fetchall()
        return {'counts': 
                [{row[0]: float(row[1])} for row in rows]
        }
    
    def get_total_count_by_count_key_and_count_subkey(self, count_key:str = None, count_subkey:str = None)-> dict:
        # Ensure count_key is proper
        if count_key is None or not isinstance(count_key, str) or len(count_key) == 0:
            raise ValueError('Invalid count_key provided')
        
        # Ensure count_subkey is proper
        if count_subkey is None or not isinstance(count_subkey, str) or len(count_subkey) == 0:
            raise ValueError('Invalid count_subkey provided')
        
        query = '''
        SELECT total_count FROM counts_table WHERE count_key = ? AND count_subkey = ?
        '''
        cursor = self.conn.execute(query, (count_key, count_subkey))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Could not found')
        
        return {'total_count': float(row[0])}
    
    def fetch_all_counts(self)-> dict:
        query = '''
        SELECT count_key, count_subkey, total_count FROM counts_table
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        return {'all_counts': 
                [{row[0]: {row[1]: float(row[2])}} for row in rows]
        }

    # ========================================= user_info =================================================
    def __ensure_user_info_table_exists(self):
        # =========================================user_info=====================================================
        # A table to store user information
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key (autoincremented)
        # date_created          :(TIMESTAMP) is the date and time the record was created (default is the current date and time)
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated (default is the current date and time)
        # user_uuid             :(str) is a unique identifier for the user (str(uuid.uuid4()))
        # username              :(str) is the username of the user (unique and str)
        # personal_fullname     :(str) is the full name of the user 
        # hashed_password       :(str) is the hashed password of the user
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
        if self.VERBOSE: print(f"Ensured 'user_info' table exists")
    
    def __create_safety_ai_user(self):
        # Ensure the SAFETY_AI_USER_INFO is properly set
        if not isinstance(PREFERENCES.SAFETY_AI_USER_INFO, dict) or len(PREFERENCES.SAFETY_AI_USER_INFO) == 0:
            raise ValueError('Invalid SAFETY_AI_USER_INFO provided')
        
        # Ensure the SAFETY_AI_USER_INFO contains the required keys
        required_keys = ['username', 'password', 'personal_fullname']
        for key in required_keys:
            if key not in PREFERENCES.SAFETY_AI_USER_INFO:
                raise ValueError(f"SAFETY_AI_USER_INFO missing key: '{key}'")
        
        # Ensure the SAFETY_AI_USER_INFO values are proper
        if not isinstance(PREFERENCES.SAFETY_AI_USER_INFO['username'], str) or len(PREFERENCES.SAFETY_AI_USER_INFO['username']) == 0:
            raise ValueError('Invalid username provided in SAFETY_AI_USER_INFO')
        
        if not isinstance(PREFERENCES.SAFETY_AI_USER_INFO['password'], str) or len(PREFERENCES.SAFETY_AI_USER_INFO['password']) == 0:
            raise ValueError('Invalid password provided in SAFETY_AI_USER_INFO')
        
        if not isinstance(PREFERENCES.SAFETY_AI_USER_INFO['personal_fullname'], str) or len(PREFERENCES.SAFETY_AI_USER_INFO['personal_fullname']) == 0:
            raise ValueError('Invalid personal_fullname provided in SAFETY_AI_USER_INFO')
        
        # Ensure the SAFETY_AI_USER_INFO is not already created
        query = '''
        SELECT id FROM user_info WHERE username = ?
        '''
        cursor = self.conn.execute(query, (PREFERENCES.SAFETY_AI_USER_INFO['username'],))
        row = cursor.fetchone()
        if row is not None:
            return # Safety AI user already exists
        
        safety_ai_user_info = self.create_user(username=PREFERENCES.SAFETY_AI_USER_INFO['username'], personal_fullname=PREFERENCES.SAFETY_AI_USER_INFO['personal_fullname'], plain_password=PREFERENCES.SAFETY_AI_USER_INFO['password'])
        if(self.VERBOSE): print(f"Safety AI user created successfully")

        # add the admin user all the permissions
        for authorization in PREFERENCES.DEFINED_AUTHORIZATIONS:
            self.add_authorization(user_uuid = safety_ai_user_info['user_uuid'], authorization_name = authorization)

    def __create_admin_user(self):
        # Ensure the ADMIN_USER_INFO is properly set
        if not isinstance(PREFERENCES.ADMIN_USER_INFO, dict) or len(PREFERENCES.ADMIN_USER_INFO) == 0:
            raise ValueError('Invalid ADMIN_USER_INFO provided')
        
        # Ensure the ADMIN_USER_INFO contains the required keys
        required_keys = ['username', 'password', 'personal_fullname']
        for key in required_keys:
            if key not in PREFERENCES.ADMIN_USER_INFO:
                raise ValueError(f"ADMIN_USER_INFO missing key: '{key}'")
        
        # Ensure the ADMIN_USER_INFO values are proper
        if not isinstance(PREFERENCES.ADMIN_USER_INFO['username'], str) or len(PREFERENCES.ADMIN_USER_INFO['username']) == 0:
            raise ValueError('Invalid username provided in ADMIN_USER_INFO')
        
        if not isinstance(PREFERENCES.ADMIN_USER_INFO['password'], str) or len(PREFERENCES.ADMIN_USER_INFO['password']) == 0:
            raise ValueError('Invalid password provided in ADMIN_USER_INFO')
        
        if not isinstance(PREFERENCES.ADMIN_USER_INFO['personal_fullname'], str) or len(PREFERENCES.ADMIN_USER_INFO['personal_fullname']) == 0:
            raise ValueError('Invalid personal_fullname provided in ADMIN_USER_INFO')
        
        # Ensure the ADMIN_USER_INFO is not already created
        query = '''
        SELECT id FROM user_info WHERE username = ?
        '''
        cursor = self.conn.execute(query, (PREFERENCES.ADMIN_USER_INFO['username'],))
        row = cursor.fetchone()
        if row is not None:
            return # Admin user already exists
        
        admin_user_info = self.create_user(username=PREFERENCES.ADMIN_USER_INFO['username'], personal_fullname=PREFERENCES.ADMIN_USER_INFO['personal_fullname'], plain_password=PREFERENCES.ADMIN_USER_INFO['password'])
        if(self.VERBOSE): print(f"Admin user created successfully")

        # add the admin user all the permissions
        for authorization in PREFERENCES.DEFINED_AUTHORIZATIONS:
            self.add_authorization(user_uuid = admin_user_info['user_uuid'], authorization_name = authorization)

    def create_user(self, username:str=None, personal_fullname:str=None, plain_password:str=None)-> dict:
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
            "hashed_password": hashed_password        
        }
    
    def get_user_by_username(self, username:str=None)-> dict:
        # Ensure username is proper
        if not isinstance(username, str) or len(username) == 0:
            raise ValueError('Invalid username provided')
        
        query = '''
        SELECT user_uuid, username, personal_fullname, hashed_password
        FROM user_info
        WHERE username = ?
        '''
        cursor = self.conn.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('User not found')
        
        return {
            "user_uuid": row[0],
            "username": row[1],
            "personal_fullname": row[2],
            "hashed_password": row[3]
        }
    
    def get_user_by_user_uuid(self, user_uuid:str=None)-> dict:
        # Ensure user_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not isinstance(user_uuid, str) or len(user_uuid) == 0 or not regex.match(user_uuid):
            raise ValueError('Invalid user_uuid provided')
        
        query = '''
        SELECT user_uuid, username, personal_fullname, hashed_password
        FROM user_info
        WHERE user_uuid = ?
        '''
        cursor = self.conn.execute(query, (user_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('User not found')
        
        return {
            "user_uuid": row[0],
            "username": row[1],
            "personal_fullname": row[2],
            "hashed_password": row[3]
        }

    def is_authenticated_user(self, username:str=None, plain_password:str=None)->dict:
        if not isinstance(username, str) or len(username) == 0:
            raise ValueError('Invalid username provided')
        
        if not isinstance(plain_password, str) or len(plain_password) == 0:
            raise ValueError('Invalid password provided')
        
        hashed_password_candidate = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        try:
            user_dict = self.get_user_by_username(username=username)          
            if user_dict["hashed_password"] == hashed_password_candidate:
                return {'is_authenticated' : True}
            else:
                return {'is_authenticated' : False}
        except Exception as e:
            return {'is_authenticated' : False}
    
    def delete_user_by_username(self, username:str=None)->dict:
        #HARDCODED: Safety AI user and Admin user cannot be deleted
        if username == PREFERENCES.SAFETY_AI_USER_INFO['username'] or username == PREFERENCES.ADMIN_USER_INFO['username']:
            raise ValueError('Safety AI user and Admin user cannot be deleted')

        # Ensure username is proper
        if not isinstance(username, str) or len(username) == 0:
            raise ValueError('Invalid username provided')
                
        # Check if the user exists
        query = '''
        SELECT id FROM user_info WHERE username = ?
        '''
        cursor = self.conn.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('User not found')
        
        # Delete the user
        query = '''
        DELETE FROM user_info WHERE username = ?
        '''
        self.conn.execute(query, (username,))
        self.conn.commit()
        return {'is_deleted' : True}
    
    def delete_user_by_user_uuid(self, user_uuid:str=None)->dict:        
        #HARDCODED: Safety AI user and Admin user cannot be deleted
        safety_ai_user_info = self.get_user_by_username(username=PREFERENCES.SAFETY_AI_USER_INFO['username'])
        admin_user_info = self.get_user_by_username(username=PREFERENCES.ADMIN_USER_INFO['username'])

        if user_uuid == safety_ai_user_info['user_uuid'] or user_uuid == admin_user_info['user_uuid']:
            raise ValueError('Safety AI user and Admin user cannot be deleted')
        
        # Ensure user_uuid is proper
        if not isinstance(user_uuid, str) or len(user_uuid) == 0:
            raise ValueError('Invalid user_uuid provided')
        
        # Check if the user exists
        query = '''
        SELECT id FROM user_info WHERE user_uuid = ?
        '''
        cursor = self.conn.execute(query, (user_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('User not found')
        
        # Delete the user
        query = '''
        DELETE FROM user_info WHERE user_uuid = ?
        '''
        self.conn.execute(query, (user_uuid,))
        self.conn.commit()
        return {'is_deleted' : True}
    
    def get_all_users(self)->dict:
        query = '''
        SELECT user_uuid, username, personal_fullname, hashed_password
        FROM user_info
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        return {'users': [{
            "user_uuid": row[0],
            "username": row[1],
            "personal_fullname": row[2],
            "hashed_password": row[3]
        } for row in rows]
        }
    
    # ========================================= authorization_table ========================================
    def __ensure_authorization_table_exists(self):
        # ===========================================authorization_table==========================================
        # A table to store the authorizations of the users. One user can be linked to multiple authorizations
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # user_uuid             :(str) is a unique identifier for the user
        # authorization_uuid    :(str) is a unique identifier for the authorization
        # authorization_name    :(str) is the name of the authorization
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
        if self.VERBOSE: print(f"Ensured 'authorization_table' table exists")
    
    def add_authorization(self, user_uuid:str=None, authorization_name:str=None)-> dict:
        # Ensure user_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not isinstance(user_uuid, str) or len(user_uuid) == 0 or not regex.match(user_uuid):
            raise ValueError('Invalid user_uuid provided')
        
        # Ensure authorization_name is proper
        if not isinstance(authorization_name, str) or authorization_name not in PREFERENCES.DEFINED_AUTHORIZATIONS:
            raise ValueError('Invalid authorization_name provided')
        
        # Ensure the user exists
        query = '''
        SELECT id FROM user_info WHERE user_uuid = ?
        '''
        cursor = self.conn.execute(query, (user_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('User not found')
        
        # Ensure the authorization does not already exist
        query = '''
        SELECT id FROM authorization_table WHERE user_uuid = ? AND authorization_name = ?
        '''
        cursor = self.conn.execute(query, (user_uuid, authorization_name))
        row = cursor.fetchone()
        if row is not None:
            raise ValueError('Authorization already exists')
        
        # Generate a UUID for the authorization
        authorization_uuid = str(uuid.uuid4())
        
        query = '''
        INSERT INTO authorization_table (user_uuid, authorization_uuid, authorization_name)
        VALUES (?, ?, ?)
        '''
        self.conn.execute(query, (user_uuid, authorization_uuid, authorization_name))
        self.conn.commit()
        
        return {
            "user_uuid": user_uuid,
            "authorization_uuid": authorization_uuid,
            "authorization_name": authorization_name
        }

    def remove_authorization(self, authorization_uuid:str = None)->dict:
        # Ensure authorization_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not isinstance(authorization_uuid, str) or len(authorization_uuid) == 0 or not regex.match(authorization_uuid):
            raise ValueError('Invalid authorization_uuid provided')
        
        # Check if the authorization exists and it is not 'ADMIN_PRIVILEGES'
        query = '''
        SELECT id, authorization_name FROM authorization_table WHERE authorization_uuid = ?
        '''
        cursor = self.conn.execute(query, (authorization_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Authorization not found')
        if row[1] == 'ADMIN_PRIVILEGES':
            raise ValueError('ADMIN_PRIVILEGES cannot be removed')
        

        # Delete the authorization
        query = '''
        DELETE FROM authorization_table WHERE authorization_uuid = ?
        '''
        self.conn.execute(query, (authorization_uuid,))
        self.conn.commit()
        return {'is_authorization_removed': True}

    def get_user_authorizations_by_user_uuid(self, user_uuid:str=None)->dict:
        # Ensure user_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not isinstance(user_uuid, str) or len(user_uuid) == 0 or not regex.match(user_uuid):
            raise ValueError('Invalid user_uuid provided')
        
        # Ensure user exists
        query = '''
        SELECT id FROM user_info WHERE user_uuid = ?
        '''
        cursor = self.conn.execute(query, (user_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('User not found')
        
        # Get the authorizations
        query = '''
        SELECT authorization_uuid, authorization_name
        FROM authorization_table
        WHERE user_uuid = ?
        '''
        cursor = self.conn.execute(query, (user_uuid,))
        rows = cursor.fetchall()
        return {'user_authorizations':[{
            "authorization_uuid": row[0],
            "authorization_name": row[1]
        } for row in rows]
        }
    
    def get_user_authorizations_by_username(self, username:str=None)->dict:
        # Ensure username is proper
        if not isinstance(username, str) or len(username) == 0:
            raise ValueError('Invalid username provided')
        
        # Ensure user exists
        query = '''
        SELECT id FROM user_info WHERE username = ?
        '''
        cursor = self.conn.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('User not found')
        
        # Get the authorizations
        query = '''
        SELECT authorization_uuid, authorization_name
        FROM authorization_table
        WHERE user_uuid = (SELECT user_uuid FROM user_info WHERE username = ?)
        '''
        cursor = self.conn.execute(query, (username,))
        rows = cursor.fetchall()
        return {'user_authorizations':[{
            "authorization_uuid": row[0],
            "authorization_name": row[1]
        } for row in rows]
        }
    
    # ========================================= camera_info_table ========================================
    
    def __ensure_camera_info_table_exists(self):
        # ========================================camera_info_table================================================
        # A table to store the information of the cameras
        # ====================================== TABLE STRUCTURE =================================================
        # id                    :(int) is the primary key
        # date_created          :(TIMESTAMP) is the date and time the record was created
        # date_updated          :(TIMESTAMP) is the date and time the record was last updated
        # camera_uuid           :(str) is a unique identifier for the camera
        # camera_ip_address     :(str) is the IP address of the camera
        # camera_region         :(str) is the region of the camera
        # camera_description    :(str) is the description of the camera
        # username              :(str) is the username to access the camera
        # password              :(str) is the password to access the camera
        # stream_path           :(str) is the path to the video stream
        # camera_status         :(str) is the status of the camera. Defined at PREFERENCES.DEFINED_CAMERA_STATUSES (probably 'active' or 'inactive' but should check)
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
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            stream_path TEXT NOT NULL,
            camera_status TEXT NOT NULL
        )
        '''
        trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS update_date_updated_camera_info_table
            AFTER UPDATE ON camera_info_table
            FOR EACH ROW
            BEGIN
                UPDATE camera_info_table 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
        '''
        
        self.conn.execute(query)
        self.conn.execute(trigger_query)
        self.conn.commit()
        if self.VERBOSE: print(f"Ensured 'camera_info_table' table exists")

    def create_camera_info(self, camera_ip_address:str=None, camera_region:str=None, camera_description:str=None, username:str=None, password:str=None, stream_path:str=None, camera_status:str=None)-> dict:
        camera_uuid = str(uuid.uuid4())
        camera_description = "" if camera_description == None else camera_description
        camera_region = "" if camera_region == None else camera_region

        # Check if the camera_ip_address is provided
        if camera_ip_address is None or not isinstance(camera_ip_address, str) or len(camera_ip_address) == 0:
            raise ValueError('Invalid camera_ip_address provided')
        
        # Check if camera_stream_path is provided
        if stream_path is None or not isinstance(stream_path, str) or len(stream_path) == 0:
            raise ValueError('Invalid stream_path provided')
        
        # Check IP is valid or not
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', camera_ip_address):
            raise ValueError('Invalid IP address provided')
                
        # Check if the camera_status is valid or not
        if camera_status not in PREFERENCES.DEFINED_CAMERA_STATUSES:
            raise ValueError(f"Invalid camera_status provided. Valid values are {PREFERENCES.DEFINED_CAMERA_STATUSES}")
        
        # Check if username and password are provided
        if username is None or password is None:
            raise ValueError('Username and password are required')
                
        # Format the camera_description and camera_region
        if camera_description is not None and not isinstance(camera_description, str):
            raise ValueError('Invalid camera_description provided')
        
        if camera_region is not None and not isinstance(camera_region, str):
            raise ValueError('Invalid camera_region provided')

        # Check if the camera_ip_address is unique or not
        query = '''
        SELECT id FROM camera_info_table WHERE camera_ip_address = ?
        '''
        cursor = self.conn.execute(query, (camera_ip_address,))
        row = cursor.fetchone()
        if row is not None:
            raise ValueError('camera_ip_address already exists')
        
        # Create camera       
        query = '''
        INSERT INTO camera_info_table (camera_uuid, camera_ip_address, camera_region, camera_description, username, password, stream_path, camera_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''    
        self.conn.execute(query, (camera_uuid, camera_ip_address, camera_region, camera_description, username, password, stream_path, camera_status))       
        self.conn.commit()

        return {
            "camera_uuid": camera_uuid,
            "camera_ip_address": camera_ip_address,
            "camera_region": camera_region,
            "camera_description": camera_description,
            "username": username,
            "password": password,
            "stream_path": stream_path,
            "camera_status": camera_status
        }

    def update_camera_info_attribute(self, camera_uuid:str=None, attribute_name:str=None, attribute_value:str=None)-> dict:
        # Check if the camera_uuid is valid or not
        if camera_uuid is None or not isinstance(camera_uuid, str) or len(camera_uuid) == 0:
            raise ValueError('Invalid camera_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        # Check if the attribute is provided
        if attribute_name is None or not isinstance(attribute_name, str): 
            raise ValueError('Invalid attribute provided')
        
        # Check if the attribute is valid or not
        if attribute_name not in ['camera_ip_address', 'camera_region', 'camera_description', 'username', 'password', 'stream_path', 'camera_status']:
            raise ValueError(f'Invalid attribute provided {attribute_name}')
        
        # Check whether camera_region attribute is properly formatted
        if not isinstance(attribute_value, str):
            raise ValueError('Attribute value must be a string')

        # Check if attribute is too long
        if len(attribute_value) > 256:
            raise ValueError('Attribute value is too long')
        
        if attribute_name == 'camera_ip_address':
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', attribute_value):
                raise ValueError('Invalid IP address provided')
            
            # Check if the camera_ip_address is unique or not
            query = '''
            SELECT id FROM camera_info_table WHERE camera_ip_address = ?
            '''
            cursor = self.conn.execute(query, (attribute_value,))
            row = cursor.fetchone()
            if row is not None:
                raise ValueError('camera_ip_address already exists')
        
        if attribute_name == 'camera_status' and attribute_value not in PREFERENCES.DEFINED_CAMERA_STATUSES:
            raise ValueError("Invalid camera_status provided. Valid values are 'active' or 'inactive'")
        
        query = f'''
        UPDATE camera_info_table 
        SET {attribute_name} = ?, date_updated = CURRENT_TIMESTAMP 
        WHERE camera_uuid = ?
        '''
        self.conn.execute(query, (attribute_value, camera_uuid))
        self.conn.commit()

        return {
            "camera_uuid": camera_uuid,
            attribute_name: attribute_value
        }

    def delete_camera_info_by_uuid(self, camera_uuid:str=None)-> dict:
        # Check if the camera_uuid is valid or not
        if camera_uuid is None or not isinstance(camera_uuid, str) or len(camera_uuid) == 0:
            raise ValueError('Invalid camera_uuid provided')
        
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
    
    def fetch_all_camera_info(self)-> dict:
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip_address, camera_region, camera_description, username, password, stream_path, camera_status FROM camera_info_table
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
                
        return {'all_camera_info':result}

    def fetch_camera_info_by_uuid(self, camera_uuid:str = None) -> dict:
        if camera_uuid is None or not isinstance(camera_uuid, str) or len(camera_uuid) == 0:
            raise ValueError('Invalid camera_uuid provided')
        
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip_address, camera_region, camera_description, username, password, stream_path, camera_status FROM camera_info_table WHERE camera_uuid = ?
        '''
        cursor = self.conn.execute(query, (camera_uuid,))
        row = cursor.fetchone()
        
        if row is None:
            raise ValueError('Camera not found')
        else:
            # Get column names from cursor description
            column_names = [description[0] for description in cursor.description]
            
            # Create a dictionary using the column names and row data
            return {'camera_info':dict(zip(column_names, row))}
    
    def fetch_camera_uuid_by_camera_ip_address(self, camera_ip_address:str=None)-> dict:
        if camera_ip_address is None or not isinstance(camera_ip_address, str) or len(camera_ip_address) == 0:
            raise ValueError('Invalid camera_ip_address provided')
        
        query = '''
        SELECT camera_uuid FROM camera_info_table WHERE camera_ip_address = ?
        '''
        cursor = self.conn.execute(query, (camera_ip_address,))
        row = cursor.fetchone()
        
        if row is None:
            raise ValueError('Camera not found')
        else:
            return {'camera_uuid': row[0]}
    