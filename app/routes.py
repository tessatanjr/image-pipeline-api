from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.services.image_service import process_image, list_images, get_image
from app.services.database_service import get_processing_stats
import json

router = APIRouter()

def format_image_response(image: dict):
    exif_raw = image.get("exif")
    if exif_raw:
        try:
            exif = json.loads(exif_raw)
        except json.JSONDecodeError:
            exif = {}
    else:
        exif = {}
    return {
        "image_id": image["id"],
        "original_name": image["filename"],
        "processed_at": image.get("processed_at"),
        "metadata": {
            "width": image.get("width"),
            "height": image.get("height"),
            "format": image.get("format"),
            "size_bytes": image.get("size_bytes")
        },
        "thumbnails": {
            "small": image.get("small_thumb"),
            "medium": image.get("medium_thumb")
        },
        "caption": image.get("caption"),
        "exif": exif
    }

@router.post("/images")
async def upload_image(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    image_id = await process_image(file, background_tasks)
    return {
        "status": "success",
        "data": {
            "image_id": image_id,
            "original_name": file.filename
        },
        "error": None
    }

@router.get("/images")
async def get_all_images():
    images = list_images()
    data = [format_image_response(img) for img in images]
    return {"status": "success", "data": data, "error": None}

@router.get("/images/{image_id}")
async def get_image_by_id(image_id: str):
    image = get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    data = format_image_response(image)
    return {"status": "success", "data": data, "error": None}

@router.get("/images/{image_id}/thumbnails/{size}")
async def get_thumbnail(image_id: str, size: str):
    image = get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if size == "small":
        thumb_path = Path(image["small_thumb"])
    elif size == "medium":
        thumb_path = Path(image["medium_thumb"])
    else:
        raise HTTPException(status_code=400, detail="Invalid size, choose 'small' or 'medium'")

    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(thumb_path)

@router.get("/stats")
async def get_stats():
    stats = get_processing_stats()
    return {
        "status": "success",
        "data": stats,
        "error": None
    }
