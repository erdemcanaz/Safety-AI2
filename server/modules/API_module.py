from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, List, Any
import jwt
import time
import json, os, platform
from pathlib import Path
import secrets
import encryption_module
import uuid, random, datetime

# Constants
SERVER_JWT_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Load user database
API_MODULE_PATH = Path(__file__).resolve()

is_linux = platform.system() == "Linux"
if is_linux:
    USER_DATABASE_JSON_PATH = API_MODULE_PATH.parent.parent.parent.parent / "safety_AI_volume" / "static_database.json"
else:
    USER_DATABASE_JSON_PATH = API_MODULE_PATH.parent.parent / "configs" / "static_database.json"
with open(USER_DATABASE_JSON_PATH, "r") as f:
    USER_DB: Dict[str, Dict[str, str]] = json.load(f)["user_db"]

# FastAPI instance
app = FastAPI()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str = None
    full_name: str = None
    email: str = None
    job_title: str = None
    plain_password : str = None
    hashed_password : str = None
    allowed_tos : List[str] = None

class MessageResponse(BaseModel):
    message: str

class ListResponse(BaseModel):
    list_ : List

class ListOfDictsResponse(BaseModel):
    list_: List[Dict[str, Any]]  # Adjusted to expect a list of dictionaries

# Helper functions
def verify_password(plain_password, hashed_password):
    hashed_password_candidate = encryption_module.hash_string(plain_text=plain_password) # uses SHA256 hashing
    return hashed_password == hashed_password_candidate

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return User(**user_dict)

def authenticate_user(user_db, username: str, password: str):
    user = get_user(user_db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = time.time() + expires_delta * 60
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SERVER_JWT_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SERVER_JWT_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("user_name")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(USER_DB, username)
    if user is None:
        raise credentials_exception
    return user

# Routes
@app.post("/get_token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(USER_DB, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"user_name": user.username, "person_name": user.full_name, "job_title":"developer", "allowed_tos":user.allowed_tos})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/get_allowed_tos", response_model=ListResponse)
async def return_test_text(current_user: User = Depends(get_current_user)):
    return {"list_":current_user.allowed_tos}

@app.get("/get_isg_ui_data", response_model=ListOfDictsResponse)
async def login_for_access_token(current_user: User = Depends(get_current_user)):
    if "ISG_APP" not in current_user.allowed_tos:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authorized for this app",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    test_list = []
    for i in range(10):
        dummy_dict = {
            "camera_uuid": uuid.uuid4(),
            "camera_region" : random.choice(["A","B","C","D","E","F","G","H","I","J"]),
            "date_time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "image_base_64" : "",
            "person_normalized_bboxes" : [ [random.random(), random.random(), random.random(), random.random(), random.choice(["","","","","","","","", "hard_hat", "restricted_area"]),] for _ in range(random.randint(0,5))],
        }

        test_list.append(dummy_dict)
    
    return {"list_": test_list}


#Run the application
if __name__ == "__main__":
    import uvicorn
    server_ip_address = input("Enter the server IP address: ")
    uvicorn.run(app, host=server_ip_address, port=80)
