from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from typing import Optional

router = APIRouter()

# Base directories
CLIPS_DIR = "./clips"
THUMBNAILS_DIR = "./thumbnails"
CAPTIONS_DIR = "./captions"
VOICEOVERS_DIR = "./voiceovers"

@router.get("/{video_id}")
async def get_video_clips(video_id: str):
    """
    Get all clips for a specific video
    """
    video_clips_dir = os.path.join(CLIPS_DIR, video_id)
    
    if not os.path.exists(video_clips_dir):
        raise HTTPException(status_code=404, detail="Video not found")
    
    clips = []
    for filename in os.listdir(video_clips_dir):
        if filename.endswith('.mp4'):
            file_path = os.path.join(video_clips_dir, filename)
            file_stats = os.stat(file_path)
            
            clips.append({
                "filename": filename,
                "path": f"/clips/file/{video_id}/{filename}",
                "size": file_stats.st_size,
                "created": file_stats.st_ctime,
                "type": "teaser" if "teaser" in filename else "standard" if "standard" in filename else "explainer" if "explainer" in filename else "unknown"
            })
    
    return {
        "video_id": video_id,
        "total_clips": len(clips),
        "clips": clips
    }

@router.get("/file/{video_id}/{filename}")
async def get_clip_file(video_id: str, filename: str):
    """
    Serve a specific clip file
    """
    file_path = os.path.join(CLIPS_DIR, video_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename
    )

@router.get("/thumbnails/{video_id}")
async def get_thumbnails(video_id: str, clip_id: Optional[int] = None):
    """
    Get thumbnails for a video or specific clip
    """
    video_thumbs_dir = os.path.join(THUMBNAILS_DIR, video_id)
    
    if not os.path.exists(video_thumbs_dir):
        raise HTTPException(status_code=404, detail="Thumbnails not found")
    
    thumbnails = []
    for filename in os.listdir(video_thumbs_dir):
        if filename.endswith('.jpg') and not filename.endswith('_web.jpg'):
            if clip_id and f"clip_{clip_id}" not in filename:
                continue
                
            file_path = os.path.join(video_thumbs_dir, filename)
            web_path = file_path.replace('.jpg', '_web.jpg')
            file_stats = os.stat(file_path)
            
            thumbnails.append({
                "filename": filename,
                "path": f"/thumbnails/file/{video_id}/{filename}",
                "web_path": f"/thumbnails/file/{video_id}/{filename.replace('.jpg', '_web.jpg')}" if os.path.exists(web_path) else None,
                "size": file_stats.st_size,
                "created": file_stats.st_ctime
            })
    
    return {
        "video_id": video_id,
        "total_thumbnails": len(thumbnails),
        "thumbnails": thumbnails
    }

@router.get("/thumbnails/file/{video_id}/{filename}")
async def get_thumbnail_file(video_id: str, filename: str):
    """
    Serve a specific thumbnail file
    """
    file_path = os.path.join(THUMBNAILS_DIR, video_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="image/jpeg",
        filename=filename
    )

@router.get("/captions/{video_id}")
async def get_captions(video_id: str):
    """
    Get captions for a video
    """
    captions_path = os.path.join(CAPTIONS_DIR, f"{video_id}.srt")
    
    if not os.path.exists(captions_path):
        raise HTTPException(status_code=404, detail="Captions not found")
    
    return FileResponse(
        captions_path,
        media_type="text/plain",
        filename=f"{video_id}_captions.srt"
    )

@router.get("/voiceovers/{video_id}")
async def get_voiceovers(video_id: str, clip_id: Optional[int] = None):
    """
    Get voiceovers for a video
    """
    video_voiceovers_dir = os.path.join(VOICEOVERS_DIR, video_id)
    
    if not os.path.exists(video_voiceovers_dir):
        raise HTTPException(status_code=404, detail="Voiceovers not found")
    
    voiceovers = []
    for filename in os.listdir(video_voiceovers_dir):
        if filename.endswith('.mp3'):
            if clip_id and f"clip_{clip_id}" not in filename:
                continue
                
            file_path = os.path.join(video_voiceovers_dir, filename)
            file_stats = os.stat(file_path)
            
            # Extract style from filename
            style = "unknown"
            if "solo" in filename:
                style = "solo"
            elif "dual_host" in filename:
                style = "dual_host"
            elif "interview" in filename:
                style = "interview"
            elif "debate" in filename:
                style = "debate"
            elif "storytelling" in filename:
                style = "storytelling"
            
            voiceovers.append({
                "filename": filename,
                "path": f"/voiceovers/file/{video_id}/{filename}",
                "style": style,
                "size": file_stats.st_size,
                "created": file_stats.st_ctime
            })
    
    return {
        "video_id": video_id,
        "total_voiceovers": len(voiceovers),
        "voiceovers": voiceovers
    }

@router.get("/voiceovers/file/{video_id}/{filename}")
async def get_voiceover_file(video_id: str, filename: str):
    """
    Serve a specific voiceover file
    """
    file_path = os.path.join(VOICEOVERS_DIR, video_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=filename
  )
