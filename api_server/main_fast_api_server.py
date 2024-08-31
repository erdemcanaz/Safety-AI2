#Built-in Imports
import os, sys, platform, time, json, base64, random, datetime, uuid, secrets, hashlib, pprint, traceback
from typing import Optional, Dict, List, Any
from pathlib import Path

#3rd Party Imports
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt, cv2

# Local imports
API_SERVER_DIRECTORY = Path(__file__).resolve().parent
SAFETY_AI2_DIRECTORY = API_SERVER_DIRECTORY.parent
sys.path.append(SAFETY_AI2_DIRECTORY) # Add the modules directory to the system path so that imports work

#Custom Imports
import SQL_module
import PREFERENCES 

# Constants
SERVER_JWT_KEY = "c56b5dfbc8b728d15f2f9d816c3b9d89f4c2d19f8a1e7b8b9a4f8f6b0c5e2d6a"
#SERVER_JWT_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# =================================================================================================
# FastAPI Server

app = FastAPI()
database_manager = SQL_module.DatabaseManager(db_path = PREFERENCES.SQL_DATABASE_PATH)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    date_created: str
    date_updated: str
    user_uuid: str
    username: str
    personal_fullname: str
    exp: float

# Routes
class Token(BaseModel):
    access_token: str
    token_type: str
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
    expire = time.time() + 60*ACCESS_TOKEN_EXPIRE_MINUTES
    db_user_dict.update({"exp": expire})
    encoded_jwt = jwt.encode(db_user_dict, SERVER_JWT_KEY, algorithm=ALGORITHM)
    return {"access_token":encoded_jwt, "token_type":"bearer"}

async def authenticate_user_by_token(token: str = Depends(oauth2_scheme)):
    # Decode JWT token and get user info
    try:
        payload = jwt.decode(token, SERVER_JWT_KEY, algorithms=[ALGORITHM])
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

@app.get("/test")
async def test_api():
    return {"description": "Deneme", "stat1": random.uniform(0,1000), "stat2": random.uniform(0,1000)}

# User Table API =================================================================================================
class UserCreate(BaseModel):
    username: str
    plain_password: str
    personal_fullname: str
