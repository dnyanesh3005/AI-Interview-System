# AI-Powered Candidate Screening System

A comprehensive, production-grade intelligent interview system that uses **Retrieval-Augmented Generation (RAG)** to dynamically generate technical interview questions based on candidates' resumes and target roles.

## 🎯 System Overview

This full-stack application implements:

- **Resume Parsing**: Extract structured data from PDF/TXT/DOCX files
- **RAG Pipeline**: Semantic retrieval from role-specific knowledge bases
- **Dynamic Question Generation**: Context-aware questions that adapt to candidate background
- **Interactive Interview Flow**: Real-time question delivery and answer collection
- **Session Management**: Complete interview history and analytics
- **Performance Analytics**: Interview summary with insights and recommendations

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLite (Persistent storage)
- Sentence Transformers (Embeddings & semantic search)
- PyPDF2 (Resume parsing)
- Uvicorn (ASGI server)

**Frontend:**
- React 18 (UI framework)
- React Router (Navigation)
- Vite (Build tool) — env vars use `VITE_*` prefix via `import.meta.env`
- CSS 3 (Styling)

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                     │
│  ┌─────────┬──────────┬─────────┬─────────┬───────────┐ │
│  │ Resume  │  Role    │Interview│ Summary │ Sessions  │ │
│  │ Upload  │ Select   │  Flow   │ View    │ List      │ │
│  └─────────┴──────────┴─────────┴─────────┴───────────┘ │
└────────────────────────┬────────────────────────────────┘
                        │ HTTP/REST API
┌────────────────────────▼────────────────────────────────┐
│                  Backend (FastAPI)                      │
│  ┌──────────┬───────────┬──────────┬──────────────────┐ │
│  │ Resume   │ Question  │ Session  │ Database         │ │
│  │ Parser   │ Generator │ Manager  │ Module           │ │
│  └──────────┴───────────┴──────────┴──────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │     RAG Pipeline (Embeddings & Retrieval)        │  │
│  │  ┌──────────┐ ┌─────────┐ ┌──────────────────┐ │  │
│  │  │Knowledge │ │Embedding│ │Vector Similarity │ │  │
│  │  │Ingestion │ │Generation│ │Search            │ │  │
│  │  └──────────┘ └─────────┘ └──────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Database (SQLite)                      │  │
│  │  Sessions | Questions | Answers | Metadata     │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## 📋 Project Structure

```
.
├── backend/
│   ├── main.py                          # FastAPI application
│   ├── requirements.txt                 # Python dependencies
│   ├── .env.example                     # Environment template
│   ├── .env                             # Active environment config
│   ├── interview_system.db              # SQLite database (generated)
│   ├── README.md                        # Backend documentation
│   └── modules/
│       ├── resume_parser.py             # Resume extraction
│       ├── rag_pipeline.py              # RAG implementation
│       ├── question_generator.py        # Question creation
│       ├── database.py                  # Data persistence
│       ├── session_manager.py           # Session lifecycle
│       └── __init__.py
│
├── frontend/
│   ├── package.json                     # Node dependencies
│   ├── vite.config.js                   # Vite configuration
│   ├── .env.local                       # Frontend env (VITE_API_URL)
│   ├── index.html                       # HTML entry point
│   └── src/
│       ├── App.jsx                      # Main app component
│       ├── App.css                      # Global styles
│       ├── main.jsx                     # React entry point
│       └── components/
│           ├── ResumeUpload.jsx         # Resume upload UI
│           ├── ResumeUpload.css
│           ├── RoleSelection.jsx        # Role selection UI (fixed)
│           ├── RoleSelection.css
│           ├── InterviewFlow.jsx        # Interview UI (fixed)
│           ├── InterviewFlow.css
│           ├── InterviewSummary.jsx     # Summary UI (fixed)
│           ├── InterviewSummary.css
│           ├── SessionsList.jsx         # Sessions list UI (fixed)
│           ├── SessionsList.css
│           ├── Navigation.jsx           # Navigation bar
│           └── Navigation.css
│
├── README.md                            # This file
└── SETUP.md                             # Detailed setup guide
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn
- Git

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the server**
   ```bash
   python main.py
   # Server will start on http://localhost:8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create environment file** (⚠️ must use `VITE_` prefix for Vite)
   ```bash
   echo "VITE_API_URL=http://localhost:8000/api" > .env.local
   ```

4. **Run development server**
   ```bash
   npm run dev
   # Frontend will start on http://localhost:5173
   ```

5. **Build for production**
   ```bash
   npm run build
   ```

## 📖 API Endpoints

### Resume Management
```
POST /api/upload-resume
Upload and parse resume file
Response: { success, data, extracted_fields }
```

### Role Management
```
POST /api/select-role
Select target job role
Request: { role }
Response: { success, role, knowledge_base_loaded, message }
```

