import asyncio
import os

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import authenticate_user, create_token, verify_token
from db import get_status
from jobs import create_job, run_job, jobs

app = FastAPI(title="Clinicorp ETL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        return verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalido")

# -- Auth ---------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    if not authenticate_user(req.email, req.password):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")
    return {"access_token": create_token(req.email), "token_type": "bearer"}

# -- Status -------------------------------------------------------------------

@app.get("/api/status")
async def status(_: str = Depends(current_user)):
    return await get_status()

# -- Jobs ---------------------------------------------------------------------

class JobRequest(BaseModel):
    type: str

@app.post("/api/jobs")
async def start_job(req: JobRequest, _: str = Depends(current_user)):
    try:
        job_id = create_job(req.type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, _: str = Depends(current_user)):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job nao encontrado")
    return jobs[job_id]

@app.websocket("/api/jobs/{job_id}/logs")
async def job_logs(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in jobs:
        await websocket.close(code=4004)
        return
    log_queue: asyncio.Queue = asyncio.Queue()
    task = asyncio.create_task(run_job(job_id, log_queue))
    try:
        while True:
            line = await log_queue.get()
            if line is None:
                break
            await websocket.send_text(line)
    except WebSocketDisconnect:
        task.cancel()
    finally:
        await websocket.close()

# -- Static (production) ------------------------------------------------------

_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
