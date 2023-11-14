from fastapi import FastAPI, Depends, HTTPException, status
import json
from pydantic import BaseModel
from typing import Dict,List,Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

app = FastAPI()

class Admission(BaseModel):
	id: int
	nama: str
	kelas: str
	sekolah: int
    jurusan: str
    pelajaran: str
    hari: str
    sesi: str

json_filename="admission.json"

with open(json_filename,"r") as read_file:
	data = json.load(read_file)

@app.post('/')
async def new_admission(admission: Admission):
	admission_dict = dict(admission)
    admission_data['admissions'].append(admission_dict)

	with open(json_filename, "w") as write_file: 
		json.dump(admission_data, write_file)

	return "Pendaftaran telah terkirim!"
    
@app.get('/')
async def admission_list(): 
	return admission_data

@app.get('/admissions/{nama}')
async def find_admission(nama : str): 
    for existing_admission in admission_data['admissions']:
        if existing_admission['name'] == name:
            return existing_admission



# Replace these with your own secret key and algorithm
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# FastAPI app
app = FastAPI()

# OAuth2 settings
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Users database (in-memory for this example)
users_db = {}

# JWT settings
JWT_EXPIRATION = timedelta(minutes=15)

# Function to verify user credentials
def verify_user(db, username: str, password: str):
    user = db.get(username)
    if user and pwd_context.verify(password, user["hashed_password"]):
        return user

# Function to create JWT token
def create_jwt_token(data: dict):
    expire = datetime.utcnow() + JWT_EXPIRATION
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to get current user from JWT token
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = {"sub": username}
    except JWTError:
        raise credentials_exception
    return token_data

# Route to generate JWT token
@app.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = verify_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = {"sub": form_data.username}
    access_token = create_jwt_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route requiring OAuth2 token
@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user}
