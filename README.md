# Image Pipeline API

## Project Overview
This API allows users to upload images, automatically generate thumbnails, extract metadata, and generate AI-based captions. 
Supports JPG and PNG formats. Built with FastAPI, SQLite, and HuggingFace BLIP for image captioning.

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/tessatanjr/image-pipeline-api.git
    cd image_pipeline
2. Create a virtual environment:
   ```bash
    python3 -m venv image-processing-venv
    source image-processing-venv/bin/activate
4. Install dependencies:
    ```bash
    pip install -r requirements.txt
6. Run the server
   ```bash
    uvicorn app.main:app --reload


## API Documentation
# Endpoints

**GET /api/images**
    - Returns a list of all images with metadata

**POST /api/images**
    - Uploads the image
    - Immediately returns imageID
    - initiates background task to generate thumbnails/ captions/ exif/ metadata

**GET /api/images/{image_id}**
    - Returns metadata, thumbnails and caption of image requested by ID

**GET /api/images/{image_id}/thumbnails/{size}**
    - Returns image file of small/medium thumbnail requested

**GET /api/stats**
    - Returns processing stats such as average processing time.
