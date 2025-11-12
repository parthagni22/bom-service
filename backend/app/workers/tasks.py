import os
from celery import Celery
from ..main import celery_app
from .pipeline import run_pipeline

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "..", "data", "jobs")
os.makedirs(DATA_DIR, exist_ok=True)

@celery_app.task(bind=True, max_retries=2)
def process_file_task(self, job_id: str, in_path: str):
    try:
        result = run_pipeline(job_id, in_path, base_dir=DATA_DIR)
        return result  # visible in /status when SUCCESS
    except Exception as e:
        raise e
