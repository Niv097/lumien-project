import os
import subprocess
import shutil
import time
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..core.security import RoleChecker

router = APIRouter()

admin_checker = RoleChecker(["Lumien Super Admin"])

def run_ingestion(custom_path=None):
    # Find the ingestion script in the project root
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_root = os.path.dirname(backend_dir)
    
    script_path = os.path.join(project_root, "ingest_i4c_dataset.py")
    if not os.path.exists(script_path):
        script_path = os.path.join(backend_dir, "ingest_demo_dataset.py")
        
    print(f"Triggering ingestion using script: {script_path}")
    
    # We must ensure we run this using the same python executable or in the right env
    import sys
    python_exe = sys.executable
    
    args = [python_exe, script_path]
    if custom_path:
        args.append(custom_path)
    
    try:
        subprocess.run(args, cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ingestion failed: {e}")

@router.post("/upload-dataset", dependencies=[Depends(admin_checker)])
async def upload_dataset(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed")
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Securely store in an 'uploads' directory
    uploads_dir = os.path.join(backend_dir, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    timestamp = int(time.time())
    safe_filename = file.filename.replace(" ", "_").replace("/", "").replace("\\", "")
    target_path = os.path.join(uploads_dir, f"{timestamp}_{safe_filename}")
    
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
        
    background_tasks.add_task(run_ingestion, target_path)
    
    return {"message": "Dataset uploaded successfully and saved securely. Ingestion started in the background (ready in ~1 minute)."}

@router.post("/reset-dataset", dependencies=[Depends(admin_checker)])
async def reset_dataset(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_ingestion)
    return {"message": "Dataset reset started. Data will be re-ingested from the default built-in Excel file in the background."}
