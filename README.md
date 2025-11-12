# BOM Service

Automated DWG → DXF → Excel BOM/BOQ generator built with FastAPI, Celery, and ezdxf.

## Structure
- `backend/` — FastAPI app, Celery worker, parsing logic
- `frontend/` — React/Next.js client for uploads
- `deploy/` — Docker, nginx, and infra files
- `.github/` — CI/CD pipelines

## Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
