import sqlite3, base64, numpy as np, cv2
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os, re, hashlib

class DatabaseManager:
    DEVICE_SECRET_KEY = b"G4ECs6lRrm6HXbtBdMwFoLA18iqF1mMT" # Note that this is an UTF8 encoded byte string. Will be changed in the future, developers should not use this key in production

    def __init__(self, db_name='safety_ai.db'):
        self.conn = sqlite3.connect(db_name) # creates a new database if it doesn't exist
        self.ensure_image_paths_table_exists()
        self.ensure_last_frames_table_exists()

    def ensure_image_paths_table_exists(self):
        # ========================================================================================================
        # A table to store image encrpytion keys and encrypted images paths
        # ====================================== TABLE STRUCTURE =================================================
        # id                    : is the primary key
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
            image_uuid TEXT NOT NULL,
            encryption_key TEXT NOT NULL,
            encrypted_image_path TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            image_category TEXT NOT NULL DEFAULT 'no-category'
        )
        '''

        self.conn.execute(query)
        self.conn.commit()

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
            CREATE TRIGGER IF NOT EXISTS update_date_updated
            AFTER UPDATE ON last_frames
            FOR EACH ROW
            BEGIN
                UPDATE last_frames 
                SET date_updated = CURRENT_TIMESTAMP 
                WHERE id = OLD.id;
            END;
            '''
        
        self.conn.execute(trigger_query)
        self.conn.execute(query)
        self.conn.commit()

    # IMAGE_PATHS TABLE FUNCTIONS
    def save_encrypted_image_and_insert_path_to_table(self, save_folder:str=None, image:np.ndarray = None, image_category:str = "no-category", image_uuid:str=None)-> bool:
        # NOTE: This function should be called in try-except block

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

    def get_encrypted_image_by_uuid(self, image_uuid: str) -> np.ndarray:
        # Retrieve the encrypted image path and random key from the database
        query = '''
        SELECT image_uuid, encryption_key, encrypted_image_path, is_deleted, image_category FROM image_paths WHERE image_uuid = ?
        '''
        cursor = self.conn.execute(query, (image_uuid,))
        row = cursor.fetchone()

        # No image found with the provided image_uuid
        if row is None: 
            return None
        
        # Unpack the row data
        retrieved_image_uuid, random_key, encrypted_image_path, is_deleted, image_category = row
        if is_deleted:
            return None
       
        # Ensure the encrypted image file exists, if not, mark the image as deleted in the database
        if not os.path.exists(encrypted_image_path):
            update_query = '''
            UPDATE image_paths SET is_deleted = 1 WHERE image_uuid = ?
            '''
            self.conn.execute(update_query, (image_uuid,))
            self.conn.commit()
            return None
        
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
            "image": image,
            "random_key": random_key,
            "encrypted_image_path": encrypted_image_path,
            "is_deleted": is_deleted,
            "image_category": image_category
        } 
    
    # LAST_FRAMES TABLE FUNCTIONS
    def update_last_camera_frame_as_b64string_by_camera_uuid(self, camera_uuid:str= None, camera_ip:str=None, is_violation_detected:bool=None, is_person_detected:bool=None, camera_region:str=None, last_frame:np.ndarray=None)-> bool:
        # Ensure image is proper
        if last_frame is None or not isinstance(last_frame, np.ndarray):
            raise ValueError('No image was provided or the image is not a NumPy array')
        
        # Ensure camera_uuid is proper
        regex = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        if not regex.match(camera_uuid):
            raise ValueError('Invalid camera_uuid provided')
        
        # Ensure image is encoded properly as a JPEG image. It takes less space than PNG with minimal data loss
        success, encoded_image = cv2.imencode('.jpg', last_frame)
        if not success:
            raise ValueError('Failed to encode image')    
        base64_encoded_image = base64.b64encode(encoded_image.tobytes()) 
    
        # Save the last frame as a file to the save_folder   
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
            self.conn.execute(query, (camera_uuid, camera_ip, camera_region, int(is_violation_detected), int(is_person_detected), sqlite3.Binary(base64_encoded_image))
            )
        else:
            query = '''
            UPDATE last_frames SET last_frame_b64 = ? WHERE camera_uuid = ?
            '''
            self.conn.execute(query, (sqlite3.Binary(base64_encoded_image), camera_uuid))
        self.conn.commit()

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

    def get_last_camera_frames_without_BLOB(self)-> list:      
        query = '''
        SELECT date_created, date_updated, camera_uuid, camera_ip, camera_region, is_violation_detected, is_person_detected FROM last_frames
        '''
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        return rows
              
    def close(self):
        self.conn.close()

