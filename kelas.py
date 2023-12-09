from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import auth

app = APIRouter()

client = MongoClient("mongodb+srv://owner:owner@onlinecourse.uzzj2ih.mongodb.net/")
db = client["onlinecourse"]
kelas_collection = db["kelas_data"]
guru_collection = db["guru_data"]

class Kelas(BaseModel):
    kelas_id: int
    name: str
    subject: str
    guru_id: int
    day: str
    session_start: str

def convert_id(kelas):
    kelas['_id'] = str(kelas['_id'])
    return kelas

def check_owner_permissions(current_user: auth.User = Depends(auth.get_current_active_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Not enough permissions")

@app.get('/kelas')
async def read_all_kelas(current_user: auth.User = Depends(auth.get_current_active_user)):
    auth.check_owner_permissions(current_user)
    return list(map(convert_id, kelas_collection.find()))

@app.get('/kelas/{kelas_id}')
async def read_kelas(kelas_id: int, current_user: auth.User = Depends(auth.get_current_active_user)):
    auth.check_owner_permissions(current_user)
    kelas = kelas_collection.find_one({"id": kelas_id})
    if kelas:
        return convert_id(kelas)
    raise HTTPException(status_code=404, detail=f'Class with ID {kelas_id} not found')

@app.post('/kelas')
async def create_kelas(kelas: Kelas, current_user: auth.User = Depends(auth.get_current_active_user)):
    auth.check_owner_permissions(current_user)
    kelas_dict = kelas.dict()

    guru_id = kelas_dict['guru_id']
    guru = guru_collection.find_one({"id": guru_id, "subject": kelas_dict['subject'], "day": kelas_dict['day']})
    if not guru:
        raise HTTPException(status_code=404, detail=f'Guru with ID {guru_id} not found or does not match subject and day')

    kelas_dict['guru_name'] = guru['name']

    inserted_id = kelas_collection.insert_one(kelas_dict).inserted_id

    if inserted_id:
        new_kelas = kelas_collection.find_one({"_id": inserted_id})
        return convert_id(new_kelas)

    raise HTTPException(status_code=404, detail='Failed to add class')

@app.put('/kelas/{kelas_id}')
async def update_kelas(kelas_id: int, kelas: Kelas, current_user: auth.User = Depends(auth.get_current_active_user)):
    auth.check_owner_permissions(current_user)
    kelas_dict = kelas.dict()

    guru_id = kelas_dict['guru_id']
    guru = guru_collection.find_one({"id": guru_id, "subject": kelas_dict['subject'], "day": kelas_dict['day']})
    if not guru:
        raise HTTPException(status_code=404, detail=f'Guru with ID {guru_id} not found or does not match subject and day')

    kelas_dict['guru_name'] = guru['name']

    result = kelas_collection.replace_one({"id": kelas_id}, kelas_dict)

    if result.modified_count > 0:
        return "Updated"

    return "Class not found."

@app.delete('/kelas/{kelas_id}')
async def delete_kelas(kelas_id: int, current_user: auth.User = Depends(auth.get_current_active_user)):
    auth.check_owner_permissions(current_user)
    result = kelas_collection.delete_one({"id": kelas_id})

    if result.deleted_count > 0:
        return "Deleted"

    return "Class not found."
