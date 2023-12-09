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

@router.get('/guru')
async def read_all_guru(current_user: auth.User = Depends(auth.get_current_active_user)):
    return list(map(convert_id, guru_collection.find()))

@router.get('/guru/{guru_id}')
async def read_guru(id: int, current_user: auth.User = Depends(auth.get_current_active_user)):
    guru = guru_collection.find_one({"id": id})
    if guru:
        return convert_id(guru)
    raise HTTPException(status_code=404, detail=f'Guru with ID {id} not found')

@router.post('/guru')
async def add_guru(guru: Guru, current_user: auth.User = Depends(auth.get_current_active_user)):
    # Logic to check if a guru with the same subject and day already exists
    existing_guru = guru_collection.find_one({"subject": guru.subject, "day": guru.day})
    if existing_guru:
        raise HTTPException(status_code=400, detail=f"Guru for subject '{guru.subject}' on day '{guru.day}' already exists.")
    
    # Insert the guru data into the collection
    inserted_id = guru_collection.insert_one(guru.dict()).inserted_id
    if inserted_id:
        # Retrieve the inserted document to return
        new_guru = guru_collection.find_one({"_id": inserted_id})
        return convert_id(new_guru)
    
    raise HTTPException(status_code=500, detail='Failed to add guru')

@router.put('/guru')
async def update_guru(guru: Guru, current_user: auth.User = Depends(auth.get_current_active_user)):
    # Logic to check if a guru with the same subject and day already exists (excluding the guru being updated)
    existing_guru = guru_collection.find_one({"subject": guru.subject, "day": guru.day, "id": {"$ne": guru.id}})
    if existing_guru:
        raise HTTPException(status_code=400, detail=f"Guru for subject '{guru.subject}' on day '{guru.day}' already exists.")
    
    # Update the guru data in the collection
    result = guru_collection.replace_one({"id": guru.id}, guru.dict())
    if result.modified_count > 0:
        return convert_id(guru)
    
    raise HTTPException(status_code=404, detail="Guru not found.")

@router.delete('/guru/{guru_id}')
async def delete_guru(id: int, current_user: auth.User = Depends(auth.get_current_active_user)):
    result = guru_collection.delete_one({"id": id})
    if result.deleted_count > 0:
        return "Deleted"
    
    raise HTTPException(status_code=404, detail="Guru not found.")
