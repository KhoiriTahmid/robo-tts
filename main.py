import edge_tts
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
import pytesseract
import numpy as np
import cv2
import re

app = FastAPI(
    title="k3",
    description="API untuk TTS",
)
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
    img_2 = read_image(file)

    # split jadi 2
    left_img_2, right_img_2 = split_image(img_2)

    # Step 4: Perform OCR
    text_left_2 = pytesseract.image_to_string(left_img_2)
    text_right_2 = pytesseract.image_to_string(right_img_2)

    all_text_2 = text_left_2 + text_right_2
    final = clean_text(all_text_2)
    print(final)
    return final

async def get_audio(text):
    try:
        tts = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")
        await tts.save("output.mp3")
    except Exception as e:
        raise RuntimeError(f"Can't generate audio: {e}")

@app.post("/get_audio/")
async def predict_comments(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    file_path = "output.mp3"
    try:
        text = await get_text(image)
        await get_audio(text)
        return FileResponse(file_path, media_type="audio/mpeg", filename="output.mp3")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