### Interview Management
```
POST /api/start-interview
Initialize interview session
Request: resume_data (+ role field)
Response: { success, session_id, question, question_number, total_questions }

POST /api/submit-answer
Submit answer and get next question
Request: { session_id, question_id, answer, duration_seconds }
Response: { interview_complete, question } OR { success, interview_complete: true }

GET /api/interview-summary/{session_id}
Get complete interview summary
Response: { summary: { session_id, candidate_name, qa_pairs, analysis } }

GET /api/sessions
List all interview sessions
Response: { sessions, count }
```

## 🎓 Supported Roles

1. **Backend Engineer** - APIs, databases, system design
2. **AI/ML Engineer** - Machine learning, deep learning, NLP
3. **Full Stack Engineer** - Frontend + backend development
4. **Data Scientist** - Analytics, statistical modeling, insights
5. **DevOps Engineer** - Infrastructure, CI/CD, cloud platforms

## 🧠 RAG Pipeline Design

### Knowledge Ingestion
- Role-specific curated knowledge bases
- Semantic chunking (500 character chunks with 100 char overlap)
- Embedding generation using sentence-transformers (all-MiniLM-L6-v2)

### Retrieval Mechanism
- Query construction from resume and role context
- Cosine similarity-based search
- Top-k retrieval with similarity threshold (>0.3)

### Question Generation
- Template-based with dynamic filling
- Multiple question types: Conceptual, Applied, Challenge, Experience
- Adaptive difficulty based on experience level
- Context-aware using retrieved knowledge

## 📊 Database Schema

**Sessions Table**
- Stores interview session metadata
- Tracks candidate info, role, timestamps, status

**Questions Table**
- Stores generated questions with metadata
- Includes question type, difficulty, category, context

**Answers Table**
- Stores candidate responses
- Tracks answer timing and metadata

**Interview Metadata Table**
- Performance metrics and analysis
- Session duration and statistics

## 🔄 Interview Flow

```
1. Resume Upload
   └─> Parse resume → Extract skills, experience, domain

2. Role Selection
   └─> Select role card → Click "Start Interview" → Load KB → Initialize RAG

3. Interview Start
   └─> Generate Q1 → Create session → Store question → Display immediately

4. Question → Answer Loop (5 iterations)
   ├─> Display question (passed directly from API response)
   ├─> Candidate provides answer
   ├─> Store answer
   ├─> Retrieve context → Generate next question
   └─> Repeat until completion

5. Interview Completion
   └─> Analyze responses → Generate summary → Display results
```

## 🐛 Known Issues Fixed

| Issue | Root Cause | Fix Applied |
|-------|-----------|------------|
| Role selection didn't proceed | Card click called `onSelect` immediately, button double-called it → race condition | Separated card click (local state) from button (single API call) |
| Interview screen blank (no question) | First question from `/api/start-interview` was discarded in App.jsx | Store `data.question` in state, pass as `initialQuestion` to `InterviewFlow` |
| Env vars not resolving | Used `process.env.REACT_APP_*` (CRA syntax) in Vite project | Changed to `import.meta.env.VITE_*` across all components + `.env.local` |

## 🔒 Security Considerations

- Input validation on all endpoints
- File type and size validation for resume uploads
- Sanitized database queries (parameterized)
- CORS configuration for cross-origin requests
- Consider adding authentication for production

## 🚀 Deployment

### Backend Deployment
```bash
# Using Gunicorn
gunicorn main:app --workers 4 --timeout 60 -k uvicorn.workers.UvicornWorker

# Using Docker
docker build -t ai-interview-backend .
docker run -p 8000:8000 ai-interview-backend
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Deploy to Vercel/Netlify
vercel deploy
# or
netlify deploy --prod --dir=dist
```

## 📝 Example Usage

### 1. Upload Resume
```bash
curl -X POST http://localhost:8000/api/upload-resume \
  -F "file=@resume.pdf"
```

### 2. Select Role
```bash
curl -X POST http://localhost:8000/api/select-role \
  -H "Content-Type: application/json" \
  -d '{"role": "Backend Engineer"}'
```

### 3. Start Interview
```bash
curl -X POST http://localhost:8000/api/start-interview \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "John Doe",
    "role": "Backend Engineer",
    "skills": ["Python", "FastAPI"],
    "experience_years": 3
  }'
```

### 4. Submit Answer
```bash
curl -X POST http://localhost:8000/api/submit-answer \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "uuid",
    "question_id": "q1",
    "answer": "My answer to the question..."
  }'
```

## 🎯 Future Enhancements

- [ ] Integration with Claude/OpenAI API for natural question generation
- [ ] Real-time answer quality scoring using LLM
- [ ] Video recording and speech-to-text
- [ ] Multi-language support
- [ ] Collaborative interview features
- [ ] Advanced analytics dashboard
- [ ] Custom question templates
- [ ] Bulk interview scheduling
- [ ] Email notifications
- [ ] Mobile app version

## 📚 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Pattern](https://aws.amazon.com/blogs/machine-learning/rag-pattern-in-generative-ai/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Vite Env Variables](https://vitejs.dev/guide/env-and-mode.html)

## 📄 License

This project is part of the PG-AGI internship program.

---

**Built with ❤️ for the PG-AGI Internship Program**