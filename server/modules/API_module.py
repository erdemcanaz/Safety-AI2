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

class DateRangeRequest(BaseModel):
    start_date: str
    end_date: str

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
async def get_isg_ui_data(current_user: User = Depends(get_current_user)):
    if "ISG_APP" not in current_user.allowed_tos:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authorized for this app",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

    # GENERATE DUMMY DATA TODO: Replace this with real data
    test_list = []
    for i in range(10):
        dummy_dict = {
            "camera_uuid": uuid.uuid4(),
            "camera_hr_name" : random.choice(["A","B","C","D","E","F","G","H","I","J"]),
            "date_time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "people_analyzed" : random.randint(0,5000),
            "frame_analyzed" : random.randint(0,5000),
            "hard_hat_violation_counts" : [random.randint(0,5000),random.randint(0,5000)],
            "restricted_area_violation_counts" : [random.randint(0,5000),random.randint(0,5000)],            
            "person_normalized_bboxes" : [ [random.uniform(0,0.45), random.uniform(0,0.45), random.uniform(0.55,1), random.uniform(0.55,1), random.choice(["","","","", "hard_hat", "restricted_area"]),] for _ in range(random.randint(0,3))],

            "image_base_64" : "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BAgQIECAQDMBBbDZwMUlQIAAAQIECCiA9gABAgQIECBAoJmAAths4OISIECAAAECBBRAe4AAAQIECBAg0ExAAWw2cHEJECBAgAABAgqgPUCAAAECBAgQaCagADYbuLgECBAgQIAAAQXQHiBAgAABAgQINBNQAJsNXFwCBAgQIECAgAJoDxAgQIAAAQIEmgkogM0GLi4BAgQIECBAQAG0BwgQIECAAAECzQQUwGYDF5cAAQIECBAgoADaAwQIECBAgACBZgIKYLOBi0uAAAECBAgQUADtAQIECBAgQIBAMwEFsNnAxSVAgAABAgQIKID2AAECBAgQIECgmYAC2Gzg4hIgQIAAAQIEFEB7gAABAgQIECDQTEABbDZwcQkQIECAAAECCqA9QIAAAQIECBBoJqAANhu4uAQIECBAgAABBdAeIECAAAECBAg0E1AAmw1cXAIECBAgQICAAmgPECBAgAABAgSaCSiAzQYuLgECBAgQIEBAAbQHCBAgQIAAAQLNBBTAZgMXlwABAgQIECCgANoDBAgQIECAAIFmAgpgs4GLS4AAAQIECBBQAO0BAgQIECBAgEAzAQWw2cDFJbC1Aocddth49atfPZ73vOeN3XffffznP/8Z3/jGN8aXvvSlpT/6ox/96HjFK14xHvOYx4wbb7xxnHDCCQv/7fr168cxxxwz9t5777HzzjuPhx9+eNxzzz3jl7/85fja1742brnllqW/8//qjctm27Bhw1i3bt149rOfvapsT3/608fb3/72ccghh0z+O+yww3jwwQfH7bffPi699NJpFl4ECBDIBBTATMg6AQKTQBSPU089dRx00EHjsY997CaVhx56aFUFMErPu9/97vHEJz5x+ozNFcAohVGSovgtekXhOf3008d11133/2ZCy2b78Ic/PI488shHOM6HuOuuu8bnPve5qdDNv/bdd9/x8Y9/fOy3334LM//73/8el19++YjP9yJAgMCWBBRA+4MAgVRg1113HZ/61KfGgQceOL33tttuGz/4wQ/G9ddfP2666ab038/eEJ/z2c9+drzoRS/a9G8WFcCXv/zl4+STT55K4h133DEd7fvOd74zldC3vvWt44gjjhg77bTTdCTwHe94x7j//vuX/hu21xuXzfa6171uvO1tbxu77LLL+Nvf/jbOPvvsTdmiGMcR1sh26623jpNOOmn8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"
        }

        test_list.append(dummy_dict)
    
    return {"list_": test_list}

@app.post("/get_violation_reports", response_model=ListOfDictsResponse)
async def get_isg_ui_data(date_range: DateRangeRequest, current_user: User = Depends(get_current_user)):
    if "IHLAL_RAPORLARI_APP" not in current_user.allowed_tos:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authorized for this app",
            headers={"WWW-Authenticate": "Bearer"},
        )    

    start_date = date_range.start_date
    end_date = date_range.end_date

    print(f"Start Date: {start_date}, End Date: {end_date}")

    # GENERATE DUMMY DATA TODO: Replace this with real data
    test_list = []
    for i in range(1785):
        dummy_dict = {
            "violation_date" : datetime.datetime.now().strftime("%Y.%m.%d - %H:%M:%S"),    
            "region_name": ''.join([random.choice(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]) for _ in range(5)]),
            "violation_type": random.choice(["Yasaklı Alan", "Baret Kuralı"]),
            "violation_score": str(int(random.random()*100)),
            "camera_uuid": str(uuid.uuid4()),
            "violation_uuid":str(uuid.uuid4())
        }

        test_list.append(dummy_dict)
    
    return {"list_": test_list}

#Run the application
if __name__ == "__main__":
    import uvicorn
    server_ip_address = input("Enter the server IP address: ")
    uvicorn.run(app, host=server_ip_address, port=80)
