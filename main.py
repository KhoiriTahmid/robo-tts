import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="k3",
    description="API untuk TTS",
)

async def get_audio(text):
    try:
        tts = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")
        await tts.save("output.mp3")
    except Exception as e:
        raise RuntimeError(f"Can't generate audio: {e}")

class TextInput(BaseModel):
  text:str

@app.post("/get_audio/")
async def predict_comments(input: TextInput):
    file_path = "output.mp3"
    try:
        await get_audio(input.text)
        return FileResponse(file_path, media_type="audio/mpeg", filename="output.mp3")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