@app.post("/create_user")
async def create_user_api(user_info: UserCreate):
    user_info_dict = user_info.dict()
    try:
        return {"user_info":  database_manager.create_user(**user_info_dict)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/fetch_all_user_info")  #http://<HOST IP>/fetch_all_user_info?start_from=0&user_count=10
async def fetch_all_user_info_api(start_from: int = 0, user_count: int = 99999 , authenticated_user: User = Depends(authenticate_user_by_token)):
    return {"users":  database_manager.fetch_all_user_info()[start_from:start_from+user_count]}

@app.get("/get_user_by_username/{user_name}")
async def get_user_by_username_api(user_name: str, authenticated_user = Depends(authenticate_user_by_token)):   
    user_info = database_manager.get_user_by_username(user_name)
    if user_info is not None: del user_info["hashed_password"]
    return {"user_info":  user_info}

@app.get("/get_user_by_uuid/{user_uuid}")
async def get_user_by_uuid_api(user_uuid: str, authenticated_user = Depends(authenticate_user_by_token)):   
    user_info = database_manager.get_user_by_uuid(user_uuid)
    if user_info is not None: del user_info["hashed_password"]
    return {"user_info":  user_info}

# Camera Info Table API =================================================================================================
class CreateCameraInfo(BaseModel):
    camera_ip_address: str
    username: str
    password: str
    stream_path: str
    camera_status:str
    NVR_ip_address: Optional[str] = None
    camera_region: Optional[str] = None
    camera_description: Optional[str] = None
@app.post("/create_camera_info")
async def create_camera_info_api(camera_info: CreateCameraInfo):
    #TODO: check if user can create camera info
    camera_info_dict = camera_info.dict()
    camera_info_dict.update({"camera_uuid": str(uuid.uuid4())})
    camera_info_dict.update({"stream_path":"profile2/media.smp"})
    try:
        return {"camera_info":  database_manager.create_camera_info(**camera_info_dict)}
    except Exception as e:
        raise HTTPException(sktatus_code=400, detail=str(e))
    
class UpdateCameraInfo(BaseModel):
    camera_uuid: str
    attribute: str
    value: Any
@app.post("/update_camera_info_attribute")
async def update_camera_info_attribute_api(update_info: UpdateCameraInfo):
    #TODO: check if user can update camera info
    update_info_dict = update_info.dict()
    try:
        return {"camera_info":  database_manager.update_camera_info_attribute(**update_info_dict)}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/fetch_all_camera_info")
async def fetch_all_camera_info_api():
    #TODO: check if user can fetch camera info
    try:
        return {"camera_info":  database_manager.fetch_all_camera_info()}
    except Exception as e:
        return {"error": str(e)}
    
@app.delete("/delete_camera_info_by_uuid/{camera_uuid}")
async def delete_camera_info_by_uuid_api(camera_uuid: str):
    try:
        return {"camera_info":  database_manager.delete_camera_info_by_uuid(camera_uuid)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Last Frames Table API =================================================================================================
@app.get("/get_all_last_camera_frame_info_without_BLOB")
async def get_all_last_camera_frame_info_without_BLOB_api():
    #TODO: check if user can fetch camera info
    try:
        return {"last_frame_info":  database_manager.get_all_last_camera_frame_info_without_BLOB()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get_last_camera_frame_by_camera_uuid/{camera_uuid}")
async def get_last_camera_frame_by_camera_uuid_api(camera_uuid: str):
    #TODO: check if user can fetch camera info
    try:
        return {"last_frame_info":  database_manager.get_last_camera_frame_by_camera_uuid(camera_uuid, convert_b64_to_cv2frame = False)}
    except Exception as e:
        return {"error": str(e)}

# Reported Violations Table API =================================================================================================
@app.get("/fetch_reported_violations_between_dates", description="Fetches all reported violations between two dates where date format is dd.mm.yyyy as string. startdate-00:00:00 and enddate-23:59:59 will be fethed.")
async def fetch_reported_violations_between_dates_api(start_date: str, end_date: str):
    try:
        start_date = datetime.datetime.strptime(start_date, "%d.%m.%Y")
        end_date = datetime.datetime.strptime(end_date, "%d.%m.%Y") + datetime.timedelta(days=1)
        return {"reported_violations":  database_manager.fetch_reported_violations_between_dates(start_date, end_date)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Image Paths Table API =================================================================================================
@app.get("/get_encrypted_image_by_uuid")
async def get_encrypted_image_by_uuid_api(image_uuid: str):
    #TODO: check if user can fetch image info
    try:
        return {"image_info":  database_manager.get_encrypted_image_by_uuid(image_uuid=image_uuid, get_b64_image_only= True)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Counts Table API =================================================================================================
@app.get("/get_counts_by_camera_uuid/{camera_uuid}")
async def get_counts_by_camera_uuid_api(camera_uuid: str):
    #TODO: check if user can fetch camera info
    try:
        return {"counts":  database_manager.get_counts_by_camera_uuid(camera_uuid)}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/fetch_all_counts")
async def fetch_all_counts_api():
    #TODO: check if user can fetch camera info
    try:
        return {"counts":  database_manager.fetch_all_counts()}
    except Exception as e:
        return {"error": str(e)}
    
# Rules Info Table API =================================================================================================
class RuleInfo(BaseModel):
    camera_uuid: str
    rule_department: str
    rule_type: str
    evaluation_method: str
    threshold_value: float
    rule_polygon: str
@app.post("/create_rule")
async def create_rule_api(rule_info: RuleInfo):
    #TODO: check if user can create camera info
    rule_info_dict = rule_info.dict()
    try:
        return {"rule_info":  database_manager.create_rule(**rule_info_dict)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/delete_rule_by_rule_uuid/{rule_uuid}")
async def delete_rule_by_uuid_api(rule_uuid: str):
    try:
        return {"rule_info":  database_manager.delete_rule_by_rule_uuid(rule_uuid)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/fetch_rules_by_camera_uuid/{camera_uuid}")
async def fetch_rules_by_camera_uuid_api(camera_uuid: str):
    #TODO: check if user can fetch camera rules info
    try:
        return {"rules":  database_manager.fetch_rules_by_camera_uuid(camera_uuid)}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/fetch_all_rules")
async def fetch_all_rules_api():
    #TODO: check if user can fetch camera rules info
    try:
        return {"rules":  database_manager.fetch_all_rules()}
    except Exception as e:
        return {"error": str(e)}
    
# Shift Counts Table API =================================================================================================
@app.get("/get_shift_counts_between_dates")
async def get_shift_counts_between_dates(start_date: str, end_date: str):
    try:
        start_date = datetime.datetime.strptime(start_date, "%d.%m.%Y")
        end_date = datetime.datetime.strptime(end_date, "%d.%m.%Y") + datetime.timedelta(days=1)
        return {"shift_counts":  database_manager.get_shift_counts_between_dates(start_date, end_date)}
    except Exception as e:
        return {"error": str(e)}
    #get_shift_counts_between_dates

# Authorizations Table API =================================================================================================
@app.get("/get_authorizations")
async def get_authorizations_api(authenticated_user = Depends(authenticate_user_by_token)):
    print(authenticated_user)
    try:
        return {"authorizations":  database_manager.fetch_user_authorizations(user_uuid=authenticated_user["user_uuid"])}
    except Exception as e:
        return {"error": str(e)}


    

