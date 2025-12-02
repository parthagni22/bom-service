from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from celery.result import AsyncResult
from ..main import celery_app
import os, uuid, shutil

router = APIRouter()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "..", "data", "jobs")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
os.makedirs(DATA_DIR, exist_ok=True)

@router.get("/", response_class=HTMLResponse)
async def home():
    """Serve the UI"""
    html_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return {"message": "BOM Service is running - UI not found"}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(DATA_DIR, job_id, "in")
    os.makedirs(job_dir, exist_ok=True)
    in_path = os.path.join(job_dir, file.filename)
    with open(in_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    from ..workers.tasks import process_file_task
    try:
        task = process_file_task.delay(job_id, in_path)
        return {"job_id": job_id, "task_id": task.id, "status": "queued"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"error":"queue_unavailable","detail":str(e)})

@router.get("/status/{task_id}")
def status(task_id: str):
    r = AsyncResult(task_id, app=celery_app)
    payload = {"task_id": task_id, "state": r.state}
    if r.state == "FAILURE":
        payload["error"] = str(r.result)
    if r.state == "SUCCESS":
        payload["result"] = r.result
    return payload

@router.get("/download/{job_id}")
def download(job_id: str):
    out_dir = os.path.join(DATA_DIR, job_id, "out")
    xlsx = os.path.join(out_dir, "BOQ_Output.xlsx")
    if not os.path.exists(xlsx):
        raise HTTPException(status_code=404, detail="Output not found yet")
    return FileResponse(
        xlsx,
        filename=f"BOQ_{job_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



#------------------------------------------------------------------------
# from fastapi import APIRouter, UploadFile, File, HTTPException
# from fastapi.responses import FileResponse, JSONResponse
# from celery.result import AsyncResult
# from ..main import celery_app
# import os, uuid, shutil

# router = APIRouter()

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# DATA_DIR = os.path.join(BASE_DIR, "..", "data", "jobs")
# os.makedirs(DATA_DIR, exist_ok=True)

# @router.get("/")
# def root():
#     return {"message": "BOM Service is running"}

# @router.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     job_id = str(uuid.uuid4())
#     job_dir = os.path.join(DATA_DIR, job_id, "in")
#     os.makedirs(job_dir, exist_ok=True)
#     in_path = os.path.join(job_dir, file.filename)
#     with open(in_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)
#     from ..workers.tasks import process_file_task
#     try:
#         task = process_file_task.delay(job_id, in_path)
#         return {"job_id": job_id, "task_id": task.id, "status": "queued"}
#     except Exception as e:
#         return JSONResponse(status_code=503, content={"error":"queue_unavailable","detail":str(e)})

# @router.get("/status/{task_id}")
# def status(task_id: str):
#     r = AsyncResult(task_id, app=celery_app)
#     payload = {"task_id": task_id, "state": r.state}
#     if r.state == "FAILURE":
#         payload["error"] = str(r.result)
#     if r.state == "SUCCESS":
#         payload["result"] = r.result
#     return payload

# @router.get("/download/{job_id}")
# def download(job_id: str):
#     out_dir = os.path.join(DATA_DIR, job_id, "out")
#     xlsx = os.path.join(out_dir, "BOQ_Output.xlsx")
#     if not os.path.exists(xlsx):
#         raise HTTPException(status_code=404, detail="Output not found yet")
#     return FileResponse(
#         xlsx,
#         filename=f"BOQ_{job_id}.xlsx",
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
