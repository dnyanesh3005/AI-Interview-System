# Complete Setup Guide - AI Candidate Screening System

This guide walks you through setting up the complete system from scratch.

## Prerequisites

Before starting, ensure you have:
- **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- **Node.js 16+** installed ([Download](https://nodejs.org/))
- **Git** installed ([Download](https://git-scm.com/))
- A code editor (VS Code recommended)
- 2GB free disk space (for embedding model download)

### Verify Installations

```bash
python --version        # Should be 3.9 or higher
node --version          # Should be 16 or higher
npm --version           # Should be 7 or higher
git --version           # Should be 2.30 or higher
```

---

## Full Setup (End-to-End)

### Step 1: Clone/Setup Project

```bash
# Option A: If cloning from Git
git clone <repository-url>
cd ai-interview-system

# Option B: If files provided manually
mkdir ai-interview-system
cd ai-interview-system
# Copy all files to appropriate directories
```

---

### Step 2: Backend Setup (Python)

#### 2.1 Navigate to Backend

```bash
cd backend
```

#### 2.2 Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**Note**: You'll see `(venv)` prefix in your terminal when activated.

#### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- PyPDF2 (PDF parsing)
- sentence-transformers (embeddings)
- scikit-learn (similarity search)
- python-dotenv (environment config)

> **First-time setup note**: First run will download the embedding model (~400MB). This is normal and only happens once.

#### 2.4 Configure Environment

```bash
# Copy example env file
cp .env.example .env
```

**Important `.env` values:**
```
HOST=0.0.0.0
PORT=8000
DEBUG=True
EMBEDDING_MODEL=all-MiniLM-L6-v2
DATABASE_URL=sqlite:///./interview_system.db
```

#### 2.5 Run Backend Server

```bash
python main.py
```

Expected output:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open.** API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

### Step 3: Frontend Setup (Node.js/React)

#### 3.1 Open a New Terminal, Navigate to Frontend

```bash
cd frontend
```

#### 3.2 Install Dependencies

```bash
npm install
```

#### 3.3 Configure Environment

> ⚠️ **Important**: This project uses **Vite**, not Create React App.
> Environment variables **must** use the `VITE_` prefix and are accessed via `import.meta.env`.

```bash
# Create .env.local file with correct Vite prefix
echo "VITE_API_URL=http://localhost:8000/api" > .env.local

# Verify
cat .env.local
# Should output: VITE_API_URL=http://localhost:8000/api
```

#### 3.4 Start Development Server

```bash
npm run dev
```

Expected output:
```
  VITE v5.0.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

#### 3.5 Access the Application

Open your browser and visit: **http://localhost:5173**

You should see the resume upload interface.

---

### Step 4: Test the System

#### 4.1 Test Resume Upload

1. Go to http://localhost:5173
2. Click the upload area or drag & drop a resume file
3. Supported formats: `.pdf`, `.txt`, `.docx`
4. Click **"Upload Resume"**

✅ Expected: Resume data extracted and displayed, moves to role selection screen.

#### 4.2 Test Role Selection *(Fixed)*

1. After upload, you see the **role selection page**
2. **Click** any role card to select it (card highlights with ✓)
3. Click **"Start Interview"** button to proceed

✅ Expected: Interview begins with the first question displayed immediately.

> **Note**: Clicking a role card now only highlights it (local state). The API call only fires when you click "Start Interview" — preventing the previous double-call race condition.

#### 4.3 Test Interview Flow

1. Read the displayed question
2. Type your answer in the textarea
3. Click **"Submit Answer"**
4. Next question appears automatically

This repeats 5 times, then the summary screen is shown.

#### 4.4 Test Summary & Sessions

1. After 5 answers, the **Interview Summary** displays
2. Review Q&A pairs and performance analysis
3. Navigate to **/sessions** to see all past sessions

---

## Troubleshooting

### Backend Issues

#### Error: "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Ensure venv is activated
venv\Scripts\activate     # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall requirements
pip install -r requirements.txt
```

#### Error: "Address already in use" (port 8000)
```bash
# Option 1: Kill the process
# Windows: netstat -ano | findstr :8000
# Option 2: Change PORT in .env
PORT=8001
python main.py
```

#### Error: "SSL certificate verify failed"
```bash
pip install --upgrade certifi
```

#### Error: Database locked
```bash
# Delete and recreate
del backend\interview_system.db    # Windows
rm backend/interview_system.db     # macOS/Linux
python main.py
```

---

### Frontend Issues

#### Error: "Cannot find module" or blank page
```bash
# Reinstall node modules
rm -rf node_modules
npm install
npm run dev
```

#### Env var `VITE_API_URL` not working
```bash
# Wrong (CRA syntax - does NOT work in Vite):
# REACT_APP_API_URL=http://localhost:8000/api

# Correct (Vite syntax):
# VITE_API_URL=http://localhost:8000/api

# Check your .env.local file:
cat frontend/.env.local
# Must show: VITE_API_URL=http://localhost:8000/api

# Restart the dev server after editing .env.local
npm run dev
```

#### Error: "Cannot GET /api/..."
```bash
# Backend not running — start it:
cd backend && python main.py
# Then verify:
curl http://localhost:8000/health
```

#### Port 5173 already in use
```bash
npm run dev -- --port 3000
```

---

## Configuration Details

### Backend `.env` Options

```
# Server
HOST=0.0.0.0           # Listen on all interfaces
PORT=8000              # Port number
DEBUG=True             # Debug mode

# Database
DATABASE_URL=sqlite:///./interview_system.db

# RAG Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Lightweight embeddings
CHUNK_SIZE=500         # Document chunk size
CHUNK_OVERLAP=100      # Overlap between chunks
RETRIEVAL_TOP_K=5      # Top results to retrieve
```

### Frontend `.env.local` Options

```
VITE_API_URL=http://localhost:8000/api
```

> ⚠️ **Never** use `REACT_APP_*` prefix in this project — it's a Vite project, not Create React App.

---

## Bug Fixes Applied

The following bugs were identified and fixed in the codebase:

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `RoleSelection.jsx` | Clicking a role card immediately triggered the full API flow; the "Start Interview" button triggered it a second time (race condition) | Card click only updates local state; `onSelect()` is called once from the button |
| 2 | `App.jsx` + `InterviewFlow.jsx` | First question returned by `/api/start-interview` was discarded; `InterviewFlow` had `currentQuestion = null` with no fetch logic | App stores `data.question` and passes it as `initialQuestion` prop to `InterviewFlow` |
| 3 | All components | `process.env.REACT_APP_API_URL` doesn't work in Vite (CRA syntax) | Changed to `import.meta.env.VITE_API_URL` in all components + `.env.local` |

---

## Development Workflow

### Running Both Servers

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate   # Windows
python main.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

### Making Changes

- **Backend changes**: Auto-reloads via uvicorn `--reload` (already enabled in `main.py`)
- **Frontend changes**: Auto-reloads via Vite HMR on every save

---

## Production Deployment

### Backend

```bash
# Using Gunicorn + Uvicorn workers
gunicorn main:app --workers 4 -k uvicorn.workers.UvicornWorker --timeout 60

# Using Docker
docker build -t ai-interview-backend .
docker run -p 8000:8000 ai-interview-backend
```

### Frontend

```bash
# Build
npm run build

# Deploy to Vercel
vercel

# Deploy to Netlify
netlify deploy --prod --dir=dist
```

---

## Quick Command Reference

```bash
# ── Backend ──────────────────────────────────────
cd backend
python -m venv venv              # Create venv
venv\Scripts\activate            # Activate (Windows)
source venv/bin/activate         # Activate (macOS/Linux)
pip install -r requirements.txt  # Install deps
python main.py                   # Run server

# ── Frontend ─────────────────────────────────────
cd frontend
npm install                      # Install deps
npm run dev                      # Development server
npm run build                    # Production build
npm run preview                  # Preview build

# ── Database ─────────────────────────────────────
del backend\interview_system.db  # Reset DB (Windows)
rm backend/interview_system.db   # Reset DB (macOS/Linux)

# ── Health Checks ─────────────────────────────────
curl http://localhost:8000/health
curl http://localhost:5173
```

---

**You're all set! Happy interviewing! 🚀**