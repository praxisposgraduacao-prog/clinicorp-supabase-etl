# Clinicorp ETL Web Interface — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI + React web interface for the team to trigger and monitor Clinicorp ETL jobs, with real-time log streaming via WebSocket and JWT auth.

**Architecture:** FastAPI backend runs ETL scripts as subprocesses and streams stdout/stderr to the browser via WebSocket. React frontend shows a dashboard with DB counts, operation buttons, and a live terminal. Database migrates from Supabase client to psycopg2 + local PostgreSQL, configured via `DATABASE_URL` in `.env`.

**Tech Stack:** Python 3.11+, FastAPI, asyncpg, psycopg2-binary, python-jose, passlib[bcrypt], React 18, Vite, TypeScript, react-router-dom

---

## File Map

```
clinicorp/
├── web/
│   ├── backend/
│   │   ├── __init__.py        (empty)
│   │   ├── main.py            FastAPI app: routes, CORS, static files
│   │   ├── auth.py            JWT create/verify, bcrypt, users.json, CLI
│   │   ├── jobs.py            Job registry, subprocess runner, WebSocket queue
│   │   ├── db.py              asyncpg: table counts + last_sync for dashboard
│   │   ├── users.json         [{email, password_hash}] — created by CLI
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx              Router + PrivateRoute
│   │       ├── api.ts               fetch/WebSocket helpers + JWT storage
│   │       ├── pages/
│   │       │   ├── Login.tsx
│   │       │   └── Dashboard.tsx
│   │       └── components/
│   │           ├── StatusCards.tsx  DB counts grid
│   │           ├── OperationGrid.tsx  Job buttons 3×2
│   │           └── JobLog.tsx         Live terminal via WebSocket
│   └── tests/
│       ├── __init__.py        (empty)
│       ├── test_auth.py
│       └── test_jobs.py
├── db_client.py               psycopg2 upsert/count/select_ids helper (project root)
└── .env                       add DATABASE_URL and JWT_SECRET
```

ETL scripts modified in Tasks 1–2:
- `incremental_sync.py` — replace supabase client with db_client
- `load_all_patients.py` — replace supabase client with db_client
- `load_professionals_direct.py` — replace supabase client with db_client
- `verify_data_integrity.py` — replace supabase client with db_client

---

## Task 1: Local PostgreSQL setup + db_client.py

**Files:**
- Create: `db_client.py` (project root)
- Modify: `.env`

- [ ] **Step 1: Create local PostgreSQL database**

  If PostgreSQL is not installed: download from https://www.postgresql.org/download/windows/ and install with default settings (user `postgres`, port `5432`).

  Then create the database:
  ```bash
  psql -U postgres -c "CREATE DATABASE clinicorp;"
  ```

  Run the schema:
  ```bash
  psql -U postgres -d clinicorp -f schema.sql
  ```

  Verify tables were created:
  ```bash
  psql -U postgres -d clinicorp -c "\dt"
  ```
  Expected: list of tables including `appointments`, `patients`, `payments`, `invoices`, `professionals`, `clinics`.

- [ ] **Step 2: Add DATABASE_URL and JWT_SECRET to .env**

  Append to `.env`:
  ```
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/clinicorp
  JWT_SECRET=gere-uma-string-aleatoria-aqui-com-32-chars
  ```

  Replace `postgres:postgres` with the actual PostgreSQL user:password on the machine.

- [ ] **Step 3: Write db_client.py**

  Create `db_client.py` at project root:
  ```python
  import os
  import psycopg2
  import psycopg2.extras
  from typing import List, Dict, Any, Set

  def _conn():
      return psycopg2.connect(os.getenv("DATABASE_URL"))

  def upsert(table: str, data: List[Dict[str, Any]], conflict_col: str = "id") -> int:
      if not data:
          return 0
      cols = list(data[0].keys())
      update_cols = [c for c in cols if c != conflict_col]
      update_set = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
      sql = (
          f"INSERT INTO {table} ({','.join(cols)}) VALUES %s "
          f"ON CONFLICT ({conflict_col}) DO UPDATE SET {update_set}"
      )
      conn = _conn()
      try:
          with conn:
              with conn.cursor() as cur:
                  values = [[row.get(c) for c in cols] for row in data]
                  psycopg2.extras.execute_values(cur, sql, values)
                  return cur.rowcount
      finally:
          conn.close()

  def count(table: str) -> int:
      conn = _conn()
      try:
          with conn.cursor() as cur:
              cur.execute(f"SELECT COUNT(*) FROM {table}")
              return cur.fetchone()[0]
      finally:
          conn.close()

  def select_ids(table: str) -> Set[int]:
      conn = _conn()
      try:
          with conn.cursor() as cur:
              cur.execute(f"SELECT id FROM {table}")
              return {row[0] for row in cur.fetchall()}
      finally:
          conn.close()
  ```

- [ ] **Step 4: Smoke-test db_client**

  ```bash
  python -c "from dotenv import load_dotenv; load_dotenv(); import db_client; print(db_client.count('clinics'))"
  ```
  Expected: `0` (or however many rows exist). No exception means the connection works.

