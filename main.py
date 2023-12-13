from fastapi import FastAPI
from pendaftaran import router as pendaftaran_router
from kelas import router as kelas_router
from siswa import router as siswa_router
from guru import router as guru_router
from auth import router as auth_router

app = FastAPI()

origins = ["*"]

app.include_router(auth_router)
app.include_router(pendaftaran_router)
app.include_router(kelas_router)
app.include_router(siswa_router)
app.include_router(guru_router)

@app.get('/')
async def homepage():
    return {"message": "Mari belajar bersama kami!"}
