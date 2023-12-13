from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pymongo import MongoClient
from pydantic import BaseModel

router = APIRouter()

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
    id: int
    hashed_password: str

class User(UserBase):
    id: int

class UserInResponse(User):
    token: Token

class UserResponse(BaseModel):
    username: str
    role: str
    id: int

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

def get_user(user_collection, username: str):
    user_data = user_collection.find_one({"username": username})
    if user_data:
        return UserInDB(**user_data)

def get_user_by_id(user_collection, user_id: int):
    user_data = user_collection.find_one({"_id": user_id})
    if user_data:
        user_data["id"] = user_data.pop("_id")
        return UserInDB(**user_data)

def authenticate_user(user_collection, username: str, password: str):
    user = get_user(user_collection, username)
    if user and verify_password(password, user.hashed_password):
        return user

def create_user(user_collection, user: UserCreate):
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user.password)
    user_dict.pop("password")

    if user.role == "siswa" and user.siswa_id:
        siswa = siswa_collection.find_one({"siswa_id": user.siswa_id})
        if not siswa:
            raise HTTPException(status_code=400, detail="Invalid siswa_id")

    user_id = user_collection.insert_one(user_dict).inserted_id
    user_data = user_collection.find_one({"_id": user_id})
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
        user = get_user(user_collection, username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

async def get_current_active_user(current_user: TokenData = Depends(get_current_user)):
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(user_collection, form_data.username, form_data.password)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, role=current_user.role)

@router.post("/register/", response_model=Token)
async def register_user(new_user: UserCreate):
    try:
        existing_user = get_user(user_collection, new_user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        last_user = user_collection.find_one(sort=[("_id", -1)])
        last_user_id = last_user["_id"] if last_user else 0

        hashed_password = get_password_hash(new_user.password)

        user_data = {
            "username": new_user.username,
            "role": new_user.role,
            "siswa_id": new_user.siswa_id,
            "hashed_password": hashed_password,
            "_id": last_user_id + 1,
        }

        user_collection.insert_one(user_data)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data["username"]}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"Error occurred during user registration: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user, please try again later")
    