- [ ] **Step 5: Commit**

  ```bash
  git add db_client.py .env
  git commit -m "feat: add db_client.py psycopg2 helper for local PostgreSQL"
  ```

---

## Task 2: Migrate ETL scripts from Supabase client to psycopg2

**Files:**
- Modify: `incremental_sync.py`
- Modify: `load_all_patients.py`
- Modify: `load_professionals_direct.py`
- Modify: `verify_data_integrity.py`

- [ ] **Step 1: Migrate incremental_sync.py**

  Replace the Supabase client block (lines that import and use `create_client`) with `db_client`:

  At top, replace:
  ```python
  from supabase import create_client
  # ...
  SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
  SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")
  client = create_client(SUPABASE_URL, SUPABASE_KEY)
  ```
  With:
  ```python
  import db_client
  ```

  Replace every `{r['id'] for r in client.table('X').select('id').execute().data}` with `db_client.select_ids('X')`.

  Replace every `upsert_batch('X', data)` call — the internal `upsert_batch` function already uses the supabase client. Replace the entire `upsert_batch` function body to call `db_client.upsert` instead:
  ```python
  def upsert_batch(table, data, conflict_col='id'):
      if not data:
          return 0, 0
      try:
          n = db_client.upsert(table, data, conflict_col)
          return n, 0
      except Exception as e:
          print(f"    [BATCH ERROR] {e}")
          return 0, len(data)
  ```

  Replace the final count block:
  ```python
  # OLD:
  apt_total = client.table('appointments').select('id', count='exact').execute().count
  # NEW:
  apt_total = db_client.count('appointments')
  ```
  Do the same for `payments`, `invoices`.

- [ ] **Step 2: Test incremental_sync.py**

  ```bash
  python incremental_sync.py
  ```
  Expected: runs without `supabase` import errors; pulls from Clinicorp API and writes to local PostgreSQL. Check counts at the end match what is printed.

- [ ] **Step 3: Migrate load_all_patients.py**

  Replace Supabase client imports and usage at the top:
  ```python
  # Remove:
  from supabase import create_client
  SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
  SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")
  client = create_client(SUPABASE_URL, SUPABASE_KEY)

  # Add:
  import db_client
  ```

  Replace the `existing_patients` query:
  ```python
  # OLD:
  result = client.table('patients').select('id').execute()
  existing_patients = set([p['id'] for p in result.data])
  # NEW:
  existing_patients = db_client.select_ids('patients')
  ```

  Replace the `safe_upsert` function internals to use `db_client.upsert`:
  ```python
  def safe_upsert(table_name, data, key='id', retry=0):
      try:
          if not data:
              return 0, 0
          seen = {}
          cleaned = [r for r in data if r.get(key) not in seen and not seen.update({r.get(key): True})]
          n = db_client.upsert(table_name, cleaned, key)
          return n, 0
      except Exception as e:
          if retry < MAX_RETRIES:
              time.sleep(RETRY_DELAY)
              return safe_upsert(table_name, data, key, retry + 1)
          print(f"        [ERROR] {str(e)[:100]}")
          return 0, len(data)
  ```

- [ ] **Step 4: Migrate load_professionals_direct.py**

  Replace Supabase client:
  ```python
  # Remove:
  from supabase import create_client
  SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
  SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

  # Keep only:
  import db_client
  ```

  Replace the insert block:
  ```python
  # OLD:
  client = create_client(SUPABASE_URL, SUPABASE_KEY)
  result = client.table('professionals').insert(data_to_insert, ignore_duplicates=True).execute()

  # NEW:
  n = db_client.upsert('professionals', data_to_insert, conflict_col='id')
  print(f"    Sucesso! {n} inseridos")
  ```

  Replace the verification block:
  ```python
  # OLD:
  client = create_client(SUPABASE_URL, SUPABASE_KEY)
  result = client.table('professionals').select('id', count='exact').execute()
  total = result.count if hasattr(result, 'count') else len(result.data)

  # NEW:
  total = db_client.count('professionals')
  ```

- [ ] **Step 5: Migrate verify_data_integrity.py**

  Open the file and replace the Supabase client with `db_client`. The file queries patient/appointment/payment IDs from the DB. Replace:
  ```python
  # OLD pattern:
  result = client.table('appointments').select('patient_id').execute()
  patient_ids = set([a.get('patient_id') for a in result.data if a.get('patient_id')])

  # NEW — use a direct psycopg2 query via db_client helper:
  # Add this function to db_client.py first (Step 5a below)
  patient_ids = db_client.select_col('appointments', 'patient_id')
  ```

- [ ] **Step 5a: Add select_col to db_client.py**

  Append to `db_client.py`:
  ```python
  def select_col(table: str, col: str) -> Set:
      conn = _conn()
      try:
          with conn.cursor() as cur:
              cur.execute(f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL")
              return {row[0] for row in cur.fetchall()}
      finally:
          conn.close()
  ```

