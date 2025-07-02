import edge_tts
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pytesseract
import numpy as np
import cv2
import re
import os

# --- Inisialisasi Aplikasi FastAPI ---
app = FastAPI(
    title="API Ekstraksi Teks dan Text-to-Speech",
    description="API dengan dua endpoint: satu untuk ekstraksi teks dari gambar, satu lagi untuk konversi teks ke suara.",
    version="2.0",
)

# --- Pydantic Model untuk Menerima Input Teks ---
class TextPayload(BaseModel):
    """Model untuk menerima payload teks dalam request body."""
    text: str

# --- Fungsi Helper (Tidak ada perubahan signifikan) ---

def split_image(img):
    height, width, _ = img.shape
    left_img = img[:, :width // 2]
    right_img = img[:, width // 2:]
    return left_img, right_img

def read_image(file: UploadFile):
    try:
        contents = file.file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("File yang diunggah bukan gambar yang valid.")
        return img
    except Exception as e:
        raise ValueError(f"Gagal membaca atau memproses gambar: {e}")

def clean_text(raw_text):
    text = raw_text.replace('\n', ' ')
    text = text.lower()
    text = re.sub(r'[^a-z0-9.,!?\- ]+', '', text)
    text = re.sub(r'\s*([.,!?])\s*', r'\1 ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

# --- Fungsi untuk Membersihkan File ---
def cleanup_file(path: str):
    """Menghapus file jika ada setelah response dikirim."""
    if os.path.exists(path):
        os.remove(path)

# --- ENDPOINT 1: GAMBAR KE TEKS ---
@app.post("/extract-text/", response_class=JSONResponse)
async def extract_text_from_image(image: UploadFile = File(...)):
    """
    Menerima input gambar dan mengembalikan teks yang diekstraksi dalam format JSON.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File yang diberikan bukan gambar.")
    
    try:
        img = read_image(image)
        left_img, right_img = split_image(img)
        text_left = pytesseract.image_to_string(left_img)
        text_right = pytesseract.image_to_string(right_img)
        
        full_text = text_left + " " + text_right
        final_text = clean_text(full_text)
        
        return {"extracted_text": final_text}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}")

# --- ENDPOINT 2: TEKS KE SUARA ---
@app.post("/generate-audio/", response_class=FileResponse)
async def generate_audio_from_text(payload: TextPayload, background_tasks: BackgroundTasks):
    """
    Menerima input teks (JSON) dan mengembalikan file audio MP3.
    """
    file_path = "output.mp3"
    
    # Menjadwalkan file untuk dihapus setelah response dikirim
    background_tasks.add_task(cleanup_file, file_path)
    
    try:
        # Membuat objek Communicate untuk TTS
        communicate = edge_tts.Communicate(payload.text, "id-ID-ArdiNeural")
        # Menyimpan file audio
        await communicate.save(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat file audio: {e}")
        
    return FileResponse(file_path, media_type="audio/mpeg", filename="output.mp3")
