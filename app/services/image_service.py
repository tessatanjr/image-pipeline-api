import uuid
from fastapi import UploadFile, BackgroundTasks
from pathlib import Path
from PIL import Image, ExifTags
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
from app.services.database_service import insert_image, get_all_images, get_image_by_id, update_image_metadata, update_image_thumbnails, update_image_caption, update_image_status, update_image_exif, mark_image_processed

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large").to(device)


UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

THUMB_SIZES = {
    "small": (128, 128),
    "medium": (512, 512)
}

def extract_exif(file_path: Path):
    img = Image.open(file_path)
    exif_data = {}
    if hasattr(img, "_getexif"):
        exifinfo = img._getexif()
        if exifinfo:
            for tag, value in exifinfo.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if hasattr(value, "numerator") and hasattr(value, "denominator"):
                    value = float(value)
                elif isinstance(value, bytes):
                    try:
                        value = value.decode(errors="ignore")
                    except Exception:
                        value = str(value)
                
                exif_data[decoded] = value
    return exif_data

async def process_image(file: UploadFile, background_tasks: BackgroundTasks):
    
    image_id = str(uuid.uuid4())

    file_path = UPLOAD_DIR / f"{image_id}_{file.filename}"
    with open(file_path, "wb") as f:
        contents = await file.read()
        f.write(contents)

    insert_image(image_id=image_id, filename=file.filename, status="processing")

    print(f"Saved {file.filename} as {file_path}, ID={image_id}")

    background_tasks.add_task(process_image_in_background, file_path, image_id)


    return image_id

def process_image_in_background(file_path: Path, image_id: str):
    try:
        img = Image.open(file_path)
        exif = extract_exif(file_path)
        update_image_exif(image_id, exif)
        width, height = img.size
        fmt = img.format.lower()
        size_bytes = file_path.stat().st_size

        thumbs = {}
        for size_name, size in THUMB_SIZES.items():
            thumb_path = UPLOAD_DIR / f"{image_id}_{size_name}_{file_path.name}"
            thumb_img = img.copy()
            thumb_img.thumbnail(size)
            thumb_img.save(thumb_path)
            thumbs[size_name] = str(thumb_path)

        update_image_metadata(image_id, width, height, fmt, size_bytes)
        update_image_thumbnails(image_id, thumbs["small"], thumbs["medium"])

        update_image_status(image_id, "processed")

        mark_image_processed(image_id)

    except Exception as e:
        print(f"Error processing image {file_path.name}: {e}")
        update_image_status(image_id, "failed")

    try:
        caption = generate_caption(str(file_path))

        update_image_caption(image_id, caption)

    except Exception as e:
        print(f"Error generating caption for {file_path.name}: {e}")

    return image_id

def list_images():
    return get_all_images()


def get_image(image_id: str):
    return get_image_by_id(image_id)

def generate_caption(image_path: str) -> str:
    img = Image.open(image_path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt").to(device)
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption
