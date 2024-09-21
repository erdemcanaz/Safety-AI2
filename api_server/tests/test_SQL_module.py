import sqlite3, base64, numpy as np, cv2, pprint, uuid, datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os, re, hashlib, time, sys, pprint, random
from pathlib import Path

# To import below modules, paths must be appended to the sys.path
API_SERVER_DIRECTORY = Path(__file__).resolve().parent.parent
SAFETY_AI2_DIRECTORY = API_SERVER_DIRECTORY.parent
sys.path.append(str(API_SERVER_DIRECTORY))
sys.path.append(str(SAFETY_AI2_DIRECTORY))    
print(f"API_SERVER_DIRECTORY: {API_SERVER_DIRECTORY}")
print(f"SAFETY_AI2_DIRECTORY: {SAFETY_AI2_DIRECTORY}")
 
import PREFERENCES
from sql_module import SQLManager


WAIT_TIME_BETWEEN_TESTS = 0 #seconds, if 0 wait for user input
paths_to_delete_after_tests = []
print(f"{'='*100}\nTesting the SQLManager class for proper functionality\n{'='*100}")
# Update the database path to the test database path
sql_database_path_local = PREFERENCES.SQL_DATABASE_FOLDER_PATH_LOCAL / "test_database.db"
print(f"Creating a test database at the '{sql_database_path_local}' path")
sql_manager = SQLManager(db_path=sql_database_path_local, verbose = True, overwrite_existing_db=True)
paths_to_delete_after_tests.append(sql_database_path_local)
#================================= Testing 'user_info' table functionality =================================
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
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
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")

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
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
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

print(f"\n(2) Fetching the camera by camera_uuid by camera_ip_address:'{test_camera_info['camera_ip_address']}'")
camera_dict_by_ip_address = sql_manager.fetch_camera_uuid_by_camera_ip_address(camera_ip_address=test_camera_info['camera_ip_address'])
pprint.pprint(camera_dict_by_ip_address)

print(f"\n(3) Creating second camera with same IP address")
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
print(f"\n(4) This camera will be updated \n\tcamera_uuid:{camera_dict_create_camera['camera_uuid']}\n\tcamera_ip_address:'{test_camera_info['camera_ip_address']}'\n\tcamera_region:'{test_camera_info['camera_region']}'\n\tcamera_description:'{test_camera_info['camera_description']}'\n\tusername:'{test_camera_info['username']}'\n\tpassword:'{test_camera_info['password']}'\n\tstream_path:'{test_camera_info['stream_path']}'\n\tcamera_status:'{test_camera_info['camera_status']}'")
for key, value in update_map.items():
    print(f"Updating {key} to {value}")
    response = camera_dict_update_camera = sql_manager.update_camera_info_attribute(camera_uuid=camera_dict_create_camera['camera_uuid'], attribute_name=key, attribute_value=value)
    pprint.pprint(response)

print(f"\n(5) Fetching the camera by camera_uuid:'{camera_dict_create_camera['camera_uuid']}'")
camera_dict_by_uuid = sql_manager.fetch_camera_info_by_uuid(camera_uuid=camera_dict_create_camera['camera_uuid'])
pprint.pprint(camera_dict_by_uuid)

print(f"\n(6) fetching all cameras")
all_cameras = sql_manager.fetch_all_camera_info()
pprint.pprint(all_cameras)

print(f"\n(7) Deleting the camera by camera_uuid:'{camera_dict_create_camera['camera_uuid']}'")
is_deleted = sql_manager.delete_camera_info_by_uuid(camera_uuid=camera_dict_create_camera['camera_uuid'])
print(f"\tIs camera deleted: {is_deleted}")
print("Fetching all cameras")
all_cameras = sql_manager.fetch_all_camera_info()
pprint.pprint(all_cameras)
#================================Testing 'counts_table' table functionality======================================================
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
print(f"{'='*100}\nTesting 'counts_table' table functionality\n{'='*100}")

