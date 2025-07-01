import edge_tts
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
import easyocr
import numpy as np
import cv2
import re

app = FastAPI(
    title="k3",
    description="API untuk TTS",
)

reader = easyocr.Reader(['id'])

def split_image(img):
  height, width, _ = img.shape

  left_img = img[:, :width // 2]
  right_img = img[:, width // 2:]
  return left_img, right_img

def read_image(file: UploadFile):
    try:
        # Read the contents of the uploaded file into memory
        contents = file.file.read()
        # Convert the contents to a NumPy array
        np_arr = np.frombuffer(contents, np.uint8)
        # Decode the NumPy array into an image using OpenCV
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("File is not a valid image.")
            
        return img
    except Exception as e:
        raise ValueError(f"Failed to read or process uploaded image: {e}")

def clean_text(raw_text):
    # Ganti newline dengan spasi
    text = raw_text.replace('\n', ' ')

    # Lowercase
    text = text.lower()

    # Hapus karakter selain alphanum, spasi, dan .,!?-
    text = re.sub(r'[^a-z0-9.,!?\- ]+', '', text)

    # Rapikan spasi sebelum dan sesudah tanda baca
    text = re.sub(r'\s*([.,!?])\s*', r'\1 ', text)

    # Perbaiki spasi ganda
    text = re.sub(r'\s+', ' ', text)

    # Strip spasi di awal/akhir
    text = text.strip()

    return text

async def get_text(file: UploadFile):
    # read image
    img_1 = read_image(file)

    # split jadi 2
    left_img_1, right_img_1 = split_image(img_1)

    # Convert to RGB
    left_rgb = cv2.cvtColor(left_img_1, cv2.COLOR_BGR2RGB)
    right_rgb = cv2.cvtColor(right_img_1, cv2.COLOR_BGR2RGB)

    # Read both halves
    left_text = reader.readtext(left_rgb, detail=0, paragraph=True)
    right_text = reader.readtext(right_rgb, detail=0, paragraph=True)

    # Combine texts: left first, then right
    all_text = " ".join(left_text + right_text)
    cleaned_text = clean_text(all_text)
    return cleaned_text

async def get_audio(text):
    try:
        tts = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")
        await tts.save("output.mp3")
    except Exception as e:
        raise RuntimeError(f"Can't generate audio: {e}")

def delete_file(path: str):
    import os
    os.remove(path)
    
@app.post("/tts/")
async def predict_comments(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    file_path = "output.mp3"
    try:
        text = await get_text(image)
        await get_audio(text)
        background_tasks.add_task(delete_file, file_path)
        return FileResponse(file_path, media_type="audio/mpeg", filename=file_path)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
