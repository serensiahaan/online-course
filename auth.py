from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pymongo import MongoClient
from pydantic import BaseModel

client = MongoClient("mongodb+srv://owner:owner@onlinecourse.uzzj2ih.mongodb.net/")
db = client["onlinecourse"]
user_collection = db["user_data"]
siswa_collection = db["siswa_data"]

# Username Owner untuk operasi CRUD : owner
# Password Owner : ownerpassword

SECRET_KEY = "082293011deef0c73bf84d15a5b9e806498897df"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    password: str
    siswa_id: Optional[int] = None

class UserInDB(UserBase):
    hashed_password: str

class User(UserBase):
    id: int

class UserInResponse(User):
    token: Token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db, username: str):
    user_data = db.find_one({"username": username})
    if user_data:
        return UserInDB(**user_data)

def get_user_by_id(db, user_id: int):
    user_data = db.find_one({"_id": user_id})
    if user_data:
        return UserInDB(**user_data)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if user and verify_password(password, user.hashed_password):
        return user

def create_user(db, user: UserCreate):
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user.password)
    user_dict.pop("password")

    if user.role == "siswa" and user.siswa_id:
        siswa = siswa_collection.find_one({"siswa_id": user.siswa_id})
        if not siswa:
            raise HTTPException(status_code=400, detail="Invalid siswa_id")
        
    if user.role == "owner":
        existing_owner = db.find_one({"username": "owner"})
        if existing_owner:
            raise HTTPException(status_code=400, detail="Owner already exists")

    user_id = db.insert_one(user_dict).inserted_id
    user_data = db.find_one({"_id": user_id})
    return UserInDB(**user_data)

async def get_current_user(token: str = Depends(oauth2_scheme)):
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
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.role == "owner" or current_user.role == "siswa":
        return current_user
    raise HTTPException(status_code=403, detail="Not enough permissions")