test_count_key = "test_count_key"
test_count_subkeys = ["test_subkey_1", "test_subkey_2", "test_subkey_3"]
print(f"\n(1) Creating counts with \n\tcount_key:'{test_count_key}'\n\tcount_subkeys:'{test_count_subkeys}'")
for subkey in test_count_subkeys:
    count_dict_create_count = sql_manager.update_count(count_key=test_count_key, count_subkey=subkey, delta_count=random.uniform(-100, 100))
    pprint.pprint(count_dict_create_count)

print(f"\n(2) Fetching the count by count_key:'{test_count_key}'")
count_dict_by_key = sql_manager.get_counts_by_count_key(count_key=test_count_key)
pprint.pprint(count_dict_by_key)

print(f"\n(3) Fetching subkey counts by count_key:'{test_count_key}'")
for subkey in test_count_subkeys:
    count_dict_by_subkey = sql_manager.get_total_count_by_count_key_and_count_subkey(count_key=test_count_key, count_subkey=subkey)
    print(f"Subkey: {subkey}")
    pprint.pprint(count_dict_by_subkey)

print(f"\n(4) Updating the subkey {test_count_subkeys[0]} with a new count")
count_dict_update_count = sql_manager.update_count(count_key=test_count_key, count_subkey=test_count_subkeys[0], delta_count=random.uniform(-100, 100))
pprint.pprint(count_dict_update_count)

print(f"\nAdding new count keys and subkeys")
new_count_key =  [f"new_key_{i}" for i in range(1, 5)]
new_count_subkeys = [f"new_subkey_{i}" for i in range(1, 3)]
print(f"\n(5) Creating counts with \n\tcount_key:'{new_count_key}'\n\tcount_subkeys:'{new_count_subkeys}'")
for key in new_count_key:
    for subkey in new_count_subkeys:
        count_dict_create_count = sql_manager.update_count(count_key=key, count_subkey=subkey, delta_count=random.uniform(-100, 100))
        pprint.pprint(count_dict_create_count)

print(f"\n(6) Fetching all counts")
all_counts = sql_manager.fetch_all_counts()
pprint.pprint(all_counts)

#================================Testing 'rules_info_table' table functionality======================================================
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
print(f"{'='*100}\nTesting 'rules_info_table' table functionality\n{'='*100}")
print("defined_departments:")
pprint.pprint(PREFERENCES.DEFINED_DEPARTMENTS)
print("defined_rules:")
pprint.pprint(PREFERENCES.DEFINED_RULES)

print(f"\nCreating a camera with \n\tcamera_ip_address:'{test_camera_info['camera_ip_address']}'\n\tcamera_region:'{test_camera_info['camera_region']}'\n\tcamera_description:'{test_camera_info['camera_description']}'\n\tusername:'{test_camera_info['username']}'\n\tpassword:'{test_camera_info['password']}'\n\tstream_path:'{test_camera_info['stream_path']}'\n\tcamera_status:'{test_camera_info['camera_status']}'")
rule_camera_1 = sql_manager.create_camera_info(camera_ip_address=test_camera_info['camera_ip_address'], camera_region=test_camera_info['camera_region'], camera_description=test_camera_info['camera_description'], username=test_camera_info['username'], password=test_camera_info['password'], stream_path=test_camera_info['stream_path'], camera_status=test_camera_info['camera_status'])
pprint.pprint(rule_camera_1)

choosen_type = random.choice(list(PREFERENCES.DEFINED_RULES.keys()))
test_rule = {
    "camera_uuid" : rule_camera_1['camera_uuid'],
    "rule_department": random.choice(PREFERENCES.DEFINED_DEPARTMENTS),
    "rule_type": choosen_type,
    "evaluation_method": random.choice(PREFERENCES.DEFINED_RULES[choosen_type]),
    "threshold_value": f"{random.uniform(0, 1):.3f}",
    "fol_threshold_value": f"{random.uniform(0, 1):.3f}",
    "rule_polygon": ','.join([f"{random.uniform(0, 1):.3f},{random.uniform(0, 1):.3f}" for _ in range(random.randint(3, 4))]),
}