- [ ] **Step 6: Run verify_data_integrity.py**

  ```bash
  python verify_data_integrity.py
  ```
  Expected: runs without `supabase` import errors. Output shows verification results against local PostgreSQL.

- [ ] **Step 7: Commit**

  ```bash
  git add db_client.py incremental_sync.py load_all_patients.py load_professionals_direct.py verify_data_integrity.py
  git commit -m "feat: migrate ETL scripts from Supabase client to psycopg2 via db_client"
  ```

---

## Task 3: Backend scaffold + auth module

**Files:**
- Create: `web/backend/__init__.py`
- Create: `web/backend/requirements.txt`
- Create: `web/backend/auth.py`
- Create: `web/backend/users.json`
- Create: `web/tests/__init__.py`
- Create: `web/tests/test_auth.py`

- [ ] **Step 1: Create directory structure**

  ```bash
  mkdir -p web/backend web/tests
  ```

- [ ] **Step 2: Create web/backend/__init__.py and web/tests/__init__.py**

  Both files are empty. Create them:
  ```bash
  touch web/backend/__init__.py web/tests/__init__.py
  ```

- [ ] **Step 3: Create web/backend/requirements.txt**

  ```
  fastapi>=0.109.0
  uvicorn[standard]>=0.27.0
  asyncpg>=0.29.0
  python-jose[cryptography]>=3.3.0
  passlib[bcrypt]>=1.7.4
  psycopg2-binary>=2.9.0
  python-multipart>=0.0.9
  python-dotenv>=1.0.0
  pytest>=8.0.0
  pytest-asyncio>=0.23.0
  ```

- [ ] **Step 4: Install backend dependencies**

  ```bash
  cd web && ../.venv/Scripts/pip install -r backend/requirements.txt
  ```
  Expected: packages install without errors.

- [ ] **Step 5: Write the failing tests for auth**

  Create `web/tests/test_auth.py`:
  ```python
  import json
  import pytest
  import sys, os
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

  from auth import hash_password, verify_password, create_token, verify_token, authenticate_user

  def test_password_hash_and_verify():
      hashed = hash_password("secret123")
      assert verify_password("secret123", hashed)
      assert not verify_password("wrong", hashed)

  def test_create_and_verify_token():
      token = create_token("test@praxis.com")
      assert verify_token(token) == "test@praxis.com"

  def test_invalid_token_raises():
      with pytest.raises(Exception):
          verify_token("not-a-valid-token")

  def test_authenticate_user(tmp_path, monkeypatch):
      users = [{"email": "admin@praxis.com", "password_hash": hash_password("pass123")}]
      users_file = tmp_path / "users.json"
      users_file.write_text(json.dumps(users))
      import auth
      monkeypatch.setattr(auth, "USERS_FILE", str(users_file))
      assert authenticate_user("admin@praxis.com", "pass123")
      assert not authenticate_user("admin@praxis.com", "wrong")
      assert not authenticate_user("other@praxis.com", "pass123")
  ```

