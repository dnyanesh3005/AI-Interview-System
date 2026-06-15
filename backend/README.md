# 🚀 AIMI FastAPI Backend: AI-Powered Candidate Screening

This directory contains the production FastAPI backend for **AIMI**, an intelligent, adaptive interview platform. The backend handles resume parsing, persistent SQLite database operations, user JWT authentication, custom **Hybrid dense-sparse RAG retrieval**, dynamic resume-grounded question generation, WebM video response uploads, and deep **Gemini-based transcript evaluation**.

---

## 🏗️ Architecture & Core Modules

The backend architecture is highly modular, split across distinct controllers in the root and processing services in `modules/`:

### 1. Unified Router & Server (`main.py`)
*   Serves as the central API gateway using FastAPI.
*   Enforces secure API usage by wrapping interactive routes in JWT verification middleware (`HTTPBearer`).
*   Configures and mounts strict CORS handling rules to safely bridge frontend domains.
*   Provides robust endpoints for registering profiles, logging in, parsing files, conducting interviews, submitting WebM video responses, skipping questions, resuming session states, and generating analytical reviews.

### 2. Resume Parser (`modules/resume_parser.py`)
*   Extracts raw character text from PDF, DOCX, and TXT files using specialized parsers.
*   Identifies target skills, toolsets, domains, and years of experience.
*   Constructs a **Candidate Knowledge Graph** mapping project whitelists and work histories to specific technologies, laying the groundwork for strict whitelisted question generation.

### 3. Hybrid RAG Pipeline (`modules/rag_pipeline.py`)
*   Manages two vector semantic layers:
    1.  **Curated Role Knowledge:** Long-form theoretical guidelines mapped to 7 key tech domains.
    2.  **Session-specific Resume Index:** Constructed lazily when a candidate launches an interview from their parsed resume.
*   **Dual-layer Retrieval:** Focuses 85% of question retrieval on the candidate's actual resume context and 15% on theoretical role knowledge.
*   **Dense-Sparse Fusion:** Computes semantic cosine similarity via a Flat Inner-Product **FAISS** index (`all-MiniLM-L6-v2`) and matches lexical tokens via a **BM25** index.
*   **Reciprocal Rank Fusion (RRF):** Synthesizes results from FAISS and BM25 to produce a single, high-relevance context block.

### 4. LLM Service (`modules/llm_service.py`)
*   Manages direct connectivity to Google Gemini (`gemini-2.5-flash` via the `google-genai` client) with a fallback to OpenAI (`gpt-3.5-turbo`) if configured.
*   Assembles whitelisted, highly constrained prompts enforcing beginner-to-intermediate level, resume-grounded, and concise single-sentence questions under 25 words.
*   Actively filters out advanced infrastructure, distributed architecture, MLOps, or complex concurrency topics unless explicitly found in the candidate's resume.

### 5. Adaptive Question Generator (`modules/question_generator.py`)
*   Guides the structural state of the interview by rotating questions across 6 distinct categories: *Conceptual, Project-based, Debugging, Deployment, Scenario-based, and Real-world*.
*   **Grounding Validation:** Scans proposed LLM questions against the candidate's resume whitelist. Rejects and regenerates any questions attempting to reference unlisted technologies or generic placeholder phrasing.
*   **Advanced Deduplication:** Encodes generated questions via SentenceTransformers and checks cosine proximity against previously asked questions in the database (current and cross-session). Blocks any question with a similarity score $\ge 0.75$.

### 6. Candidate Evaluator (`modules/evaluation.py`)
*   Invoked on interview completion to perform a comprehensive candidate audit.
*   Pulls full Q&A transcripts and runs them through the **Gemini 2.5 Flash API** using a structured JSON schema.
*   Computes scores (0-100) for individual skills, overall technical accuracy, communication clarity, and confidence.
*   Provides qualitative assessments detailing strengths, weak areas, and project-specific suggestions.
*   **Heuristic Fallback:** Implements a keyword density and answer length heuristic evaluator to ensure a report is returned even if the LLM API is unavailable.

### 7. Database Engine (`modules/database.py`)
*   Provides a persistent transactional SQLite interface.
*   Manages tables for `users` (credentials hashed with PBKDF2), `sessions`, `questions` (with category and difficulty metadata), `answers` (with timing and video file paths), and `metadata`/`evaluations`.