print(f"\n(1) Creating a rule with \n\tcamera_uuid:'{test_rule['camera_uuid']}'\n\trule_department:'{test_rule['rule_department']}'\n\trule_type:'{test_rule['rule_type']}'\n\tevaluation_method:'{test_rule['evaluation_method']}'\n\tthreshold_value:'{test_rule['threshold_value']}'\n\tfol_threshold_value:'{test_rule['fol_threshold_value']},\n\trule_polygon:'{test_rule['rule_polygon']}'")
rule_dict_create_rule = sql_manager.create_rule(camera_uuid=test_rule['camera_uuid'], rule_department=test_rule['rule_department'], rule_type=test_rule['rule_type'], evaluation_method=test_rule['evaluation_method'], threshold_value=test_rule['threshold_value'], fol_threshold_value= test_rule['fol_threshold_value'], rule_polygon=test_rule['rule_polygon'])
pprint.pprint(rule_dict_create_rule)

print(f"\n(2) Fetching the rule by rule_uuid:'{rule_dict_create_rule['rule_uuid']}'")
rule_dict_by_uuid = sql_manager.fetch_rules_by_camera_uuid(camera_uuid=test_rule['camera_uuid'])
pprint.pprint(rule_dict_by_uuid)

print(f"\n(3) Deleting the rule by rule_uuid:'{rule_dict_create_rule['rule_uuid']}'")
is_deleted = sql_manager.delete_rule_by_rule_uuid(rule_uuid=rule_dict_create_rule['rule_uuid'])
print(f"\tIs rule deleted: {is_deleted}")

print(f"\nFetching all rules")
all_rules = sql_manager.fetch_all_rules()
pprint.pprint(all_rules)

print(f"\n(4) Fetching all rules where 2 cameras exists")
print("Creating a second camera")
rule_camera_2 = sql_manager.create_camera_info(camera_ip_address="1.1.1.2", camera_region=test_camera_info['camera_region'], camera_description=test_camera_info['camera_description'], username=test_camera_info['username'], password=test_camera_info['password'], stream_path=test_camera_info['stream_path'], camera_status=test_camera_info['camera_status'])
pprint.pprint(rule_camera_2)

print("\nAssigning random rules to camera 1 & 2")
for _ in range(random.randint(1, 5)):
    choosen_type = random.choice(list(PREFERENCES.DEFINED_RULES.keys()))
    test_rule = {
        "camera_uuid" : rule_camera_1['camera_uuid'],
        "rule_department": random.choice(PREFERENCES.DEFINED_DEPARTMENTS),
        "rule_type": choosen_type,
        "evaluation_method": random.choice(PREFERENCES.DEFINED_RULES[choosen_type]),
        "threshold_value": f"{random.uniform(0, 1):.3f}",
        "fol_threshold_value": f"{random.uniform(0, 1):.3f}",
        "rule_polygon": ','.join([f"{random.uniform(0, 1):.3f},{random.uniform(0, 1):.3f}" for _ in range(random.randint(3, 4))]),
    }
    print(f"Creating a rule for camera-1 with \n\tcamera_uuid:'{test_rule['camera_uuid']}'\n\trule_department:'{test_rule['rule_department']}'\n\trule_type:'{test_rule['rule_type']}'\n\tevaluation_method:'{test_rule['evaluation_method']}'\n\tthreshold_value:'{test_rule['threshold_value']}'\n\tfol_threshold_value:'{test_rule['fol_threshold_value']},\n\trule_polygon:'{test_rule['rule_polygon']}'")
    sql_manager.create_rule(camera_uuid=test_rule['camera_uuid'], rule_department=test_rule['rule_department'], rule_type=test_rule['rule_type'], evaluation_method=test_rule['evaluation_method'], threshold_value=test_rule['threshold_value'], fol_threshold_value= test_rule['fol_threshold_value'], rule_polygon=test_rule['rule_polygon'])

