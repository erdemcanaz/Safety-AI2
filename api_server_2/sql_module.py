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

# (+ 1)     camera_info_table
# (+ 1.1)   last_frames table
# (+ 1.2)   reported_violations
# (+ 1.2.1) image_paths table
# (+ 1.3)   counts_table
# (+ 1.4)   rules_info_table
# (+ 1.5)   shift_counts_table
# (+++++++++++++++ 2)     user_info_table
# (+ 2.1)   authorizations_table

class SQLManager:
    DEVICE_SECRET_KEY = b"G4ECs6lRrm6HXbtBdMwFoLA18iqF1mMT" # Note that this is an UTF8 encoded byte string. Will be changed in the future, developers should not use this key in production

    def __init__(self, db_path=None, verbose=False, overwrite_existing_db=False): 
        self.DB_PATH = db_path
        self.VERBOSE = verbose     

        #check if the database exists and delete it if it does before creating a new one
        if overwrite_existing_db and os.path.exists(db_path):
            os.remove(db_path) if os.path.exists(db_path) else None

        #check if the path folder exists, if not, create it 
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        #NOTE: creates a new database if it doesn't exist
        self.conn = sqlite3.connect(self.DB_PATH) 

        #Ensure required tables exist
        self.ensure_user_info_table_exists()

        #Ensure the SAFETY_AI_USER_INFO is created, if not, create it
        self.__create_safety_ai_user() 
    def close(self):
        self.conn.close()

    # ========================================= user_info =================================================
    def ensure_user_info_table_exists(self):
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

    def create_user(self, username:str=None, personal_fullname:str=None, plain_password:str=None)-> bool:
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

    def is_authenticated_user(self, username:str=None, plain_password:str=None)->bool:
        if not isinstance(username, str) or len(username) == 0:
            raise ValueError('Invalid username provided')
        
        if not isinstance(plain_password, str) or len(plain_password) == 0:
            raise ValueError('Invalid password provided')
        
        hashed_password_candidate = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        try:
            user_dict = self.get_user_by_username(username=username)          
            if user_dict["hashed_password"] == hashed_password_candidate:
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def delete_user_by_username(self, username:str=None)->bool:
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
        return True
    
    def delete_user_by_user_uuid(self, user_uuid:str=None)->bool:
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
        return True
    
    def get_all_users(self)->list:
        query = '''
        SELECT user_uuid, username, personal_fullname, hashed_password
        FROM user_info
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        return [{
            "user_uuid": row[0],
            "username": row[1],
            "personal_fullname": row[2],
            "hashed_password": row[3]
        } for row in rows]

if __name__ == "__main__":
    print(f"{'='*100}\nTesting the SQLManager class for proper functionality\n{'='*100}")
    # Update the database path to the test database path
    PREFERENCES.SQL_DATABASE_PATH = str(Path(PREFERENCES.SQL_DATABASE_PATH).with_name('test_database.db'))
    print(f"Creating a test database at the '{PREFERENCES.SQL_DATABASE_PATH}' path")
    sql_manager = SQLManager(db_path=PREFERENCES.SQL_DATABASE_PATH, verbose = True, overwrite_existing_db=True)

    #================================= Testing 'user_info' table functionality =================================
    print(f"\nTesting 'user_info' table functionality {'='*50}")
    test_user_info = {
        "username": "test_user",
        "personal_fullname": "Dummy Dum",
        "plain_password": "test_password_123"
    }
    print(f"(1) Creating a user with \n\tusername:'{test_user_info['username']}'\n\tpersonal_fullname:'{test_user_info['personal_fullname']}'\n\tplain_password:'{test_user_info['plain_password']}'")
    user_dict_create_user = sql_manager.create_user(username=test_user_info['username'], personal_fullname=test_user_info['personal_fullname'], plain_password=test_user_info['plain_password'])
    print(f"User created:")
    pprint.pprint(user_dict_create_user)

    print(f"\n(2) Getting the user by username:'{user_dict_create_user['username']}'")
    user_dict_by_username = sql_manager.get_user_by_username(username=user_dict_create_user['username'])
    print(f"User retrieved by username:")
    pprint.pprint(user_dict_by_username)

    print(f"\n(3) Getting the user by wrong username:'non_existing_username'")
    try:
        user_dict_by_username = sql_manager.get_user_by_username(username='non_existing_username')
    except Exception as e:
        print(f"Error raised: {e}")

    print(f"\n(4) Getting the user by user_uuid:'{user_dict_create_user['user_uuid']}'")
    user_dict_by_uuid = sql_manager.get_user_by_user_uuid(user_uuid=user_dict_create_user['user_uuid'])
    print(f"User retrieved by UUID")
    pprint.pprint(user_dict_by_uuid)

    print(f"\n(5) Getting the user by wrong user_uuid:'non_existing_user_uuid'")
    try:
        user_dict_by_uuid = sql_manager.get_user_by_user_uuid(user_uuid='non_existing_user_uuid')
    except Exception as e:
        print(f"Error raised: {e}")

    print(f"\n(6- Correct) Authenticating the user with \n\tusername:'test_user'\n\tplain_password:'test_password_123'")
    is_authenticated = sql_manager.is_authenticated_user(username= test_user_info['username'], plain_password= test_user_info['plain_password'])
    print(f"\t Is user authenticated: {is_authenticated}")

    print(f"\n(6- Incorrect) Authenticating the user with \n\tusername:'test_user'\n\tplain_password:'wrong_password'")
    is_authenticated = sql_manager.is_authenticated_user(username='test_user', plain_password='wrong_password')
    print(f"\tIs user authenticated: {is_authenticated}")

    print(f"\n(6- Non-existing) Authenticating the user with \n\tusername:'non_existing_user'\n\tplain_password:'test_password_123'")
    is_authenticated = sql_manager.is_authenticated_user(username='non_existing_user', plain_password='test_password_123')
    print(f"\tIs user authenticated: {is_authenticated}")

    print(f"\n(7) Deleting the user by username:'{user_dict_create_user['username']}'")
    is_deleted = sql_manager.delete_user_by_username(username=user_dict_create_user['username'])
    print(f"\tIs user deleted: {is_deleted}")

    print(f"Fetching all users")
    all_users = sql_manager.get_all_users()
    pprint.pprint(all_users)

    print(f"\n(8) Deleting the user by user_uuid:")
    print(f"Creating a user with \n\tusername:'{test_user_info['username']}'\n\tpersonal_fullname:'{test_user_info['personal_fullname']}'\n\tplain_password:'{test_user_info['plain_password']}'")
    user_dict_create_user_2 = sql_manager.create_user(username=test_user_info['username'], personal_fullname=test_user_info['personal_fullname'], plain_password=test_user_info['plain_password'])
    pprint.pprint(user_dict_create_user_2)

    print(f"\n(9)Deleting the user by user_uuid:'{user_dict_create_user_2['user_uuid']}'")
    is_deleted = sql_manager.delete_user_by_user_uuid(user_uuid=user_dict_create_user_2['user_uuid'])
    print(f"\tIs user deleted: {is_deleted}")

    print(f"\n(10) Fetching all users")   
    all_users = sql_manager.get_all_users()
    pprint.pprint(all_users)



    sql_manager.close()
