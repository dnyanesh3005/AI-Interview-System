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
- Vite (Build tool)
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
│   ├── index.html                       # HTML entry point
│   ├── README.md                        # Frontend documentation
│   └── src/
│       ├── App.jsx                      # Main app component
│       ├── App.css                      # Global styles
│       ├── main.jsx                     # React entry point
│       ├── components/
│       │   ├── ResumeUpload.jsx         # Resume upload UI
│       │   ├── ResumeUpload.css
│       │   ├── RoleSelection.jsx        # Role selection UI
│       │   ├── RoleSelection.css
│       │   ├── InterviewFlow.jsx        # Interview UI
│       │   ├── InterviewFlow.css
│       │   ├── InterviewSummary.jsx     # Summary UI
│       │   ├── InterviewSummary.css
│       │   ├── SessionsList.jsx         # Sessions list UI
│       │   ├── SessionsList.css
│       │   ├── Navigation.jsx           # Navigation bar
│       │   └── Navigation.css
│       └── services/
│           └── api.js                   # API client (optional)
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

3. **Create environment file**
   ```bash
   echo "REACT_APP_API_URL=http://localhost:8000/api" > .env.local
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
Response: { success, knowledge_base_loaded }
```

### Interview Management
```
POST /api/start-interview
Initialize interview session
Request: resume_data
Response: { session_id, question, question_number, total_questions }

POST /api/submit-answer
Submit answer and get next question
Request: { session_id, question_id, answer }
Response: { interview_complete, question } OR { success }

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
- Embedding generation using sentence-transformers

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
   └─> Load knowledge base → Initialize RAG pipeline

3. Interview Start
   └─> Generate Q1 → Create session → Store question

4. Question → Answer Loop (5 iterations)
   ├─> Display question
   ├─> Candidate provides answer
   ├─> Store answer
   ├─> Retrieve context → Generate next question
   └─> Repeat until completion

5. Interview Completion
   └─> Analyze responses → Generate summary → Display results
```

## 🎨 Key Features

### Resume Parsing
- Extracts: Name, email, phone, skills, experience, education, projects
- Supports: PDF, TXT, DOCX formats
- Uses regex patterns and domain knowledge

### Adaptive Question Generation
- Questions adapt to candidate's experience level
- Different difficulty levels: Basic, Intermediate, Advanced
- Variety of question types for comprehensive evaluation
- Grounded in actual knowledge base content

### Session Management
- Unique session IDs for each interview
- Real-time progress tracking
- Complete Q&A history preservation
- Performance metadata collection

### Analytics & Reporting
- Interview summary with all Q&A pairs
- Performance analysis (knowledge depth, technical accuracy, etc.)
- Recommendations for improvement
- Downloadable summary reports

## 🔒 Security Considerations

- Input validation on all endpoints
- File type and size validation for resume uploads
- Sanitized database queries (parameterized)
- CORS configuration for cross-origin requests
- Consider adding authentication for production

## 🚀 Deployment

### Backend Deployment
```bash
# Using Heroku
gunicorn main:app --workers 4 --timeout 60

# Using Docker
docker build -t ai-interview-backend .
docker run -p 8000:8000 ai-interview-backend

# Using Railway/Render
Just push to git, they'll deploy automatically
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

## 🐛 Troubleshooting

### Common Issues

**1. CORS Errors**
```
Solution: Update CORS_ORIGINS in backend .env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

**2. Resume Parsing Fails**
```
Solution: Ensure file is valid PDF/TXT/DOCX
Check file encoding for text files
```

**3. Questions Not Generating**
```
Solution: Ensure knowledge base loaded for role
Check RAG pipeline initialization
```

**4. Database Locked**
```
Solution: Close other connections to SQLite
Consider upgrading to PostgreSQL
```

## 🎯 Future Enhancements

- [ ] Integration with Claude API for natural question generation
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

## 📄 License

This project is part of the PG-AGI internship program.

## 👥 Contributing

For contributions, please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend/README.md
3. Check frontend components for usage examples
4. Create an issue on GitHub

## 🎥 Demo Video

See the DEMO.md file for instructions on creating a demo video showcasing the system.

---

**Built with ❤️ for the PG-AGI Internship Program**