### 8. Session Manager (`modules/session_manager.py`)
*   Orchestrates the active lifecycles of candidate interviews.
*   Coordinates with the database to resume in-progress interviews, rebuild temporary FAISS indices, and restore the question category queue.

---

## 🗄️ Database Schema Representation

The relational persistence layer is designed as follows:

```
users
 └── id (UUID Primary Key)
      ├── username (Unique)
      ├── email (Unique)
      └── password_hash (PBKDF2)

sessions
 └── id (UUID Primary Key)
      ├── user_id (Foreign Key ──> users.id)
      ├── candidate_name
      ├── role
      ├── resume_data (JSON BLOB)
      ├── total_questions (Default: 5)
      ├── status ("in_progress" | "completed")
      └── created_at

questions
 └── id (Primary Key)
      ├── session_id (Foreign Key ──> sessions.id)
      ├── question_number
      ├── question_text
      ├── question_type
      ├── difficulty
      ├── category
      ├── context_used (JSON BLOB)
      └── created_at

answers
 └── id (Primary Key)
      ├── session_id (Foreign Key ──> sessions.id)
      ├── question_id (Foreign Key ──> questions.id)
      ├── answer_text
      ├── duration_seconds
      ├── video_path (Path to local WebM file)
      └── created_at
```

---

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.9+
*   Virtualenv tool (`python -m venv`)

### Deployment
1.  **Clone the directory & create environment:**
    ```bash
    cd backend
    python -m venv venv
    ```

2.  **Activate virtual environment:**
    *   **Windows:** `.\venv\Scripts\activate`
    *   **macOS / Linux:** `source venv/bin/activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `faiss-cpu`, `sentence-transformers`, `rank-bm25`, and `scikit-learn` will be fetched automatically.*

4.  **Establish Environment Keys:**
    Create a `.env` file at the root of `/backend`:
    ```ini
    JWT_SECRET=generate-a-secure-random-key-in-production
    GEMINI_API_KEY=AIzaSy...your-gemini-key
    CORS_ORIGINS=["http://localhost:5173"]
    ```

5.  **Run Server:**
    ```bash
    python main.py
    ```

---

## 🧪 Detailed API Endpoints

### 🔑 User Access Control
*   `POST /api/auth/register` - Create user profile.
*   `POST /api/auth/login` - Exchange credentials for a secure JWT.

### 📄 Parser & Setup
*   `POST /api/upload-resume` - Upload a resume file, parse skills, domains, and build knowledge graphs.
*   `POST /api/select-role` - Loads the specialized RAG knowledge base.

### ⏱️ Active Interview Flow
*   `POST /api/start-interview` - Create a session, build lazy RAG indices, and serve question 1.
*   `POST /api/resume-interview/{session_id}` - Rebuild indices and resume an unfinished session.
*   `POST /api/submit-answer` - Upload text answer, duration, and WebM video file, then receive the next question.
*   `POST /api/skip-question` - Register question as `[SKIPPED]` and retrieve the next question.

### 📊 Reports & Management
*   `GET /api/interview-summary/{session_id}` - Retrieve Q&A transcript and complete evaluation report.
*   `GET /api/evaluation/{session_id}` - Get/regenerate transcript evaluation reports.
*   `GET /api/sessions` - List all sessions under the authenticated user.
*   `DELETE /api/sessions/{session_id}` - Cleanly remove a session, all its Q&As, and video files.

---

## 🛡️ Production & Security Safeguards

1.  **JWT Verification:** Interactive session routes require the `Authorization: Bearer <token>` header, verified against `JWT_SECRET`.
2.  **PBKDF2 Password Hashing:** User passwords are encrypted with randomly generated salts using PBKDF2 with SHA256.
3.  **File Validation:** Strict filename extensions checking (PDF, DOCX, TXT) and content verification before processing.
4.  **CORS Handling:** Custom CORS middleware automatically sanitizes allowed domains, ensuring unauthorized sites cannot query endpoints.
5.  **Volume Persistence:** In production (e.g. Railway), database `interview_system.db` and video `recordings/` must be mounted on a persistent volume (e.g. Mount Path `/app`) to ensure they survive deployment restarts.