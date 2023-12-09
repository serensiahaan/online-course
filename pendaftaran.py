from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import auth

router = APIRouter()

class Pendaftaran(BaseModel):
    pendaftaran_id: int
    nama: str
    sekolah: str
    kelas: int
    subject: str
    day: str

client = MongoClient("mongodb+srv://owner:owner@onlinecourse.uzzj2ih.mongodb.net/")
db = client["onlinecourse"]
pendaftaran_collection = db["pendaftaran_data"]
kelas_collection = db["kelas_data"]

def convert_id(item):
    item['_id'] = str(item['_id'])
    return item

@router.get('/pendaftaran')
async def read_all_pendaftaran(current_user: auth.User = Depends(auth.get_current_active_user)):
    return list(map(convert_id, pendaftaran_data.find()))

@router.get('/pendaftaran/{pendaftaran_id}')
async def read_pendaftaran(pendaftaran_id: str, current_user: auth.User = Depends(auth.get_current_active_user)):
    pendaftaran = pendaftaran_data.find_one({"_id": ObjectId(pendaftaran_id)})
    if pendaftaran:
        return convert_id(pendaftaran)
    raise HTTPException(status_code=404, detail=f'Pendaftaran with ID {pendaftaran_id} not found')

@router.post('/pendaftaran')
async def add_pendaftaran(pendaftaran: dict):
    kelas_id = pendaftaran.get("kelas")
    kelas_info = kelas_data.find_one({"_id": ObjectId(kelas_id)})

    if not kelas_info:
        raise HTTPException(status_code=404, detail=f'Kelas with ID {kelas_id} not found')

    pendaftaran["subject"] = kelas_info.get("subject")
    pendaftaran["day"] = kelas_info.get("day")

    # Incremental ID logic
    last_pendaftaran = pendaftaran_data.find_one(sort=[("_id", -1)])
    new_id = 1 if not last_pendaftaran else last_pendaftaran["_id"] + 1
    pendaftaran["_id"] = new_id

    inserted_id = pendaftaran_data.insert_one(pendaftaran).inserted_id
    if inserted_id:
        new_pendaftaran = pendaftaran_data.find_one({"_id": ObjectId(inserted_id)})
        return convert_id(new_pendaftaran)

    raise HTTPException(status_code=404, detail='Failed to add item')

@router.put('/pendaftaran/{pendaftaran_id}')
async def update_pendaftaran(pendaftaran_id: str, pendaftaran: dict, current_user: auth.User = Depends(auth.get_current_active_user)):
    kelas_id = pendaftaran.get("kelas")
    kelas_info = kelas_data.find_one({"_id": ObjectId(kelas_id)})

    if not kelas_info:
        raise HTTPException(status_code=404, detail=f'Kelas with ID {kelas_id} not found')

    pendaftaran["subject"] = kelas_info.get("subject")
    pendaftaran["day"] = kelas_info.get("day")

    result = pendaftaran_data.replace_one({"_id": ObjectId(pendaftaran_id)}, pendaftaran)
    if result.modified_count > 0:
        return "Updated"

    raise HTTPException(status_code=404, detail=f'Pendaftaran with ID {pendaftaran_id} not found')

@router.delete('/pendaftaran/{pendaftaran_id}')
async def delete_pendaftaran(pendaftaran_id: str, current_user: auth.User = Depends(auth.get_current_active_user)):
    result = pendaftaran_data.delete_one({"_id": ObjectId(pendaftaran_id)})
    if result.deleted_count > 0:
        return "Deleted"
    raise HTTPException(status_code=404, detail=f'Pendaftaran with ID {pendaftaran_id} not found')
