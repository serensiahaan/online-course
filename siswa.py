from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import auth

router = APIRouter()

class Siswa(BaseModel):
    siswa_id: int
    nama: str
    sekolah: str
    kelas: int
    subject: str
    day: str
    nilaimatm: int | None = None
    nilaimatw: int | None = None
    nilaifis: int | None = None
    nilaikim: int | None = None
    nilaibio: int | None = None
    nilaiind: int | None = None
    nilaiing: int | None = None

client = MongoClient("mongodb+srv://owner:owner@onlinecourse.uzzj2ih.mongodb.net/")
db = client["onlinecourse"]
siswa_collection = db["siswa_data"]
pendaftaran_collection = db["pendaftaran_data"]
kelas_collection = db["kelas_data"]

def convert_id(siswa):
    siswa['_id'] = str(siswa['_id'])
    return siswa

@router.get('/siswa', response_model=list[Siswa])
async def read_all_siswa(current_user: auth.User = Depends(auth.get_current_active_user)):
    return list(map(convert_id, siswa_collection.find()))

@router.get('/siswa/{siswa_id}')
async def read_siswa(siswa_id: int, current_user: auth.User = Depends(auth.get_current_active_user)):
    siswa = siswa_collection.find_one({"siswa_id": siswa_id})
    if siswa:
        return convert_id(siswa)
    raise HTTPException(status_code=404, detail=f'Siswa with ID {siswa_id} not found')

@router.post('/siswa', response_model=Siswa)
async def add_siswa(siswa: Siswa, current_user: auth.User = Depends(auth.get_current_active_user)):
    # Logic to check if a siswa with the same pendaftaran_id already exists
    existing_siswa = siswa_collection.find_one({"pendaftaran_id": siswa.pendaftaran_id})
    if existing_siswa:
        raise HTTPException(status_code=400, detail=f"Siswa for Pendaftaran ID '{siswa.pendaftaran_id}' already exists.")
    
    # Insert the siswa data into the collection
    inserted_id = siswa_collection.insert_one(siswa.dict()).inserted_id
    if inserted_id:
        # Retrieve the inserted document to return
        new_siswa = siswa_collection.find_one({"_id": inserted_id})
        return convert_id(new_siswa)
    
    raise HTTPException(status_code=500, detail='Failed to add siswa')

@router.put('/siswa', response_model=Siswa)
async def update_siswa(siswa: Siswa, current_user: auth.User = Depends(auth.get_current_active_user)):
    # Logic to check if a siswa with the same pendaftaran_id already exists (excluding the siswa being updated)
    existing_siswa = siswa_collection.find_one({"pendaftaran_id": siswa.pendaftaran_id, "id": {"$ne": siswa.id}})
    if existing_siswa:
        raise HTTPException(status_code=400, detail=f"Siswa for Pendaftaran ID '{siswa.pendaftaran_id}' already exists.")
    
    # Update the siswa data in the collection
    result = siswa_collection.replace_one({"siswa_id": siswa.siswa_id}, siswa.dict())
    if result.modified_count > 0:
        return convert_id(siswa)
    
    raise HTTPException(status_code=404, detail="Siswa not found.")

@router.delete('/siswa/{siswa_id}')
async def delete_siswa(siswa_id: int, current_user: auth.User = Depends(auth.get_current_active_user)):
    result = siswa_collection.delete_one({"siswa_id": siswa_id})
    if result.deleted_count > 0:
        return "Deleted"
    
    raise HTTPException(status_code=404, detail="Siswa not found.")

