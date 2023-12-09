from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import auth

router = APIRouter()

class Guru(BaseModel):
    guru_id: int
    name: str
    subject: str
    day: str

client = MongoClient("mongodb+srv://owner:owner@onlinecourse.uzzj2ih.mongodb.net/")
db = client["onlinecourse"]
guru_collection = db["guru_data"]

def convert_id(guru):
    guru['_id'] = str(guru['_id'])
    return guru

def check_owner_permissions(current_user: auth.User = Depends(auth.get_current_active_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Not enough permissions")

@router.get('/guru')
async def read_all_guru(current_user: auth.User = Depends(check_owner_permissions)):
    return list(map(convert_id, guru_collection.find()))

@router.get('/guru/{guru_id}')
async def read_guru(guru_id: int, current_user: auth.User = Depends(check_owner_permissions)):
    guru = guru_collection.find_one({"id": guru_id})
    if guru:
        return convert_id(guru)
    raise HTTPException(status_code=404, detail=f'Guru with ID {guru_id} not found')

@router.post('/guru')
async def add_guru(guru: Guru, current_user: auth.User = Depends(check_owner_permissions)):
    existing_guru = guru_collection.find_one({"subject": guru.subject, "day": guru.day})
    if existing_guru:
        raise HTTPException(status_code=400, detail=f"Guru for subject '{guru.subject}' on day '{guru.day}' already exists.")

    inserted_id = guru_collection.insert_one(guru.dict()).inserted_id
    if inserted_id:
        new_guru = guru_collection.find_one({"_id": inserted_id})
        return convert_id(new_guru)
    
    raise HTTPException(status_code=500, detail='Failed to add guru')

@router.put('/guru')
async def update_guru(guru: Guru, current_user: auth.User = Depends(check_owner_permissions)):
    existing_guru = guru_collection.find_one({"subject": guru.subject, "day": guru.day, "id": {"$ne": guru.id}})
    if existing_guru:
        raise HTTPException(status_code=400, detail=f"Guru for subject '{guru.subject}' on day '{guru.day}' already exists.")
    
    result = guru_collection.replace_one({"id": guru.id}, guru.dict())
    if result.modified_count > 0:
        return convert_id(guru)
    
    raise HTTPException(status_code=404, detail="Guru not found.")

@router.delete('/guru/{guru_id}')
async def delete_guru(guru_id: int, current_user: auth.User = Depends(check_owner_permissions)):
    result = guru_collection.delete_one({"id": guru_id})
    if result.deleted_count > 0:
        return "Deleted"
    
    raise HTTPException(status_code=404, detail="Guru not found.")
