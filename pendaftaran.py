from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import auth

router = APIRouter()

class Pendaftaran(BaseModel):
    nama: str
    sekolah: str
    kelas: int
    subject: str
    day: str

client = MongoClient("mongodb+srv://owner:owner@onlinecourse.uzzj2ih.mongodb.net/")
db = client["onlinecourse"]
pendaftaran_data = db["pendaftaran_data"]

def convert_id(item):
    item['_id'] = str(item['_id'])
    return item

def check_owner_permissions(current_user: auth.User = Depends(auth.get_current_active_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Not enough permissions")

@router.get('/pendaftaran', response_model=list[Pendaftaran])
async def read_all_pendaftaran(current_user: auth.User = Depends(auth.get_current_active_user)):
    check_owner_permissions(current_user)
    return list(map(convert_id, pendaftaran_data.find()))

@router.get('/pendaftaran/{pendaftaran_id}', response_model=Pendaftaran)
async def read_pendaftaran(pendaftaran_id: str, current_user: auth.User = Depends(auth.get_current_active_user)):
    check_owner_permissions(current_user)
    pendaftaran = pendaftaran_data.find_one({"_id": ObjectId(pendaftaran_id)})
    if pendaftaran:
        return convert_id(pendaftaran)
    raise HTTPException(status_code=404, detail=f'Pendaftaran with ID {pendaftaran_id} not found')

@router.post('/pendaftaran/add', response_model=Pendaftaran)
async def add_pendaftaran(pendaftaran: Pendaftaran):
    last_pendaftaran = pendaftaran_data.find_one(sort=[("_id", -1)])
    new_id = 1 if not last_pendaftaran else last_pendaftaran["_id"] + 1

    pendaftaran_data.insert_one({"pendaftaran_id": new_id, **pendaftaran.dict()})

    new_pendaftaran = pendaftaran_data.find_one({"pendaftaran_id": new_id})
    return convert_id(new_pendaftaran)

@router.put('/pendaftaran/update/{pendaftaran_id}')
async def update_pendaftaran(pendaftaran_id: str, pendaftaran: dict, current_user: auth.User = Depends(auth.get_current_active_user)):
    check_owner_permissions(current_user)

    result = pendaftaran_data.replace_one({"_id": ObjectId(pendaftaran_id)}, pendaftaran)
    if result.modified_count > 0:
        return "Updated"
    raise HTTPException(status_code=404, detail=f'Pendaftaran with ID {pendaftaran_id} not found')

@router.delete('/pendaftaran/delete/{pendaftaran_id}')
async def delete_pendaftaran(pendaftaran_id: str, current_user: auth.User = Depends(auth.get_current_active_user)):
    check_owner_permissions(current_user)
    result = pendaftaran_data.delete_one({"_id": ObjectId(pendaftaran_id)})
    if result.deleted_count > 0:
        return "Deleted"
    raise HTTPException(status_code=404, detail=f'Pendaftaran with ID {pendaftaran_id} not found')
