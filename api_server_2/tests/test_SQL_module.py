import sqlite3, base64, numpy as np, cv2, pprint, uuid, datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os, re, hashlib, time, sys, pprint
from pathlib import Path

# To import below modules, paths must be appended to the sys.path
API_SERVER_DIRECTORY = Path(__file__).resolve().parent.parent
SAFETY_AI2_DIRECTORY = API_SERVER_DIRECTORY.parent
sys.path.append(str(API_SERVER_DIRECTORY))
sys.path.append(str(SAFETY_AI2_DIRECTORY))     
import PREFERENCES
from sql_module import SQLManager

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

#================================= Testing 'authorization_table' table functionality =================================
print(f"\nTesting 'authorization_table' table functionality {'='*50}")
print(f"creating a test user with \n\tusername:'{test_user_info['username']}'\n\tpersonal_fullname:'{test_user_info['personal_fullname']}'\n\tplain_password:'{test_user_info['plain_password']}'")
test_user_authorization = sql_manager.create_user(username=test_user_info['username'], personal_fullname=test_user_info['personal_fullname'], plain_password=test_user_info['plain_password'])

print(f"\n(1) Fetching {test_user_info['username']}'s authorizations")
user_authorizations = sql_manager.get_user_authorizations_by_username(username=test_user_info['username'])
pprint.pprint(user_authorizations)

print(f"\n(2) Adding an authorization to {test_user_info['username']}")
available_authorizations = PREFERENCES.DEFINED_AUTHORIZATIONS
print(f"Available authorizations: {available_authorizations}")
for authorization_name in available_authorizations:
    print(f"# Adding authorization: {authorization_name}")
    authorization_dict = sql_manager.add_authorization(user_uuid=test_user_authorization['user_uuid'], authorization_name=authorization_name)
    pprint.pprint(authorization_dict)

print(f"\n(3) Fetching {test_user_info['username']}'s authorizations by username")
user_authorizations = sql_manager.get_user_authorizations_by_username(username=test_user_info['username'])
pprint.pprint(user_authorizations)

print(f"\n(4) Fetching {test_user_info['username']}'s authorizations by user_uuid")
user_authorizations = sql_manager.get_user_authorizations_by_user_uuid(user_uuid=test_user_authorization['user_uuid'])
pprint.pprint(user_authorizations)

print(f"\n(5) Removing authorizations from {test_user_info['username']}")
for authorization in user_authorizations['user_authorizations']:
    print(f"# Removing authorization: {authorization['authorization_name']}")
    is_removed = sql_manager.remove_authorization(authorization_uuid=authorization['authorization_uuid'])
    print(f"\tIs removed: {is_removed}")

print(f"Fetching {test_user_info['username']}'s authorizations")
user_authorizations = sql_manager.get_user_authorizations_by_username(username=test_user_info['username'])
pprint.pprint(user_authorizations)

#================================= Testing 'camera_info_table' table functionality =================================
print(f"\nTesting 'camera_info_table' table functionality {'='*50}")
test_camera_info = {
    "camera_ip_address": "172.0.0.0",
    "camera_region": "test_region",
    "camera_description": "test_description",
    "username": 'camera_username',
    "password": 'camera_password',
    "stream_path": "/rtsp_stream",
    "camera_status": "active",
}

print(f"\n(1) Creating a camera with \n\tcamera_ip_address:'{test_camera_info['camera_ip_address']}'\n\tcamera_region:'{test_camera_info['camera_region']}'\n\tcamera_description:'{test_camera_info['camera_description']}'\n\tusername:'{test_camera_info['username']}'\n\tpassword:'{test_camera_info['password']}'\n\tstream_path:'{test_camera_info['stream_path']}'\n\tcamera_status:'{test_camera_info['camera_status']}'")
camera_dict_create_camera = sql_manager.create_camera_info(camera_ip_address=test_camera_info['camera_ip_address'], camera_region=test_camera_info['camera_region'], camera_description=test_camera_info['camera_description'], username=test_camera_info['username'], password=test_camera_info['password'], stream_path=test_camera_info['stream_path'], camera_status=test_camera_info['camera_status'])
pprint.pprint(camera_dict_create_camera)

print(f"\n(2) Creating second camera with same IP address")
try:
    camera_dict_create_camera_2 = sql_manager.create_camera_info(camera_ip_address=test_camera_info['camera_ip_address'], camera_region=test_camera_info['camera_region'], camera_description=test_camera_info['camera_description'], username=test_camera_info['username'], password=test_camera_info['password'], stream_path=test_camera_info['stream_path'], camera_status=test_camera_info['camera_status'])
except Exception as e:
    print(f"Error raised: {e}")


update_map = {
    "camera_ip_address": "172.0.0.1",
    "camera_region": "updated_region",
    "camera_description": "updated_description",
    "username": 'updated_username',
    "password": 'updated_password',
    "stream_path": "/updated_rtsp_stream",
    "camera_status": "inactive",
}
print(f"\n(3) This camera will be updated \n\tcamera_uuid:{camera_dict_create_camera['camera_uuid']}\n\tcamera_ip_address:'{test_camera_info['camera_ip_address']}'\n\tcamera_region:'{test_camera_info['camera_region']}'\n\tcamera_description:'{test_camera_info['camera_description']}'\n\tusername:'{test_camera_info['username']}'\n\tpassword:'{test_camera_info['password']}'\n\tstream_path:'{test_camera_info['stream_path']}'\n\tcamera_status:'{test_camera_info['camera_status']}'")
for key, value in update_map.items():
    print(f"Updating {key} to {value}")
    response = camera_dict_update_camera = sql_manager.update_camera_info_attribute(camera_uuid=camera_dict_create_camera['camera_uuid'], attribute_name=key, attribute_value=value)
    pprint.pprint(response)

print(f"\n(4) Fetching the camera by camera_uuid:'{camera_dict_create_camera['camera_uuid']}'")
camera_dict_by_uuid = sql_manager.fetch_camera_info_by_uuid(camera_uuid=camera_dict_create_camera['camera_uuid'])
pprint.pprint(camera_dict_by_uuid)

print(f"\n(5) fetching all cameras")
all_cameras = sql_manager.fetch_all_camera_info()
pprint.pprint(all_cameras)

print(f"\n(6) Deleting the camera by camera_uuid:'{camera_dict_create_camera['camera_uuid']}'")
is_deleted = sql_manager.delete_camera_info_by_uuid(camera_uuid=camera_dict_create_camera['camera_uuid'])
print(f"\tIs camera deleted: {is_deleted}")
print("Fetching all cameras")
all_cameras = sql_manager.fetch_all_camera_info()
pprint.pprint(all_cameras)

# TODO: print test results
# TODO: delete the test database
sql_manager.close()