for _ in range(random.randint(1, 5)):
    choosen_type = random.choice(list(PREFERENCES.DEFINED_RULES.keys()))
    test_rule = {
        "camera_uuid" : rule_camera_2['camera_uuid'],
        "rule_department": random.choice(PREFERENCES.DEFINED_DEPARTMENTS),
        "rule_type": choosen_type,
        "evaluation_method": random.choice(PREFERENCES.DEFINED_RULES[choosen_type]),
        "threshold_value": f"{random.uniform(0, 1):.3f}",
        "fol_threshold_value": f"{random.uniform(0, 1):.3f}",
        "rule_polygon": ','.join([f"{random.uniform(0, 1):.3f},{random.uniform(0, 1):.3f}" for _ in range(random.randint(3, 4))]),
    }
    print(f"Creating a rule for camera-2 with \n\tcamera_uuid:'{test_rule['camera_uuid']}'\n\trule_department:'{test_rule['rule_department']}'\n\trule_type:'{test_rule['rule_type']}'\n\tevaluation_method:'{test_rule['evaluation_method']}'\n\tthreshold_value:'{test_rule['threshold_value']}'\n\tfol_threshold_value:'{test_rule['fol_threshold_value']},\n\trule_polygon:'{test_rule['rule_polygon']}'")
    sql_manager.create_rule(camera_uuid=test_rule['camera_uuid'], rule_department=test_rule['rule_department'], rule_type=test_rule['rule_type'], evaluation_method=test_rule['evaluation_method'], threshold_value=test_rule['threshold_value'], fol_threshold_value= test_rule['fol_threshold_value'], rule_polygon=test_rule['rule_polygon'])

all_rules = sql_manager.fetch_all_rules()
pprint.pprint(all_rules)

print(f"\n(5) Triggering the rule from all rules")
picked_rule = random.choice(all_rules['all_rules'])
print(f"Triggering the rule with rule_uuid:'{picked_rule['rule_uuid']}'")
print('Before triggering the rule:')
rule_dict_by_uuid = sql_manager.fetch_rules_by_camera_uuid(camera_uuid=picked_rule['camera_uuid'])
pprint.pprint(rule_dict_by_uuid)
triggered_rule = sql_manager.trigger_rule_by_rule_uuid(rule_uuid=picked_rule['rule_uuid'])
pprint.pprint(triggered_rule)
print('After triggering the rule:')
rule_dict_by_uuid = sql_manager.fetch_rules_by_camera_uuid(camera_uuid=picked_rule['camera_uuid'])
pprint.pprint(rule_dict_by_uuid)




# ================================= Testing 'camera_last_frames' table functionality =================================
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
print(f"{'='*100}\nTesting 'camera_last_frames' table functionality\n{'='*100}")

print(f"(1) Updateing camera last frame for camera-1")
camera_ip = str(random.randint(0,255))+"."+str(random.randint(0,255))+"."+str(random.randint(0,255))+"."+str(random.randint(0,255))
print(f"Creating a camera with \n\tcamera_ip_address:'{camera_ip}'\n\tcamera_region:'{test_camera_info['camera_region']}'\n\tcamera_description:'{test_camera_info['camera_description']}'\n\tusername:'{test_camera_info['username']}'\n\tpassword:'{test_camera_info['password']}'\n\tstream_path:'{test_camera_info['stream_path']}'\n\tcamera_status:'{test_camera_info['camera_status']}'")
camera_last_frame_camera = sql_manager.create_camera_info(camera_ip_address=camera_ip, camera_region=test_camera_info['camera_region'], camera_description=test_camera_info['camera_description'], username=test_camera_info['username'], password=test_camera_info['password'], stream_path=test_camera_info['stream_path'], camera_status=test_camera_info['camera_status'])
pprint.pprint(camera_dict_create_camera)

print(f"\nCreating a random RGB frame with 640x480 resolution")
random_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
print(f"Frame shape: {random_frame.shape}")
print(f"Frame dtype: {random_frame.dtype}")


print(f"\n(2) Updating the camera last frame for camera")
updated_last_frame = sql_manager.update_last_camera_frame_as_by_camera_uuid(camera_uuid=camera_last_frame_camera['camera_uuid'], last_frame=random_frame, is_violation_detected=random.choice([True, False]), is_person_detected= random.choice([True, False]))
pprint.pprint(updated_last_frame)

print(f"\n(3) Fetching the last frame for camera")
last_frame = sql_manager.get_last_camera_frame_by_camera_uuid(camera_uuid=camera_last_frame_camera['camera_uuid'])
keys_to_show = ['date_created', 'date_updated','camera_uuid', 'is_violation_detected', 'is_person_detected']
pprint.pprint({key: last_frame[key] for key in keys_to_show})

