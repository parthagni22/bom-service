import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workers.pipeline import run_pipeline

# Use an actual DWG file you have
dwg_file = r"C:\Users\91930\Downloads\Furniture Layout_ PCMC.dwg"
job_id = "test-001"
base_dir = r"D:\Irizpro\bom-service\data\jobs"

# Create job structure
job_dir = os.path.join(base_dir, job_id, "in")
os.makedirs(job_dir, exist_ok=True)

# Copy your DWG file there
import shutil
dest = os.path.join(job_dir, "test.dwg")
shutil.copy(dwg_file, dest)

# Run pipeline
try:
    result = run_pipeline(job_id, dest, base_dir)
    print("✅ Success!")
    print(result)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()