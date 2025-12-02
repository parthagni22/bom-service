from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery
from celery.result import AsyncResult
import shutil
import os
import uuid

app = FastAPI(title="BOM Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Initialize Celery (will use Redis broker)
celery_app = Celery(
    "bom_service",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("RESULT_BACKEND", "redis://localhost:6379/1")
)

celery_app.conf.update(
    include=["app.workers.tasks"],     # register tasks on worker boot
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def ping():
    return "pong"


from .api.routes import router
app.include_router(router)




# # Test Celery task
# @celery_app.task
# def process_file_task(file_path: str):
#     # (You’ll replace this with your DWG→DXF→Excel logic)
#     import time
#     time.sleep(5)
#     return {"status": "completed", "file_path": file_path}

# @app.get("/")
# def root():
#     return {"message": "BOM Service is running"}

# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     job_id = str(uuid.uuid4())
#     folder = f"uploads/{job_id}"
#     os.makedirs(folder, exist_ok=True)

#     file_path = os.path.join(folder, file.filename)
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     # Queue a Celery task
#     task = process_file_task.delay(file_path)
#     return {"job_id": job_id, "task_id": task.id, "status": "queued"}