cv2.imshow("last_frame", last_frame['last_frame_np_array'])
cv2.waitKey(1000)
cv2.destroyAllWindows()

# ================================= Testing 'image_paths' table functionality =================================
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
print(f"{'='*100}\nTesting 'image_paths' table functionality\n{'='*100}")
print(f"(1) Saving the random frame as an encrypted image and recording the path in the database")
print(f"\nCreating a random RGB frame with 640x480 resolution")
random_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
test_image_info = {
    'image' : random_frame,
    'image_category' : random.choice(['violation', 'person']),
    'image_uuid' : str(uuid.uuid4())
}
post_result = sql_manager.save_encrypted_image_and_insert_path_to_table(**test_image_info)
paths_to_delete_after_tests.append(post_result['encrypted_image_path'])
pprint.pprint(post_result)

print(f"\n(2) Fetching the image path by image_uuid:'{test_image_info['image_uuid']}'")
get_result = sql_manager.get_encrypted_image_by_image_uuid(image_uuid=post_result['image_uuid'])
pprint.pprint(get_result)
cv2.imshow("image", get_result['image'])
cv2.waitKey(2500)

print(f"\n(3) Fetching non-existing image path by image_uuid:'non_existing_image_uuid'")
try:
    get_result = sql_manager.get_encrypted_image_by_image_uuid(image_uuid='non_existing_image_uuid')
except Exception as e:
    print(f"Error raised: {e}")

print(f"\n(4) Corrupting the SQL_MANAGER_SECRET_KEY and then fetching the image path by image_uuid:'{test_image_info['image_uuid']}'")
initial_key = PREFERENCES.SQL_MANAGER_SECRET_KEY
PREFERENCES.SQL_MANAGER_SECRET_KEY = b'G4ECs6lRrm6HXbtBdMwFoLA18iqaaaaa'
try:
    get_result = sql_manager.get_encrypted_image_by_image_uuid(image_uuid=post_result['image_uuid'])
    pprint.pprint(get_result)
    cv2.imshow("image", get_result['image'])
    cv2.waitKey(2500)
except Exception as e:
    print(f"Error raised: {e}")

print(f"Restoring the SQL_MANAGER_SECRET_KEY to the initial value")
PREFERENCES.SQL_MANAGER_SECRET_KEY = initial_key
# ================================= Testing 'reported_violations' table functionality =================================
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
print(f"{'='*100}\nTesting 'reported_violations' table functionality\n{'='*100}")
print(f"\n(1) Creating a violation report")   
   
print("Creating a random frame with 640x480 resolution")
random_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

camera_ip = str(random.randint(0,255))+"."+str(random.randint(0,255))+"."+str(random.randint(0,255))+"."+str(random.randint(0,255))
print(f"\nCreating a camera with \n\tcamera_ip_address:'{camera_ip}'\n\tcamera_region:'{test_camera_info['camera_region']}'\n\tcamera_description:'{test_camera_info['camera_description']}'\n\tusername:'{test_camera_info['username']}'\n\tpassword:'{test_camera_info['password']}'\n\tstream_path:'{test_camera_info['stream_path']}'\n\tcamera_status:'{test_camera_info['camera_status']}'")
reported_violation_camera = sql_manager.create_camera_info(camera_ip_address=camera_ip, camera_region=test_camera_info['camera_region'], camera_description=test_camera_info['camera_description'], username=test_camera_info['username'], password=test_camera_info['password'], stream_path=test_camera_info['stream_path'], camera_status=test_camera_info['camera_status'])
pprint.pprint(reported_violation_camera)

reported_violation_info = {
    "camera_uuid": reported_violation_camera['camera_uuid'],
    "violation_frame": random_frame,
    "violation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "violation_type": "test_violation_type",
    "violation_score": random.uniform(0, 1),
    "region_name": "test_region",
}
created_reported_violation = sql_manager.create_reported_violation(**reported_violation_info)
pprint.pprint(created_reported_violation)

