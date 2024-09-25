#NOTE: All request (except token login and authentication) that is not resulted in unknown error will return status code 200 even though error occured. You should check is_task_successful field in response to see if the task was successful or not. If is_task_successful is False, then the detail field will contain the error message.
# If status code is 200, default reponse body will be like below:
# {
#     "status": 200,
#     "is_task_successful": true,
#     "detail": "Human readable message",
#     "json_data": {...}
# }
# else if HTTP-status code is not 200, either unknown error occurs or user is not authorized to access the resource.
# In such a case ensure user is authorized and try to get a new token and re-try the request. If the error persists, then request is failed

#Built-in Imports
import os, sys, platform, time, json, base64, random, datetime, uuid, secrets, hashlib, pprint, traceback
from typing import Optional, Dict, List, Any
from pathlib import Path

#3rd Party Imports
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import jwt, cv2
import numpy as np

# Local imports
API_SERVER_DIRECTORY = Path(__file__).resolve().parent
SAFETY_AI2_DIRECTORY = API_SERVER_DIRECTORY.parent
print(f"API_SERVER_DIRECTORY: {API_SERVER_DIRECTORY}")
print(f"SAFETY_AI2_DIRECTORY: {SAFETY_AI2_DIRECTORY}")
sys.path.append(str(SAFETY_AI2_DIRECTORY)) # Add the modules directory to the system path so that below imports work

import PREFERENCES
import sql_module

# Constants
ALGORITHM = "HS256"

app = FastAPI()
sql_database_path_local = PREFERENCES.SQL_DATABASE_FILE_PATH_LOCAL
database_manager = sql_module.SQLManager(db_path = sql_database_path_local, overwrite_existing_db= False)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
class User(BaseModel): 
    date_created: str  = Field(..., alias='date_created')
    date_updated: str = Field(..., alias='date_updated')
    user_uuid: str = Field(..., alias='user_uuid')
    username: str = Field(..., alias='username')
    personal_fullname: str = Field(..., alias='personal_fullname')

# Routes
class Token(BaseModel):
    access_token: str = Field(..., alias='access_token')
    token_type: str = Field(..., alias='token_type')

class default_response(BaseModel):
    status: int = Field(..., alias='status')
    is_task_successful: bool = Field(..., alias='is_task_successful')
    detail: str = Field(..., alias='detail') 
    json_data: dict = Field(None, alias='json_data')

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        # Check if user exists by username
        db_user_dict = database_manager.get_user_by_username(form_data.username)
        if db_user_dict is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )        
        
        # Check if password hash matches
        if not db_user_dict["hashed_password"] == hashlib.sha256(form_data.password.encode('utf-8')).hexdigest():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        del db_user_dict["hashed_password"]    
        expire = time.time() + 60*PREFERENCES.ACCESS_TOKEN_EXPIRE_MINUTES
        db_user_dict.update({"exp": expire})
        encoded_jwt = jwt.encode(db_user_dict, PREFERENCES.SERVER_JWT_KEY, algorithm=ALGORITHM)
        return {"access_token":encoded_jwt, "token_type":"bearer"}

