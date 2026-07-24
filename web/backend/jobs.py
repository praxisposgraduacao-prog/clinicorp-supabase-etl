import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Dict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SCRIPTS: Dict[str, str] = {
    "incremental": "incremental_sync.py",
    "full_load": "load_complete_2020.py",
    "patients": "load_all_patients.py",
    "professionals": "load_professionals_direct.py",
    "verify": "verify_data_integrity.py",
}

jobs: Dict[str, dict] = {}

def create_job(job_type: str) -> str:
    if job_type not in SCRIPTS:
        raise ValueError(f"Unknown job type: {job_type}")
    for j in jobs.values():
        if j["status"] == "running":
            raise RuntimeError("Another job is already running")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "type": job_type,
        "script": SCRIPTS[job_type],
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "return_code": None,
    }
    return job_id

async def run_job(job_id: str, log_queue: asyncio.Queue) -> None:
    job = jobs[job_id]
    job["status"] = "running"
    job["started_at"] = datetime.now(timezone.utc).isoformat()

    python = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
    if not os.path.exists(python):
        python = "python"

    script_path = os.path.join(PROJECT_ROOT, job["script"])
    try:
        proc = await asyncio.create_subprocess_exec(
            python, script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=PROJECT_ROOT,
        )

        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").rstrip()
            await log_queue.put(text)

        await proc.wait()
        job["status"] = "done" if proc.returncode == 0 else "error"
        job["return_code"] = proc.returncode
    except Exception as e:
        job["status"] = "error"
        await log_queue.put(f"[ERROR] Failed to launch job: {e}")
    finally:
        await log_queue.put(None)  # sentinel — signals WebSocket to close