print(f"\n(2 - no match) Fetching the reported violation by start_date = '2021-01-01 00:00:00' and end_date = '2022-01-01 00:00:00'")
start_date = datetime.datetime.strptime('2021-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
end_date = datetime.datetime.strptime('2022-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
reported_violations = sql_manager.fetch_reported_violations_between_dates(start_date=start_date, end_date=end_date)
pprint.pprint(reported_violations)

print(f"\n(3 - match) Fetching the reported violation by start_date = '1970-01-01 00:00:00' and end_date = '2099-01-01 00:00:00'")
start_date = datetime.datetime.strptime('1970-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
end_date = datetime.datetime.strptime('2099-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
reported_violations = sql_manager.fetch_reported_violations_between_dates(start_date=start_date, end_date=end_date)
pprint.pprint(reported_violations)


violation_uuid = reported_violations['fetched_violations'][0]['violation_uuid']
print(f"\n(4) Fetching the reported violation by violation_uuid:'{violation_uuid}'")
reported_violation_by_uuid = sql_manager.fetch_reported_violation_by_violation_uuid(violation_uuid=violation_uuid)
pprint.pprint(reported_violation_by_uuid)

print(f"\n(5) Deleting the reported violation by violation_uuid:'{violation_uuid}'")
print(f"fetching all violations between dates {start_date} - {end_date}")
all_violations = sql_manager.fetch_reported_violations_between_dates(start_date=start_date, end_date=end_date)
pprint.pprint(all_violations)

is_deleted = sql_manager.delete_reported_violation_by_violation_uuid(violation_uuid=violation_uuid)
pprint.pprint(is_deleted)

print(f"fetching all violations between dates {start_date} - {end_date}")
all_violations = sql_manager.fetch_reported_violations_between_dates(start_date=start_date, end_date=end_date)
pprint.pprint(all_violations)

print("trying to fetch corresponding image")
try:
    image_uuid = reported_violations['fetched_violations'][0]['image_uuid']
    get_result = sql_manager.get_encrypted_image_by_image_uuid(image_uuid=image_uuid)
    pprint.pprint(get_result)
    cv2.imshow("image", get_result['image'])
    cv2.waitKey(2500)
except Exception as e:
    print(f"Error raised: {e}")

# ================================= Testing 'iot_devices' table functionality =================================
print(f"{'='*100}\nTesting 'iot_devices' table functionality\n{'='*100}")
print(f"\n(1) Creating two IoT devices")
iot_device_1_info = {
    "device_name": "test_device_1",
    "device_id": "12",
}
iot_device_2_info = {
    "device_name": "test_device_2",
    "device_id": "13",
}
iot_device_1 = sql_manager.create_iot_device(**iot_device_1_info)
pprint.pprint(iot_device_1)
iot_device_2 = sql_manager.create_iot_device(**iot_device_2_info)
pprint.pprint(iot_device_2)

print(f"\n(2) Fetching all IoT devices")
all_iot_devices = sql_manager.fetch_all_iot_devices()
pprint.pprint(all_iot_devices)

print(f"\n(3) deleting the IoT devices by device_uuids {iot_device_1['device_uuid']} and {iot_device_2['device_uuid']}")
deleted_1 = sql_manager.delete_iot_device_by_device_uuid(device_uuid=iot_device_1['device_uuid'])
pprint.pprint(deleted_1)

print(f"Fetching all IoT devices")
all_iot_devices = sql_manager.fetch_all_iot_devices()
pprint.pprint(all_iot_devices)

deleted_2 = sql_manager.delete_iot_device_by_device_uuid(device_uuid=iot_device_2['device_uuid'])
pprint.pprint(deleted_2)

print(f"Fetching all IoT devices")
all_iot_devices = sql_manager.fetch_all_iot_devices()
pprint.pprint(all_iot_devices)

# ================================= Testing 'iot_device_and_rule' table functionality =================================
time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to continue...")
print(f"{'='*100}\nTesting 'iot_device_and_rule_relations' table functionality\n{'='*100}")

print(f"\n(1)  Creating a device-rule relation")

camera_ip = str(random.randint(0,255))+"."+str(random.randint(0,255))+"."+str(random.randint(0,255))+"."+str(random.randint(0,255))
print(f"\nCreating a camera with \n\tcamera_ip_address:'{camera_ip}'\n\tcamera_region:'{test_camera_info['camera_region']}'\n\tcamera_description:'{test_camera_info['camera_description']}'\n\tusername:'{test_camera_info['username']}'\n\tpassword:'{test_camera_info['password']}'\n\tstream_path:'{test_camera_info['stream_path']}'\n\tcamera_status:'{test_camera_info['camera_status']}'")
relation_camera = sql_manager.create_camera_info(camera_ip_address=camera_ip, camera_region=test_camera_info['camera_region'], camera_description=test_camera_info['camera_description'], username=test_camera_info['username'], password=test_camera_info['password'], stream_path=test_camera_info['stream_path'], camera_status=test_camera_info['camera_status'])
pprint.pprint(relation_camera)

print("Creating a rule")
choosen_type = random.choice(list(PREFERENCES.DEFINED_RULES.keys()))
test_rule = {
    "camera_uuid" : relation_camera['camera_uuid'],
    "rule_department": random.choice(PREFERENCES.DEFINED_DEPARTMENTS),
    "rule_type": choosen_type,
    "evaluation_method": random.choice(PREFERENCES.DEFINED_RULES[choosen_type]),
    "threshold_value": f"{random.uniform(0, 1):.3f}",
    "fol_threshold_value": f"{random.uniform(0, 1):.3f}",
    "rule_polygon": ','.join([f"{random.uniform(0, 1):.3f},{random.uniform(0, 1):.3f}" for _ in range(random.randint(3, 4))]),
}
created_rule = sql_manager.create_rule(**test_rule)
pprint.pprint(created_rule)

print(f"Creating a iot-device")
iot_device_info = {
    "device_name": "test_device_1",
    "device_id": "12",
}
iot_device_1 = sql_manager.create_iot_device(**iot_device_info)
pprint.pprint(iot_device_1)

print(f"Creating a device-rule relation")
relation_info = {
    "device_uuid": iot_device_1['device_uuid'],
    "rule_uuid": created_rule['rule_uuid'],
    "which_action": str(random.randint(0,255))
}
created_relation_1 = sql_manager.add_iot_device_and_rule_relation(**relation_info)
pprint.pprint(created_relation_1)

print("adding a second relation")
relation_info = {
    "device_uuid": iot_device_1['device_uuid'],
    "rule_uuid": created_rule['rule_uuid'],
    "which_action": str(random.randint(0,255))
}
created_relation_2 = sql_manager.add_iot_device_and_rule_relation(**relation_info)
pprint.pprint(created_relation_2)

print(f"\n(2) Fetching all device-rule relations")
all_relations = sql_manager.fetch_all_iot_device_and_rule_relations()
pprint.pprint(all_relations)

print(f"\n(3) Deleting the device-rule relation by relation_uuid:{created_relation_1['relation_uuid']}")

print("Deleting the first relation")
is_deleted = sql_manager.remove_iot_device_and_rule_relation_by_relation_uuid(relation_uuid=created_relation_1['relation_uuid'])
pprint.pprint(is_deleted)

print(f"Fetching all device-rule relations")
all_relations = sql_manager.fetch_all_iot_device_and_rule_relations()
pprint.pprint(all_relations)

print("Deleting the second relation")
is_deleted = sql_manager.remove_iot_device_and_rule_relation_by_relation_uuid(relation_uuid=created_relation_2['relation_uuid'])
pprint.pprint(is_deleted)

print(f"Fetching all device-rule relations")
all_relations = sql_manager.fetch_all_iot_device_and_rule_relations()
pprint.pprint(all_relations)


time.sleep(WAIT_TIME_BETWEEN_TESTS) if WAIT_TIME_BETWEEN_TESTS > 0 else input("Press Enter to finish the tests...")
cv2.destroyAllWindows()
sql_manager.close() #otherwise the database will be locked and cannot be deleted

print(f"{'='*100}\n{'='*100}\nTesting completed, deleting created files in 10 seconds\n{'='*100}\n{'='*100}")
time.sleep(10)
for path in paths_to_delete_after_tests:
    if Path(path).exists():
        os.remove(path)
        print(f"Deleted the path: {path}")