async def authenticate_user_by_token(token: str = Depends(oauth2_scheme)):
    # Decodes JWT token and returns user if token is valid, else raises exception
    try:
        # This will raise an exception if token is invalid
        payload = jwt.decode(token, PREFERENCES.SERVER_JWT_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="'username' is not present in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT token could not be decoded",
                headers={"WWW-Authenticate": "Bearer"},
        )

    user = database_manager.get_user_by_username(username = username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.get("/test_ping_server", response_model = default_response)
async def test_ping_server():
    return {
        "status":status.HTTP_200_OK,
        "is_task_successful":True,
        "detail":"Server is working",
        "json_data":{"test_key":"test_value"}
    }

# User Table API =================================================================================================

class UserCreate(BaseModel):
    username: str
    personal_fullname: str
    plain_password: str
@app.post("/create_user", response_model = default_response)
async def create_user_api(user_info: UserCreate):
    user_info_dict = user_info.model_dump( exclude= {}, by_alias=False)
    try:
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"User created successfully",
            "json_data": database_manager.create_user(**user_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

@app.get("/get_all_users", response_model = default_response)
async def get_all_users_api(authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['MANAGE_USERS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":  "All users are fetched successfully",
            "json_data": database_manager.get_all_users(),
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

@app.get("/get_user_by_username", response_model = default_response)
async def get_user_by_username_api(username: str, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['MANAGE_USERS']
    try:
        if(authenticated_user['username'] != username):
            user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
            if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
                raise Exception("User is not authorized to access this resource")    
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":  "User is fetched successfully",
            "json_data": database_manager.get_user_by_username(username),
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }
    
@app.get("/get_user_by_uuid")
async def get_user_by_uuid_api(user_uuid: str, authenticated_user = Depends(authenticate_user_by_token)):   
    REQUIRED_AUTHORIZATIONS = ['MANAGE_USERS']
    try:
        if(authenticated_user['user_uuid'] != user_uuid):
            user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
            if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
                raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":  "User is fetched successfully",
            "json_data": database_manager.get_user_by_user_uuid(user_uuid),
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class DeleteUser(BaseModel):
    user_uuid: str
@app.delete("/delete_user_by_uuid", response_model = default_response)
async def delete_user_by_username_api( user_info : DeleteUser, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['MANAGE_USERS']
    try:
        if(authenticated_user['user_uuid'] != user_info.user_uuid):
            user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
            if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
                raise Exception("User is not authorized to access this resource")
        
        user_info_dict = user_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":  "User is deleted successfully",
            "json_data": database_manager.delete_user_by_user_uuid(**user_info_dict),
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }
    
# Camera Info Table API =================================================================================================
@app.get("/fetch_all_camera_info", response_model = default_response)
async def fetch_all_camera_info_api(authenticated_user: User = Depends(authenticate_user_by_token)):    
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES', 'UPDATE_CAMERAS']
    try:

        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":  "All camera info are fetched successfully",
            "json_data": database_manager.fetch_all_camera_info(),
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class CreateCameraInfo(BaseModel):
    camera_ip_address: str
    camera_region: Optional[str] = None
    camera_description: Optional[str] = None
    username: str
    password: str
    stream_path: str
    camera_status:str    
@app.post("/create_camera_info", response_model = default_response)
async def create_camera_info_api(camera_info: CreateCameraInfo, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['UPDATE_CAMERAS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        camera_info_dict = camera_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Camera info created successfully",
            "json_data": database_manager.create_camera_info(**camera_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class UpdateCameraInfoAttribute(BaseModel):
    camera_uuid: str
    attribute_name: str
    attribute_value: str
@app.post("/update_camera_info_attribute", response_model = default_response)
async def update_camera_info_attribute_api(camera_info: UpdateCameraInfoAttribute, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['UPDATE_CAMERAS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        camera_info_dict = camera_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Camera info updated successfully",
            "json_data": database_manager.update_camera_info_attribute(**camera_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }
    
class DeleteCameraInfo(BaseModel):
    camera_uuid: str
@app.delete("/delete_camera_info", response_model = default_response)
async def delete_camera_info_api(camera_info: DeleteCameraInfo, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['UPDATE_CAMERAS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        camera_info_dict = camera_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Camera info deleted successfully",
            "json_data": database_manager.delete_camera_info_by_uuid(**camera_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class FetchCameraInfo(BaseModel):
    camera_uuid: str
@app.post("/fetch_camera_info", response_model = default_response)
async def fetch_camera_info_api(camera_info: FetchCameraInfo, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES', 'UPDATE_CAMERAS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        camera_info_dict = camera_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Camera info fetched successfully",
            "json_data": database_manager.fetch_camera_info_by_uuid(**camera_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }
    
class FetchCameraUUIDByIP(BaseModel):
    camera_ip_address: str
@app.post("/fetch_camera_uuid_by_ip", response_model = default_response)
async def fetch_camera_uuid_by_ip_api(camera_info: FetchCameraUUIDByIP, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES', 'UPDATE_CAMERAS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        camera_info_dict = camera_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Camera uuid fetched successfully",
            "json_data": database_manager.fetch_camera_uuid_by_camera_ip_address(**camera_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }
    
# Last Frames Table API =================================================================================================
@app.get("/fetch_last_frames_info_without_frames", response_model = default_response)
async def fetch_last_frames_info_without_frames_api(authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES', 'UPDATE_CAMERAS', 'ISG_UI', 'SUMMARY_PAGE']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Last frames info fetched successfully",
            "json_data": database_manager.get_all_last_camera_frame_info_without_frames()
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class UpdateLastFrameAs(BaseModel):
    camera_uuid: str
    is_violation_detected: bool # will be stored as int by int(bool) conversion in the dataset
    is_person_detected: bool # will be stored as int by int(bool) conversion in the dataset
    frame_b64_string: str
@app.post("/update_last_camera_frame_as", response_model = default_response)
async def update_last_camera_frame_as_api(last_frame_info: UpdateLastFrameAs, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES', 'UPDATE_CAMERAS', 'ISG_UI', 'SUMMARY_PAGE']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        last_frame_info_dict = last_frame_info.model_dump( exclude= {}, by_alias=False)
        last_frame_info_dict['last_frame'] = database_manager.decode_url_body_b64_string_to_frame(base64_encoded_image_string=last_frame_info_dict['frame_b64_string'])
        del last_frame_info_dict['frame_b64_string']

        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Last frame info updated successfully",
            "json_data": database_manager.update_last_camera_frame_as_by_camera_uuid(**last_frame_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class FetchLastFrameInfo(BaseModel):
    camera_uuid: str
@app.post("/fetch_last_camera_frame_info", response_model = default_response)
async def fetch_last_camera_frame_info_api(last_frame_info: FetchLastFrameInfo, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES', 'UPDATE_CAMERAS', 'ISG_UI', 'SUMMARY_PAGE']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        last_frame_info_dict = last_frame_info.model_dump( exclude= {}, by_alias=False)
        # Convert np array to base64 string for response
        response_json_data = database_manager.get_last_camera_frame_by_camera_uuid(**last_frame_info_dict)
        response_json_data['frame_b64_string'] = database_manager.encode_frame_for_url_body_b64_string(np_ndarray= response_json_data['last_frame_np_array'])
        del response_json_data['last_frame_np_array']
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Last frame info fetched successfully",
            "json_data": response_json_data
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

# Reported Violations Table API =================================================================================================
class FetchReportedViolationsBetweenDates(BaseModel):
    start_date: str # format: 'YYYY-MM-DD HH:MM:SS'
    end_date: str # format: 'YYYY-MM-DD HH:MM:SS'
@app.post("/fetch_reported_violations_between_dates", response_model = default_response)
async def fetch_reported_violations_between_dates_api(report_info: FetchReportedViolationsBetweenDates, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['REPORTED_VIOLATIONS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        # start date is older than end date, otherwise it will raise exception
        report_info_dict = report_info.model_dump( exclude= {}, by_alias=False)
        report_info_dict['start_date'] = datetime.datetime.strptime(report_info_dict['start_date'], '%Y-%m-%d %H:%M:%S')
        report_info_dict['end_date'] = datetime.datetime.strptime(report_info_dict['end_date'], '%Y-%m-%d %H:%M:%S')
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":f"Reported violations fetched successfully between dates {report_info_dict['start_date']} and {report_info_dict['end_date']}",
            "json_data": database_manager.fetch_reported_violations_between_dates(**report_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }
    
class CreateReportedViolation(BaseModel):
    camera_uuid: str
    violation_frame_b64_string: str
    violation_date: str # format: 'YYYY-MM-DD HH:MM:SS'
    violation_type: str
    violation_score : float # between 0 and 1
    region_name: str
@app.post("/create_reported_violation", response_model = default_response)
async def create_reported_violation_api(report_info: CreateReportedViolation, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = [] # only admin privilages can create reported violations 
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        report_info_dict = report_info.model_dump( exclude= {}, by_alias=False)
        report_info_dict['violation_frame'] = database_manager.decode_url_body_b64_string_to_frame(base64_encoded_image_string=report_info_dict['violation_frame_b64_string'])
        del report_info_dict['violation_frame_b64_string']
        report_info_dict['violation_date'] = datetime.datetime.strptime(report_info_dict['violation_date'], '%Y-%m-%d %H:%M:%S')
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Reported violation created successfully",
            "json_data": database_manager.create_reported_violation(**report_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class FetchReportedViolation(BaseModel):
    violation_uuid: str
@app.post("/fetch_reported_violation", response_model = default_response)
async def fetch_reported_violation_api(report_info: FetchReportedViolation, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['REPORTED_VIOLATIONS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        report_info_dict = report_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Reported violation fetched successfully",
            "json_data": database_manager.fetch_reported_violation_by_violation_uuid(**report_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class DeleteReportedViolation(BaseModel):
    violation_uuid: str
@app.delete("/delete_reported_violation", response_model = default_response)
async def delete_reported_violation_api(report_info: DeleteReportedViolation, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['REPORTED_VIOLATIONS'] 
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        report_info_dict = report_info.model_dump( exclude= {}, by_alias=False)
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Reported violation deleted successfully",
            "json_data": database_manager.delete_reported_violation_by_violation_uuid(**report_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

# Image Paths Table API =================================================================================================
class GetImage(BaseModel):
    image_uuid: str

@app.post("/get_image", response_model = default_response)
async def get_image_api(image_info: GetImage, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['REPORTED_VIOLATIONS']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        image_info_dict = image_info.model_dump( exclude= {}, by_alias=False) 
        json_data = database_manager.get_encrypted_image_by_image_uuid(**image_info_dict)  
        json_data['frame_b64_string'] = database_manager.encode_frame_for_url_body_b64_string(np_ndarray= json_data['frame'])
        del json_data['frame']
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Image fetched successfully",
            "json_data": json_data
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

# Counts Table API =================================================================================================

class UpdateCount(BaseModel):
    count_key: str
    count_subkey: str
    delta_count: float
@app.post("/update_count", response_model = default_response)
async def update_count_api(count_info: UpdateCount, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = [] # only admin privilages
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        count_info_dict = count_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Count updated successfully",
            "json_data": database_manager.update_count(**count_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class GetCountsByCountKey(BaseModel):
    count_key: str
@app.post("/get_counts_by_count_key", response_model = default_response)
async def get_counts_by_count_key_api(count_info: GetCountsByCountKey, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = [] # only admin privilages

    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        count_info_dict = count_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":f"Counts fetched successfully for count_key: {count_info_dict['count_key']}",
            "json_data": database_manager.get_counts_by_count_key(**count_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class GetCountByCountKeyAndSubkey(BaseModel):
    count_key: str
    count_subkey: str
@app.post("/get_count_by_count_key_and_subkey", response_model = default_response)
async def get_count_by_count_key_and_subkey_api(count_info: GetCountByCountKeyAndSubkey, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = [] # only admin privilages

    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        count_info_dict = count_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":f"Count fetched successfully for count_key: {count_info_dict['count_key']} and count_subkey: {count_info_dict['count_subkey']}",
            "json_data": database_manager.get_total_count_by_count_key_and_count_subkey(**count_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

@app.get("/get_all_counts", response_model = default_response)
async def get_all_counts_api(authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = [] # only admin privilages

    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"All counts fetched successfully",
            "json_data": database_manager.fetch_all_counts()
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

# Rules Info Table API =================================================================================================

class CreateRule(BaseModel):
    camera_uuid: str
    rule_department: str
    rule_type: str
    evaluation_method: str
    threshold_value: float
    fol_threshold_value: float
    rule_polygon: str
@app.post("/create_rule", response_model = default_response)
async def create_rule_api(rule_info: CreateRule, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        rule_info_dict = rule_info.model_dump( exclude= {}, by_alias=False) 
        rule_info_dict['threshold_value'] = str(rule_info_dict['threshold_value'])
        rule_info_dict['fol_threshold_value'] = str(rule_info_dict['fol_threshold_value'])
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Rule created successfully",
            "json_data": database_manager.create_rule(**rule_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class TriggerRule(BaseModel):
    rule_uuid: str
@app.post("/trigger_rule", response_model = default_response)
async def trigger_rule_api(rule_info: TriggerRule, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        rule_info_dict = rule_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Rule triggered successfully",
            "json_data": database_manager.trigger_rule_by_rule_uuid(**rule_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class DeleteRule(BaseModel):
    rule_uuid: str
@app.delete("/delete_rule", response_model = default_response)
async def delete_rule_api(rule_info: DeleteRule, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        rule_info_dict = rule_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Rule deleted successfully",
            "json_data": database_manager.delete_rule_by_rule_uuid(**rule_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class FetchRulesByCameraUUID(BaseModel):
    camera_uuid: str
@app.post("/fetch_rules_by_camera_uuid", response_model = default_response)
async def fetch_rules_by_camera_uuid_api(rule_info: FetchRulesByCameraUUID, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        rule_info_dict = rule_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Rules fetched successfully",
            "json_data": database_manager.fetch_rules_by_camera_uuid(**rule_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

@app.get("/fetch_all_rules", response_model = default_response)
async def fetch_all_rules_api(authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['EDIT_RULES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"All rules fetched successfully",
            "json_data": database_manager.fetch_all_rules()
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

# Authorizations Table API =================================================================================================
#    def get_user_authorizations_by_user_uuid(self, user_uuid:str=None)->dict:
class FetchUserAuthorizations(BaseModel):
    user_uuid: str
@app.post("/fetch_user_authorizations_by_user_uuid", response_model =  default_response )
async def fetch_user_authorizations_by_user_uuid_api(user_info: FetchUserAuthorizations, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = []
    try:
        user_info_dict = user_info.model_dump(exclude= {}, by_alias=False)
        user_uuid = user_info_dict['user_uuid']
        if(authenticated_user['user_uuid'] != user_uuid):
            user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
            if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
                raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"User authorizations fetched successfully",
            "json_data": database_manager.get_user_authorizations_by_user_uuid(**user_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

@app.get("/fetch_all_authorizations", response_model = default_response)
async def fetch_all_authorizations_api(authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['MANAGE_USERS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"All authorizations fetched successfully",
            "json_data": database_manager.fetch_all_authorizations()
        }
     
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

#def add_authorization(self, user_uuid:str=None, authorization_name:str=None)-> dict:
class AddAuthorization(BaseModel):
    username: str
    authorization_name: str
@app.post("/add_authorization_by_username", response_model = default_response)
async def add_authorization_api(authorization_info: AddAuthorization, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED = ['MANAGE_USERS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED):
            raise Exception("User is not authorized to access this resource")
        
        request_info_dict = authorization_info.model_dump( exclude= {}, by_alias=False)

        user_info = database_manager.get_user_by_username(username= request_info_dict['username'])

        authorization_info_dict = {
            "user_uuid": user_info['user_uuid'],
            "authorization_name": request_info_dict['authorization_name']
        }         
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Authorization added successfully",
            "json_data": database_manager.add_authorization(**authorization_info_dict)
        }
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

#    def remove_authorization(self, authorization_uuid:str = None)->dict:
class RemoveAuthorization(BaseModel):
    authorization_uuid: str
@app.delete("/remove_authorization", response_model = default_response)
async def remove_authorization_api(authorization_info: RemoveAuthorization, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['MANAGE_USERS']
    try:
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]       
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        authorization_info_dict = authorization_info.model_dump( exclude= {}, by_alias=False)

        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"All authorizations fetched successfully",
            "json_data": database_manager.remove_authorization(authorization_uuid= authorization_info_dict['authorization_uuid'])
        }
     
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

# ======================================= iot_device ========================================

class CreateIotDevice(BaseModel):
    device_name: str
    device_id: str
@app.post("/create_iot_device", response_model = default_response)
async def create_iot_device_api(iot_device_info: CreateIotDevice, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['IOT_DEVICES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        iot_device_info_dict = iot_device_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Iot device created successfully",
            "json_data": database_manager.create_iot_device(**iot_device_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class UpdateIotDevice(BaseModel):
    device_uuid: str
    device_name: str
    device_id: str
@app.post("/update_iot_device", response_model = default_response)
async def update_iot_device_api(iot_device_info: UpdateIotDevice, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['IOT_DEVICES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        iot_device_info_dict = iot_device_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Iot device updated successfully",
            "json_data": database_manager.update_device_by_device_uuid(**iot_device_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }
    
class DeleteIotDevice(BaseModel):
    device_uuid: str
@app.delete("/delete_iot_device", response_model = default_response)
async def delete_iot_device_api(iot_device_info: DeleteIotDevice, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['IOT_DEVICES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        iot_device_info_dict = iot_device_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Iot device deleted successfully",
            "json_data": database_manager.delete_iot_device_by_device_uuid(**iot_device_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

@app.get("/fetch_all_iot_devices", response_model = default_response)
async def fetch_all_iot_devices_api(authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['IOT_DEVICES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"All iot devices fetched successfully",
            "json_data": database_manager.fetch_all_iot_devices()
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

# ================================iot_device_and_rule_relations==============================
class AddIotDeviceAndRuleRelation(BaseModel):
    device_uuid: str
    rule_uuid: str
    which_action: str
@app.post("/add_iot_device_and_rule_relation", response_model = default_response)
async def add_iot_device_and_rule_relation_api(iot_device_and_rule_relation_info: AddIotDeviceAndRuleRelation, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['IOT_DEVICES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        iot_device_and_rule_relation_info_dict = iot_device_and_rule_relation_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Iot device and rule relation added successfully",
            "json_data": database_manager.add_iot_device_and_rule_relation(**iot_device_and_rule_relation_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

@app.get("/fetch_all_iot_device_and_rule_relations", response_model = default_response)
async def fetch_all_iot_device_and_rule_relations_api(authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['IOT_DEVICES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"All iot device and rule relations fetched successfully",
            "json_data": database_manager.fetch_all_iot_device_and_rule_relations()
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

class RemoveIotDeviceAndRuleRelation(BaseModel):
    relation_uuid: str
@app.delete("/remove_iot_device_and_rule_relation", response_model = default_response)
async def remove_iot_device_and_rule_relation_api(iot_device_and_rule_relation_info: RemoveIotDeviceAndRuleRelation, authenticated_user: User = Depends(authenticate_user_by_token)):
    REQUIRED_AUTHORIZATIONS = ['IOT_DEVICES']
    try:
        # Check if user is authorized to access this resource
        user_authorizations = [ auth_dict['authorization_name'] for auth_dict in  database_manager.get_user_authorizations_by_user_uuid(user_uuid= authenticated_user['user_uuid'])['user_authorizations']]
        if 'ADMIN_PRIVILEGES' not in user_authorizations and not all (auth in user_authorizations for auth in REQUIRED_AUTHORIZATIONS):
            raise Exception("User is not authorized to access this resource")
        
        iot_device_and_rule_relation_info_dict = iot_device_and_rule_relation_info.model_dump( exclude= {}, by_alias=False) 
        return {
            "status":status.HTTP_200_OK,
            "is_task_successful": True,
            "detail":"Iot device and rule relation removed successfully",
            "json_data": database_manager.remove_iot_device_and_rule_relation_by_relation_uuid(**iot_device_and_rule_relation_info_dict)
        }
    
    except Exception as e:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "is_task_successful": False,
            "detail": str(e),
            "json_data":  {}
        }

pass
