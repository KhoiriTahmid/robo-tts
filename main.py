import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import easyocr
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

def read_image():
  img = cv2.imread("image.jpeg")

  if img is None:
    raise ValueError("Image not found or unreadable. Check the file path.")

  return img
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

async def get_text():
    # read image
    img_1 = read_image()

    # split jadi 2
    left_img_1, right_img_1 = split_image(img_1)

    # Convert to RGB
    left_rgb = cv2.cvtColor(left_img_1, cv2.COLOR_BGR2RGB)
    right_rgb = cv2.cvtColor(right_img_1, cv2.COLOR_BGR2RGB)

    # Read both halves
    reader = easyocr.Reader(['id'])  # 'id' for Indonesian
    left_text_1 = reader.readtext(left_rgb, detail=0, paragraph=True)
    right_text_1 = reader.readtext(right_rgb, detail=0, paragraph=True)

    # Combine texts: left first, then right
    all_text_1 = left_text_1[0] + right_text_1[0]
    cleaned_text_1 = clean_text(all_text_1)
    print(cleaned_text_1)
    return cleaned_text_1

async def get_audio(text):
    try:
        tts = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")
        await tts.save("output.mp3")
    except Exception as e:
        raise RuntimeError(f"Can't generate audio: {e}")

class TextInput(BaseModel):
  text:str

@app.post("/get_audio/")
async def predict_comments():
    file_path = "output.mp3"
    try:
        text = await get_text()
        await get_audio(text)
        return FileResponse(file_path, media_type="audio/mpeg", filename="output.mp3")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
