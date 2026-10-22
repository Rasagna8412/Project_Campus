# Project Campus — Local Experience & Developer Startup Guide

**Document Version:** 1.0.0  
**Status:** Approved for Local Exploration & Verification  
**Target Environment:** Local Windows / Linux / macOS Development Workstation  
**Backend Port:** `8000` (`http://127.0.0.1:8000`)  
**Frontend Port:** `5173` (`http://localhost:5173`)  
**Date:** October 2026  

---

## 1. Prerequisites

Ensure the following tools are installed on your machine before running Project Campus:

1. **Python 3.12+**
   * Check installation: `python --version` (or `py --version`)
   * Virtual environment support: `python -m venv`
2. **Node.js v20+ & npm v10+**
   * Check installation: `node -v` and `npm -v`
3. **PowerShell 7+ (or Windows PowerShell 5.1)**
   * Built-in to modern Windows environments.
4. **Git**
   * Check installation: `git --version`

> [!NOTE]
> Project Campus uses a dual-dialect database architecture. For local development and demonstration, it runs seamlessly on **SQLite (Async via `aiosqlite`)** without requiring a local PostgreSQL daemon or Docker installation. In staging and production, it transitions to **PostgreSQL 15+** via configuration.

---

## 2. Quick Setup & Environment Preparation

### 2.1. Clone and Navigate
```powershell
cd c:\Users\LOQ\OneDrive\Desktop\project_campus
```

### 2.2. Backend Python Virtual Environment
If `.venv` is not already activated or created:
```powershell
# Create virtual environment if missing
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt
```

### 2.3. Frontend Node Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 3. Database Initialization & Automated Seeding

The development database (`backend/project_campus_dev.db`) is pre-migrated to the latest Alembic revision head (`0cbebed2ada2`).

### 3.1. Verify Database Schema Migration
To verify or apply migrations to the local database:
```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

### 3.2. Automated Idempotent Seeding
When the FastAPI backend boots up, its `lifespan` handler automatically seeds initial data if missing:
1. **System Roles:** `STUDENT`, `EDUCATOR`, `REVIEWER`, `ADMIN`
2. **Curricula & Grades:** CBSE (Class 11, Class 12), JEE Main, NEET
3. **Core Subjects:** Physics, Chemistry, Mathematics, Biology
4. **Academic Content:** Chapters, Topics, Lessons, and Sections
5. **Question Bank:** Single-choice, multiple-choice, and numerical questions with educator answer keys.

---

## 4. Starting the Application Locally

To experience the full website, you will run the backend and frontend in two separate terminal windows.

### Terminal 1: Backend Server (FastAPI)
```powershell
cd c:\Users\LOQ\OneDrive\Desktop\project_campus\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected Output:*
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Terminal 2: Frontend Server (Vite)
Open a new PowerShell terminal:
```powershell
cd c:\Users\LOQ\OneDrive\Desktop\project_campus\frontend
npm run dev
```
*Expected Output:*
```
  VITE v5.4.21  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 5. Confirmed Local Access URLs

| Interface | URL | Purpose |
| :--- | :--- | :--- |
| **Main Website (Frontend SPA)** | [http://localhost:5173/](http://localhost:5173/) | Interactive student application, onboarding, lessons, practice, and planner |
| **API Health Check (Direct)** | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) | Backend health & version check (`{"status":"healthy","version":"0.1.0"}`) |
| **API Health Check (Vite Proxy)** | [http://localhost:5173/api/v1/health](http://localhost:5173/api/v1/health) | Verifies Vite reverse-proxy forwarding to FastAPI |
| **OpenAPI / Swagger Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive Swagger UI for testing all REST endpoints |
| **ReDoc Documentation** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Alternate static API reference |

---

## 6. How to Stop the Application

To shut down the servers cleanly:
1. In the **Frontend Terminal**, press `Ctrl + C` and confirm with `Y`.
2. In the **Backend Terminal**, press `Ctrl + C`.

If any process remains bound in the background:
```powershell
# Check processes occupying port 8000 and 5173
Get-NetTCPConnection -LocalPort 8000, 5173 -ErrorAction SilentlyContinue | Select-Object LocalPort, OwningProcess

# Kill process by PID if needed
Stop-Process -Id <PID> -Force
```

---

## 7. Troubleshooting Common Issues

### Issue 1: "Backend Server Unreachable" banner in the frontend
* **Cause:** The backend uvicorn process is not running on port 8000.
* **Fix:** Start the backend in Terminal 1 using `..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Once running, click **"Retry Live Ping"** on the frontend header.

### Issue 2: Port 8000 or 5173 already in use
* **Cause:** A previous background test or process is holding the port.
* **Fix:** Run `Get-NetTCPConnection -LocalPort 8000` to find the offending process ID, and terminate it with `Stop-Process -Id <PID> -Force`.

### Issue 3: Missing KaTeX mathematical formulas
* **Cause:** KaTeX fonts or CDN stylesheet blocked by browser extensions.
* **Fix:** Project Campus imports KaTeX from `cdn.jsdelivr.net`. Ensure your browser does not block CDN assets on `localhost`.

### Issue 4: Session token expired (HTTP 401 Unauthorized)
* **Cause:** Access tokens expire after 60 minutes.
* **Fix:** Click **"Sign Out"** in the top navigation bar and log back in, or register a new synthetic student account.