- [ ] **Step 6: Run tests to verify they fail**

  ```bash
  cd web && ../.venv/Scripts/pytest tests/test_auth.py -v
  ```
  Expected: `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 7: Create web/backend/auth.py**

  ```python
  import json
  import os
  import sys
  from datetime import datetime, timedelta, timezone

  from jose import jwt, JWTError
  from passlib.context import CryptContext

  SECRET_KEY = os.getenv("JWT_SECRET", "change-me")
  ALGORITHM = "HS256"
  EXPIRE_HOURS = 8
  USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def hash_password(plain: str) -> str:
      return pwd_context.hash(plain)

  def verify_password(plain: str, hashed: str) -> bool:
      return pwd_context.verify(plain, hashed)

  def create_token(email: str) -> str:
      expire = datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS)
      return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

  def verify_token(token: str) -> str:
      payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
      return payload["sub"]

  def authenticate_user(email: str, password: str) -> bool:
      try:
          with open(USERS_FILE) as f:
              users = json.load(f)
      except FileNotFoundError:
          return False
      user = next((u for u in users if u["email"] == email), None)
      if not user:
          return False
      return verify_password(password, user["password_hash"])

  if __name__ == "__main__":
      if len(sys.argv) == 3 and sys.argv[1] == "create-user":
          import getpass
          email = sys.argv[2]
          password = getpass.getpass("Password: ")
          users = []
          try:
              with open(USERS_FILE) as f:
                  users = json.load(f)
          except FileNotFoundError:
              pass
          users.append({"email": email, "password_hash": hash_password(password)})
          with open(USERS_FILE, "w") as f:
              json.dump(users, f, indent=2)
          print(f"Usuário {email} criado.")
  ```

- [ ] **Step 8: Create initial users.json**

  ```bash
  cd web/backend && ../../.venv/Scripts/python auth.py create-user admpraxis@praxis
  ```
  Enter a password when prompted. This creates `web/backend/users.json`.

- [ ] **Step 9: Run tests to verify they pass**

  ```bash
  cd web && ../.venv/Scripts/pytest tests/test_auth.py -v
  ```
  Expected: 4 tests PASSED.

- [ ] **Step 10: Commit**

  ```bash
  git add web/backend/__init__.py web/backend/requirements.txt web/backend/auth.py web/backend/users.json web/tests/__init__.py web/tests/test_auth.py
  git commit -m "feat: backend auth module (JWT + bcrypt) with CLI user creation"
  ```

---

## Task 4: Job executor module

**Files:**
- Create: `web/backend/jobs.py`
- Create: `web/tests/test_jobs.py`

- [ ] **Step 1: Write failing tests for jobs**

  Create `web/tests/test_jobs.py`:
  ```python
  import pytest
  import sys, os
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

  import jobs as jobs_module

  def setup_function():
      jobs_module.jobs.clear()

  def test_create_job_valid_type():
      job_id = jobs_module.create_job("incremental")
      assert job_id in jobs_module.jobs
      assert jobs_module.jobs[job_id]["type"] == "incremental"
      assert jobs_module.jobs[job_id]["status"] == "pending"

  def test_create_job_invalid_type():
      with pytest.raises(ValueError, match="Unknown job type"):
          jobs_module.create_job("nonexistent")

  def test_create_job_blocks_when_running():
      job_id = jobs_module.create_job("incremental")
      jobs_module.jobs[job_id]["status"] = "running"
      with pytest.raises(RuntimeError, match="already running"):
          jobs_module.create_job("patients")

  def test_create_job_allows_after_previous_done():
      job_id = jobs_module.create_job("incremental")
      jobs_module.jobs[job_id]["status"] = "done"
      new_id = jobs_module.create_job("patients")
      assert new_id in jobs_module.jobs
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd web && ../.venv/Scripts/pytest tests/test_jobs.py -v
  ```
  Expected: `ModuleNotFoundError: No module named 'jobs'`

- [ ] **Step 3: Create web/backend/jobs.py**

  ```python
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
      await log_queue.put(None)  # sentinel — signals WebSocket to close
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd web && ../.venv/Scripts/pytest tests/test_jobs.py -v
  ```
  Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

  ```bash
  git add web/backend/jobs.py web/tests/test_jobs.py
  git commit -m "feat: job executor module with subprocess runner and WebSocket queue"
  ```

---

## Task 5: Database status module + FastAPI main

**Files:**
- Create: `web/backend/db.py`
- Create: `web/backend/main.py`

- [ ] **Step 1: Create web/backend/db.py**

  ```python
  import asyncpg
  import json
  import os

  DATABASE_URL = os.getenv("DATABASE_URL", "")
  SYNC_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "sync_state.json")

  TABLES = ["appointments", "payments", "invoices", "patients", "professionals"]

  async def get_status() -> dict:
      conn = await asyncpg.connect(DATABASE_URL)
      try:
          counts = {}
          for table in TABLES:
              row = await conn.fetchrow(f"SELECT COUNT(*) FROM {table}")
              counts[table] = row[0]
      finally:
          await conn.close()

      try:
          with open(SYNC_STATE_FILE) as f:
              state = json.load(f)
          counts["last_sync"] = state.get("last_sync", "N/A")
      except (FileNotFoundError, json.JSONDecodeError):
          counts["last_sync"] = "N/A"

      return counts
  ```

- [ ] **Step 2: Create web/backend/main.py**

  ```python
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
          raise HTTPException(status_code=401, detail="Token inválido")

  # ── Auth ──────────────────────────────────────────────────────────────────────

  class LoginRequest(BaseModel):
      email: str
      password: str

  @app.post("/api/auth/login")
  async def login(req: LoginRequest):
      if not authenticate_user(req.email, req.password):
          raise HTTPException(status_code=401, detail="Credenciais inválidas")
      return {"access_token": create_token(req.email), "token_type": "bearer"}

  # ── Status ────────────────────────────────────────────────────────────────────

  @app.get("/api/status")
  async def status(_: str = Depends(current_user)):
      return await get_status()

  # ── Jobs ──────────────────────────────────────────────────────────────────────

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
          raise HTTPException(status_code=404, detail="Job não encontrado")
      return jobs[job_id]

  @app.websocket("/api/jobs/{job_id}/logs")
  async def job_logs(websocket: WebSocket, job_id: str):
      await websocket.accept()
      if job_id not in jobs:
          await websocket.close(code=4004)
          return
      log_queue: asyncio.Queue = asyncio.Queue()
      asyncio.create_task(run_job(job_id, log_queue))
      try:
          while True:
              line = await log_queue.get()
              if line is None:
                  break
              await websocket.send_text(line)
      except WebSocketDisconnect:
          pass
      finally:
          await websocket.close()

  # ── Static (production) ───────────────────────────────────────────────────────

  _dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
  if os.path.exists(_dist):
      app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
  ```

- [ ] **Step 3: Smoke-test the backend**

  ```bash
  cd web/backend && ../../.venv/Scripts/uvicorn main:app --reload --port 8000
  ```
  Expected: server starts, output shows `Application startup complete`.

  In a second terminal, test the login endpoint:
  ```bash
  curl -s -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admpraxis@praxis\",\"password\":\"<sua-senha>\"}"
  ```
  Expected: `{"access_token":"eyJ...","token_type":"bearer"}`

- [ ] **Step 4: Commit**

  ```bash
  git add web/backend/db.py web/backend/main.py
  git commit -m "feat: FastAPI backend with auth, status, jobs routes and WebSocket log streaming"
  ```

---

## Task 6: Frontend scaffold

**Files:**
- Create: `web/frontend/package.json`
- Create: `web/frontend/vite.config.ts`
- Create: `web/frontend/tsconfig.json`
- Create: `web/frontend/index.html`
- Create: `web/frontend/src/main.tsx`
- Create: `web/frontend/src/App.tsx`
- Create: `web/frontend/src/api.ts`

- [ ] **Step 1: Verify Node.js is installed**

  ```bash
  node --version && npm --version
  ```
  Expected: versions printed (e.g. `v20.x.x` and `10.x.x`). If missing, install from https://nodejs.org/.

- [ ] **Step 2: Create web/frontend/package.json**

  ```json
  {
    "name": "clinicorp-etl-web",
    "version": "0.1.0",
    "scripts": {
      "dev": "vite",
      "build": "tsc && vite build",
      "preview": "vite preview"
    },
    "dependencies": {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-router-dom": "^6.22.0"
    },
    "devDependencies": {
      "@types/react": "^18.2.0",
      "@types/react-dom": "^18.2.0",
      "@vitejs/plugin-react": "^4.2.0",
      "typescript": "^5.3.0",
      "vite": "^5.1.0"
    }
  }
  ```

- [ ] **Step 3: Create web/frontend/vite.config.ts**

  ```typescript
  import { defineConfig } from "vite";
  import react from "@vitejs/plugin-react";

  export default defineConfig({
    plugins: [react()],
    server: {
      proxy: {
        "/api": "http://localhost:8000",
      },
    },
  });
  ```

- [ ] **Step 4: Create web/frontend/tsconfig.json**

  ```json
  {
    "compilerOptions": {
      "target": "ES2020",
      "useDefineForClassFields": true,
      "lib": ["ES2020", "DOM", "DOM.Iterable"],
      "module": "ESNext",
      "skipLibCheck": true,
      "moduleResolution": "bundler",
      "allowImportingTsExtensions": true,
      "resolveJsonModule": true,
      "isolatedModules": true,
      "noEmit": true,
      "jsx": "react-jsx",
      "strict": true
    },
    "include": ["src"]
  }
  ```

- [ ] **Step 5: Create web/frontend/index.html**

  ```html
  <!DOCTYPE html>
  <html lang="pt-BR">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Clinicorp ETL</title>
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; }
      </style>
    </head>
    <body>
      <div id="root"></div>
      <script type="module" src="/src/main.tsx"></script>
    </body>
  </html>
  ```

- [ ] **Step 6: Install frontend dependencies**

  ```bash
  cd web/frontend && npm install
  ```
  Expected: `node_modules` created, no errors.

- [ ] **Step 7: Create web/frontend/src/api.ts**

  ```typescript
  const API_BASE = import.meta.env.VITE_API_URL ?? "";

  export function getToken(): string | null {
    return localStorage.getItem("token");
  }

  export function setToken(token: string): void {
    localStorage.setItem("token", token);
  }

  export function clearToken(): void {
    localStorage.removeItem("token");
  }

  async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
    const token = getToken();
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
    if (res.status === 401) {
      clearToken();
      window.location.href = "/login";
    }
    return res;
  }

  export async function login(email: string, password: string): Promise<string> {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Credenciais inválidas");
    const data = await res.json();
    return data.access_token as string;
  }

  export async function getStatus(): Promise<Record<string, number | string>> {
    const res = await apiFetch("/api/status");
    if (!res.ok) throw new Error("Erro ao buscar status");
    return res.json();
  }

  export async function startJob(type: string): Promise<string> {
    const res = await apiFetch("/api/jobs", {
      method: "POST",
      body: JSON.stringify({ type }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error((err.detail as string) ?? "Erro ao iniciar job");
    }
    const data = await res.json();
    return data.job_id as string;
  }

  export function createLogSocket(jobId: string): WebSocket {
    const wsBase = (window.location.origin).replace(/^http/, "ws");
    return new WebSocket(`${wsBase}/api/jobs/${jobId}/logs`);
  }
  ```

- [ ] **Step 8: Create web/frontend/src/main.tsx**

  ```tsx
  import { StrictMode } from "react";
  import { createRoot } from "react-dom/client";
  import App from "./App";

  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
  ```

- [ ] **Step 9: Create web/frontend/src/App.tsx**

  ```tsx
  import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
  import { getToken } from "./api";
  import Login from "./pages/Login";
  import Dashboard from "./pages/Dashboard";

  function PrivateRoute({ children }: { children: React.ReactNode }) {
    return getToken() ? <>{children}</> : <Navigate to="/login" replace />;
  }

  export default function App() {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
    );
  }
  ```

- [ ] **Step 10: Verify TypeScript compiles**

  ```bash
  cd web/frontend && npm run build
  ```
  Expected: fails with `Cannot find module './pages/Login'` — this is correct, pages don't exist yet.

- [ ] **Step 11: Commit**

  ```bash
  git add web/frontend/
  git commit -m "feat: React + Vite frontend scaffold with api.ts and router"
  ```

---

## Task 7: Login page

**Files:**
- Create: `web/frontend/src/pages/Login.tsx`

- [ ] **Step 1: Create web/frontend/src/pages/Login.tsx**

  ```tsx
  import { useState } from "react";
  import { useNavigate } from "react-router-dom";
  import { login, setToken } from "../api";

  export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    async function handleSubmit(e: React.FormEvent) {
      e.preventDefault();
      setLoading(true);
      setError("");
      try {
        const token = await login(email, password);
        setToken(token);
        navigate("/");
      } catch {
        setError("Email ou senha incorretos");
      } finally {
        setLoading(false);
      }
    }

    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <form onSubmit={handleSubmit} style={{ background: "#1e293b", padding: "2rem", borderRadius: "8px", width: "320px", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <h2 style={{ color: "#38bdf8", textAlign: "center", marginBottom: "0.5rem" }}>⚡ Clinicorp ETL</h2>
          {error && <p style={{ color: "#f87171", fontSize: "0.875rem" }}>{error}</p>}
          <input
            type="email" placeholder="Email" value={email} required
            onChange={e => setEmail(e.target.value)}
            style={{ padding: "0.75rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#e2e8f0" }}
          />
          <input
            type="password" placeholder="Senha" value={password} required
            onChange={e => setPassword(e.target.value)}
            style={{ padding: "0.75rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#e2e8f0" }}
          />
          <button
            type="submit" disabled={loading}
            style={{ padding: "0.75rem", background: loading ? "#334155" : "#0284c7", color: "white", border: "none", borderRadius: "4px", cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </div>
    );
  }
  ```

- [ ] **Step 2: Start both servers and test login manually**

  Terminal 1 (backend):
  ```bash
  cd web/backend && ../../.venv/Scripts/uvicorn main:app --reload --port 8000
  ```

  Terminal 2 (frontend):
  ```bash
  cd web/frontend && npm run dev
  ```

  Open http://localhost:5173/login — enter the credentials created in Task 3 Step 8. Expected: redirects to `/` (which shows a blank page since Dashboard doesn't exist yet).

- [ ] **Step 3: Commit**

  ```bash
  git add web/frontend/src/pages/Login.tsx
  git commit -m "feat: login page with JWT auth"
  ```

---

## Task 8: StatusCards component

**Files:**
- Create: `web/frontend/src/components/StatusCards.tsx`

- [ ] **Step 1: Create web/frontend/src/components/StatusCards.tsx**

  ```tsx
  import { useEffect, useState } from "react";
  import { getStatus } from "../api";

  const CARDS = [
    { key: "appointments",  label: "Agendamentos",  color: "#38bdf8" },
    { key: "payments",      label: "Pagamentos",    color: "#34d399" },
    { key: "invoices",      label: "Faturas",       color: "#a78bfa" },
    { key: "patients",      label: "Pacientes",     color: "#fb923c" },
    { key: "professionals", label: "Profissionais", color: "#e2e8f0" },
  ];

  interface Props {
    refreshTrigger: number;
  }

  export default function StatusCards({ refreshTrigger }: Props) {
    const [data, setData] = useState<Record<string, number | string>>({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      setLoading(true);
      getStatus()
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }, [refreshTrigger]);

    const fmt = (v: number | string | undefined) =>
      typeof v === "number" ? v.toLocaleString("pt-BR") : (v ?? "—");

    return (
      <section>
        <p style={{ color: "#64748b", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Dashboard</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "0.75rem", marginBottom: "0.75rem" }}>
          {CARDS.map(c => (
            <div key={c.key} style={{ background: "#1e293b", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
              <div style={{ color: c.color, fontSize: "1.5rem", fontWeight: 700 }}>
                {loading ? "..." : fmt(data[c.key])}
              </div>
              <div style={{ color: "#64748b", fontSize: "0.7rem" }}>{c.label}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1.5rem" }}>
          <div style={{ background: "#1e293b", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
            <div style={{ color: "#fbbf24", fontSize: "0.85rem", fontWeight: 600 }}>
              {String(data.last_sync ?? "—").slice(0, 16).replace("T", " ")}
            </div>
            <div style={{ color: "#64748b", fontSize: "0.7rem" }}>Última Sync</div>
          </div>
          <div style={{ background: "#1e293b", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
            <div style={{ color: loading ? "#64748b" : "#34d399", fontSize: "0.85rem", fontWeight: 600 }}>
              {loading ? "..." : "● Conectado"}
            </div>
            <div style={{ color: "#64748b", fontSize: "0.7rem" }}>Status PostgreSQL</div>
          </div>
        </div>
      </section>
    );
  }
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add web/frontend/src/components/StatusCards.tsx
  git commit -m "feat: StatusCards component showing DB counts and last sync"
  ```

---

## Task 9: OperationGrid + JobLog components

**Files:**
- Create: `web/frontend/src/components/OperationGrid.tsx`
- Create: `web/frontend/src/components/JobLog.tsx`

- [ ] **Step 1: Create web/frontend/src/components/OperationGrid.tsx**

  ```tsx
  const OPS = [
    { type: "incremental",   label: "Sync Incremental",    desc: "Dados do dia",       icon: "↻",  primary: true },
    { type: "full_load",     label: "Carga Completa",      desc: "Desde 2020",         icon: "📦", primary: false },
    { type: "patients",      label: "Sync Pacientes",      desc: "Novos cadastros",    icon: "👤", primary: false },
    { type: "professionals", label: "Sync Profissionais",  desc: "Equipe clínica",     icon: "🩺", primary: false },
    { type: "verify",        label: "Verificar Integridade", desc: "Diagnóstico FK",   icon: "🔍", primary: false },
    { type: "__refresh__",   label: "Atualizar Status",    desc: "Recarregar contagens", icon: "⟳", primary: false },
  ] as const;

  interface Props {
    running: boolean;
    onStart: (type: string) => void;
    onRefresh: () => void;
  }

  export default function OperationGrid({ running, onStart, onRefresh }: Props) {
    return (
      <section>
        <p style={{ color: "#64748b", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Operações</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem", marginBottom: "1.5rem" }}>
          {OPS.map(op => {
            const disabled = running && op.type !== "__refresh__";
            return (
              <button
                key={op.type}
                disabled={disabled}
                onClick={() => op.type === "__refresh__" ? onRefresh() : onStart(op.type)}
                style={{
                  background: disabled ? "#1a2332" : op.primary ? "#0284c7" : "#1e293b",
                  border: `1px solid ${disabled ? "#1e2d3f" : op.primary ? "#0284c7" : "#334155"}`,
                  color: disabled ? "#334155" : "#e2e8f0",
                  borderRadius: "8px",
                  padding: "0.875rem",
                  cursor: disabled ? "not-allowed" : "pointer",
                  textAlign: "center",
                  transition: "background 0.15s",
                }}
              >
                <div style={{ fontSize: "1.25rem", marginBottom: "0.25rem" }}>{op.icon}</div>
                <div style={{ fontWeight: 600, fontSize: "0.8rem" }}>{op.label}</div>
                <div style={{ fontSize: "0.72rem", color: disabled ? "#334155" : "#64748b" }}>{op.desc}</div>
              </button>
            );
          })}
        </div>
      </section>
    );
  }
  ```

- [ ] **Step 2: Create web/frontend/src/components/JobLog.tsx**

  ```tsx
  import { useEffect, useRef, useState } from "react";
  import { createLogSocket } from "../api";

  const LABEL: Record<string, string> = {
    incremental:   "Sync Incremental",
    full_load:     "Carga Completa",
    patients:      "Sync Pacientes",
    professionals: "Sync Profissionais",
    verify:        "Verificar Integridade",
  };

  function lineColor(line: string): string {
    if (line.includes("[OK]"))         return "#34d399";
    if (line.includes("[ERROR]") || line.includes("[BATCH ERROR]")) return "#f87171";
    if (line.includes("[FALLBACK]"))   return "#fbbf24";
    if (line.startsWith("==="))        return "#334155";
    return "#94a3b8";
  }

  interface Props {
    jobId: string | null;
    jobType: string | null;
    onDone: () => void;
  }

  export default function JobLog({ jobId, jobType, onDone }: Props) {
    const [lines, setLines] = useState<string[]>([]);
    const [running, setRunning] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      if (!jobId) return;
      setLines([]);
      setRunning(true);

      const ws = createLogSocket(jobId);

      ws.onmessage = (e) => {
        setLines(prev => [...prev, e.data as string]);
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
      };

      ws.onclose = () => {
        setRunning(false);
        onDone();
      };

      return () => ws.close();
    }, [jobId]);

    if (!jobId) return null;

    return (
      <section>
        <p style={{ color: "#64748b", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
          Log — {LABEL[jobType ?? ""] ?? jobType}{" "}
          <span style={{ color: running ? "#fbbf24" : "#34d399" }}>
            {running ? "● em execução" : "● concluído"}
          </span>
        </p>
        <div style={{ background: "#020617", borderRadius: "8px", padding: "1rem", fontFamily: "monospace", fontSize: "0.78rem", lineHeight: 1.6, height: "240px", overflowY: "auto" }}>
          {lines.map((line, i) => (
            <div key={i} style={{ color: lineColor(line) }}>{line || " "}</div>
          ))}
          {running && <div style={{ color: "#475569" }}>▌</div>}
          <div ref={bottomRef} />
        </div>
      </section>
    );
  }
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add web/frontend/src/components/OperationGrid.tsx web/frontend/src/components/JobLog.tsx
  git commit -m "feat: OperationGrid and JobLog components with WebSocket live streaming"
  ```

---

## Task 10: Dashboard page + end-to-end test

**Files:**
- Create: `web/frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Create web/frontend/src/pages/Dashboard.tsx**

  ```tsx
  import { useState } from "react";
  import { useNavigate } from "react-router-dom";
  import { clearToken, startJob } from "../api";
  import StatusCards from "../components/StatusCards";
  import OperationGrid from "../components/OperationGrid";
  import JobLog from "../components/JobLog";

  export default function Dashboard() {
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [jobId, setJobId] = useState<string | null>(null);
    const [jobType, setJobType] = useState<string | null>(null);
    const [running, setRunning] = useState(false);
    const navigate = useNavigate();

    async function handleStart(type: string) {
      try {
        const id = await startJob(type);
        setJobId(id);
        setJobType(type);
        setRunning(true);
      } catch (err) {
        alert((err as Error).message);
      }
    }

    function handleRefresh() {
      setRefreshTrigger(n => n + 1);
    }

    function handleJobDone() {
      setRunning(false);
      setRefreshTrigger(n => n + 1);
    }

    function handleLogout() {
      clearToken();
      navigate("/login");
    }

    return (
      <div style={{ background: "#0f172a", minHeight: "100vh", padding: "1.5rem" }}>
        <div style={{ maxWidth: "960px", margin: "0 auto" }}>
          <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "#1e293b", padding: "0.75rem 1.25rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
            <span style={{ color: "#38bdf8", fontWeight: 700, fontSize: "1rem" }}>⚡ Clinicorp ETL</span>
            <button onClick={handleLogout} style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer", fontSize: "0.875rem" }}>
              Sair
            </button>
          </header>

          <StatusCards refreshTrigger={refreshTrigger} />
          <OperationGrid running={running} onStart={handleStart} onRefresh={handleRefresh} />
          <JobLog jobId={jobId} jobType={jobType} onDone={handleJobDone} />
        </div>
      </div>
    );
  }
  ```

- [ ] **Step 2: Build frontend to verify TypeScript compiles cleanly**

  ```bash
  cd web/frontend && npm run build
  ```
  Expected: `dist/` folder created, no TypeScript errors.

- [ ] **Step 3: End-to-end manual test**

  Start backend:
  ```bash
  cd web/backend && ../../.venv/Scripts/uvicorn main:app --reload --port 8000
  ```

  Start frontend:
  ```bash
  cd web/frontend && npm run dev
  ```

  Open http://localhost:5173 and verify:
  1. Redirects to `/login`
  2. Login with credentials → redirects to `/`
  3. Dashboard shows DB counts (or `0` if DB is empty)
  4. Click "Sync Incremental" → log panel appears, output streams live
  5. After job completes → counts refresh automatically
  6. Click "Sair" → redirects to login

- [ ] **Step 4: Commit**

  ```bash
  git add web/frontend/src/pages/Dashboard.tsx
  git commit -m "feat: Dashboard page wiring StatusCards + OperationGrid + JobLog"
  ```

---

## Task 11: Production build setup

**Files:**
- Create: `web/start.ps1` (Windows launcher)

- [ ] **Step 1: Build frontend for production**

  ```bash
  cd web/frontend && npm run build
  ```
  Expected: `web/frontend/dist/` created with `index.html` and assets.

- [ ] **Step 2: Verify backend serves the static build**

  Start backend without `--reload` to simulate production:
  ```bash
  cd web/backend && ../../.venv/Scripts/uvicorn main:app --host 0.0.0.0 --port 8000
  ```

  Open http://localhost:8000 — should show the React app (login page). The API and frontend now come from the same server.

- [ ] **Step 3: Create web/start.ps1**

  ```powershell
  # Builds frontend and starts the production server
  Write-Host "Building frontend..."
  Set-Location "$PSScriptRoot\frontend"
  npm run build

  Write-Host "Starting backend server on port 8000..."
  Set-Location "$PSScriptRoot\backend"
  & "..\..\\.venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8000
  ```

- [ ] **Step 4: Add .superpowers to .gitignore**

  Append to `.gitignore` (create it if it doesn't exist):
  ```
  .superpowers/
  web/frontend/node_modules/
  web/frontend/dist/
  ```

- [ ] **Step 5: Final commit**

  ```bash
  git add web/start.ps1 .gitignore
  git commit -m "feat: production build script and .gitignore for web artifacts"
  ```

---

## VPS Migration (after local testing is complete)

This is not a task in this plan — do it once the local version is fully tested.

Steps when ready:
1. Install PostgreSQL on VPS, run `schema.sql`, copy data
2. `scp` or `git clone` project to VPS
3. Update `DATABASE_URL` in `.env` to point to VPS postgres
4. `pip install -r web/backend/requirements.txt`
5. `npm install && npm run build` in `web/frontend/`
6. Run: `uvicorn web.backend.main:app --host 0.0.0.0 --port 8000`
7. Configure a systemd service or PM2 to keep it running
