from fastapi import FastAPI
from app.routes import router as image_router
from app.services.database_service import init_db 

init_db()

app = FastAPI(title = "Image Pipeline API")

app.include_router(image_router, prefix="/api")