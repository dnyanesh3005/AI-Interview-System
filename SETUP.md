# Complete Setup Guide - AI Candidate Screening System

This guide will walk you through setting up the complete system from scratch.

## Prerequisites

Before starting, ensure you have:
- **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- **Node.js 16+** installed ([Download](https://nodejs.org/))
- **Git** installed ([Download](https://git-scm.com/))
- A code editor (VS Code recommended)
- 2GB free disk space

### Verify Installations

```bash
python --version        # Should be 3.9 or higher
node --version         # Should be 16 or higher
npm --version          # Should be 7 or higher
git --version          # Should be 2.30 or higher
```

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
- And other dependencies

**First-time setup note**: First run will download the embedding model (~400MB). This is normal.

#### 2.4 Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
# nano .env  (or use your editor)
```

**Important .env values:**
```
HOST=0.0.0.0
PORT=8000
DEBUG=True
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### 2.5 Verify Backend Setup

```bash
# Test imports
python -c "import fastapi; import sentence_transformers; print('✓ All imports successful')"

# Run server
python main.py
```

Expected output:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open**, the backend will run here.

#### API Documentation

Once backend is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Step 3: Frontend Setup (Node.js/React)

#### 3.1 Open New Terminal, Navigate to Frontend

```bash
# In a new terminal window
cd frontend
```

#### 3.2 Install Dependencies

```bash
npm install
```

This installs:
- React 18
- React Router
- Vite (build tool)
- And other dependencies

#### 3.3 Configure Environment

```bash
# Create .env.local file
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env.local

# Verify file was created
cat .env.local
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

### Step 4: Test the System

#### 4.1 Test Resume Upload

1. Go to http://localhost:5173
2. Click upload area or drag & drop
3. Select a resume file (create a test one if needed)
4. Click "Upload Resume"

Expected result: Resume data extracted successfully

#### 4.2 Test Role Selection

1. After upload, see the role selection page
2. Click any role card
3. Click "Start Interview"

Expected result: Interview starts with first question

#### 4.3 Test Interview Flow

1. Read the question
2. Type an answer in the textarea
3. Click "Submit Answer"
4. See the next question

This repeats 5 times, then shows the summary.

## Troubleshooting Setup

### Backend Issues

#### Error: "Python not found"
```bash
# Use python3 instead
python3 -m venv venv
python3 main.py
```

#### Error: "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

#### Error: "Address already in use"
```bash
# Port 8000 is already in use, either:
# Option 1: Kill the process using port 8000
# Option 2: Change PORT in .env
PORT=8001
# Then run: python main.py
```

#### Error: "SSL certificate verify failed"
```bash
# For embeddings download issues
pip install --upgrade certifi
```

### Frontend Issues

#### Error: "npm: command not found"
```bash
# Node.js not installed
# Download from https://nodejs.org/
# Then restart terminal and try again
```

#### Error: "Port 5173 already in use"
```bash
# Use different port
npm run dev -- --port 3000
```

#### Error: "Cannot GET /api/..."
```bash
# Backend not running
# Ensure backend server is running on http://localhost:8000
# Check REACT_APP_API_URL in .env.local
```

### Database Issues

#### Error: "database is locked"
```bash
# Close other connections
# Delete interview_system.db and restart
rm interview_system.db
python main.py
```

#### Reset Database
```bash
# Backend directory
rm interview_system.db
# Backend will recreate it on next run
```

## Project Structure Verification

After setup, verify your structure:

```bash
# From root directory
tree -I 'node_modules|venv|*.db' -L 3

# Or manually check:
ls -la backend/
ls -la frontend/
ls -la backend/modules/
```

## Configuration Details

### Backend .env Options

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

### Frontend .env Options

```
REACT_APP_API_URL=http://localhost:8000/api
```

## Production Deployment

### Backend (Python)

#### Option 1: Heroku

```bash
# Install Heroku CLI
# Login and create app
heroku create your-app-name

# Deploy
git push heroku main
```

#### Option 2: Docker

```bash
# Create Dockerfile in backend/
# Build image
docker build -t ai-interview-backend .

# Run container
docker run -p 8000:8000 ai-interview-backend
```

#### Option 3: Cloud Platforms

- **Railway**: Push to Git, auto-deploys
- **Render**: Push to Git, auto-deploys
- **PythonAnywhere**: Upload files, configure
- **Replit**: Import repo, click Run

### Frontend (React)

#### Option 1: Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel
```

#### Option 2: Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Build and deploy
cd frontend
npm run build
netlify deploy --prod --dir=dist
```

#### Option 3: GitHub Pages

```bash
# Update package.json
"homepage": "https://yourusername.github.io/repo-name"

# Build
npm run build

# Deploy (requires gh-pages package)
npm run deploy
```

## Development Workflow

### During Development

1. **Terminal 1 - Backend**
   ```bash
   cd backend
   source venv/bin/activate  # or activate.bat on Windows
   python main.py
   ```

2. **Terminal 2 - Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:5173 in browser

### Making Changes

- **Backend changes**: Auto-reload with `--reload` flag
  ```bash
  python main.py  # With reload enabled
  ```

- **Frontend changes**: Auto-reload with hot module replacement (HMR)
  ```bash
  npm run dev  # Auto-refreshes on save
  ```

## Testing the System

### Manual Test Cases

#### Test 1: Complete Interview Flow
```
1. Upload a resume (PDF/TXT/DOCX)
2. Select a role
3. Answer all 5 questions
4. Verify summary displays
5. Download summary
```

#### Test 2: Multiple Sessions
```
1. Complete first interview
2. Start new interview
3. Upload different resume
4. Complete second interview
5. Verify both in sessions list
```

#### Test 3: Database Persistence
```
1. Complete an interview
2. Stop backend server
3. Restart backend server
4. Verify session still exists in list
```

#### Test 4: Resume Parsing
```
1. Try uploading different file types (.pdf, .txt)
2. Verify all are parsed correctly
3. Check extracted fields (skills, experience, etc.)
```

## Next Steps

### After Successful Setup

1. **Test with Sample Data**
   - Create a test resume
   - Go through complete interview flow
   - Verify all features work

2. **Customize Questions**
   - Edit knowledge bases in `rag_pipeline.py`
   - Add your own domain knowledge
   - Test question generation

3. **Deploy to Production**
   - Choose hosting platform
   - Set up environment variables
   - Deploy both backend and frontend
   - Configure custom domain (optional)

4. **Monitor and Maintain**
   - Check server logs regularly
   - Back up database periodically
   - Update dependencies monthly
   - Monitor API performance

## Additional Resources

### Official Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Node.js Docs](https://nodejs.org/docs/)
- [SQLite Docs](https://www.sqlite.org/docs.html)

### Tutorials & Guides
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [React Tutorial](https://react.dev/learn)
- [Vite Guide](https://vitejs.dev/guide/)

### Community & Support
- [Stack Overflow](https://stackoverflow.com/)
- [GitHub Discussions](https://github.com/)
- [Reddit r/learnprogramming](https://reddit.com/r/learnprogramming/)

## Getting Help

If you encounter issues:

1. **Check the logs**: Look at terminal output for error messages
2. **Read error messages**: They often indicate the solution
3. **Check this guide**: Look for your issue in Troubleshooting
4. **Search online**: Copy error message and search
5. **Create an issue**: Document your setup and error

## Quick Command Reference

```bash
# Backend
cd backend
python -m venv venv              # Create venv
source venv/bin/activate         # Activate (macOS/Linux)
venv\Scripts\activate            # Activate (Windows)
pip install -r requirements.txt  # Install deps
python main.py                   # Run server

# Frontend
cd frontend
npm install                      # Install deps
npm run dev                      # Development server
npm run build                    # Production build
npm run preview                  # Preview build

# Database
rm backend/interview_system.db   # Reset database

# Testing
curl http://localhost:8000/health        # Check backend
curl http://localhost:5173               # Check frontend
```

---

**You're all set! Happy interviewing! 🚀**