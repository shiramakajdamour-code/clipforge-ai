from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import os
from app.tasks.worker import process_video
import aiofiles

router = APIRouter()
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file and start processing
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Validate file size (500MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 500 * 1024 * 1024:  # 500MB in bytes
        raise HTTPException(status_code=400, detail="File too large (max 500MB)")
    
    # Reset file position after reading
    await file.seek(0)
    
    # Generate unique filename
    video_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Validate extension
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
    if file_ext not in valid_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Supported: {valid_extensions}")
    
    filepath = os.path.join(UPLOAD_DIR, f"{video_id}{file_ext}")
    
    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Start async processing
    task = process_video.delay(filepath)
    
    return {
        "video_id": video_id,
        "filename": file.filename,
        "file_size": file_size,
        "task_id": task.id,
        "status": "processing",
        "message": "Video uploaded successfully. Processing started."
    }

@router.get("/status/{task_id}")
async def get_upload_status(task_id: str):
    """
    Get status of an upload task
    """
    from celery.result import AsyncResult
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.ready():
        response["result"] = task_result.result
    
    return response
