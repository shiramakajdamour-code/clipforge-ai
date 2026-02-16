from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.tasks.worker import process_video
import uuid
import os
import aiofiles
from celery.result import AsyncResult

app = FastAPI(title="ClipForge AI")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Start processing task
    task = process_video.delay(file_path)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "task_id": task.id,
        "status": "processing"
    }

@app.get("/api/status/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id)
    
    result = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    
    return JSONResponse(content=result)
