from fastapi import FastAPI, Depends, HTTPException, APIRouter
from pydantic import BaseModel
import auth
from data import admission

router = APIRouter()

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

@router.post('/')
async def new_admission(admission: Admission):
	admission_dict = drivers.dict()
    admission_data['admissions'].append(admission_dict)

	with open(json_filename, "w") as write_file: 
		json.dump(admission_data, write_file)

	return "Pendaftaran telah terkirim!"
    
@router.get('/')
async def admission_list(current_user: User = Depends(get_current_active_user)): 
	return admission_data['admissions']

@router.get('/admissions/{nama}')
async def find_admission(nama : str, current_user: User = Depends(get_current_active_user)): 
    for existing_admission in admission_data['admissions']:
        if existing_admission['name'] == name:
            return existing_admission
    raise HTTPException(
		status_code=404, detail=f'Pendaftaran tidak ditemukan'
	)

@router.delete('/admissions/{id}')
async def delete_menu(id: int, current_user: User = Depends(get_current_active_user)):
	for idx, admission_item in enumerate(data['admission']):
		if admission_item['id'] == id:
			existing_admission['admissions'].pop(idx)
			
			with open(json_filename,"w") as write_file:
				json.dump(data, write_file)
			return "admission deleted"
	raise HTTPException(
		status_code=404, detail=f'Pendaftaran tidak ditemukan'
	)
