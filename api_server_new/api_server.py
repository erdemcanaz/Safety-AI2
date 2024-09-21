#NOTE: All request (except token login and authentication) that is not resulted in unknown error will return status code 200 even though error occured. You should check is_task_successful field in response to see if the task was successful or not. If is_task_successful is False, then the detail field will contain the error message.
# If status code is 200, default reponse body will be like below:
# {
#     "status": 200,
#     "is_task_successful": true,
#     "detail": "Human readable message",
#     "json_data": {...}
# }
# else if status code is not 200, either unknown error occurs or user is not authorized to access the resource.
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
sql_database_path_local = PREFERENCES.SQL_DATABASE_FOLDER_PATH_LOCAL / "api_server_database.db"
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
    REQUIRED_AUTHORIZATIONS = ['MENAGE_USERS']
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
    REQUIRED_AUTHORIZATIONS = ['MENAGE_USERS']
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
    REQUIRED_AUTHORIZATIONS = ['MENAGE_USERS']
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
@app.post("/delete_camera_info", response_model = default_response)
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