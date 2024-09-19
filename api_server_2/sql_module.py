import sqlite3, base64, numpy as np, cv2, pprint, uuid, datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os, re, hashlib, time, sys, pprint
from pathlib import Path

# To import PREFERENCES if the script is run as the main script
if __name__ == "__main__":
    SAFETY_AI2_DIRECTORY = Path(__file__).resolve().parent.parent
    sys.path.append(str(SAFETY_AI2_DIRECTORY))     
import PREFERENCES

# (-) Last time rule triggered table
# (+ 1.1)   last_frames table
# (+ 1.2)   reported_violations
# (+ 1.2.1) image_paths table
# (+ 1.4)   rules_info_table
# (+ 1.5)   shift_counts_table

# (+ 1.3)   counts_table
# (+ 1)     camera_info_table
# (2)     user_info_table
# (2.1)   authorizations_table

class SQLManager:
    DEVICE_SECRET_KEY = b"G4ECs6lRrm6HXbtBdMwFoLA18iqF1mMT" # Note that this is an UTF8 encoded byte string. Will be changed in the future, developers should not use this key in production

    def __init__(self, db_path=None, verbose=False, overwrite_existing_db=False): 
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

        #Ensure a user is registered for the safety AI | first user !
        self.__create_safety_ai_user() 
   
    def close(self):
        self.conn.close()

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
        
        self.create_user(username=PREFERENCES.SAFETY_AI_USER_INFO['username'], personal_fullname=PREFERENCES.SAFETY_AI_USER_INFO['personal_fullname'], plain_password=PREFERENCES.SAFETY_AI_USER_INFO['password'])
        if(self.VERBOSE): print(f"Safety AI user created successfully")

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
        
        # Check if the authorization exists
        query = '''
        SELECT id FROM authorization_table WHERE authorization_uuid = ?
        '''
        cursor = self.conn.execute(query, (authorization_uuid,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Authorization not found')
        
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
        camera_uuid = str(uuid.uuid4())
        camera_description = "" if camera_description == None else camera_description
        camera_region = "" if camera_region == None else camera_region

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
    