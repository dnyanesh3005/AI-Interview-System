"""
FastAPI Backend — AI-Powered Candidate Screening System
Hybrid Agentic RAG + Gemini + Structured Resume Parsing + Candidate Evaluation
"""

# Load .env FIRST before any module reads os.getenv()
from dotenv import load_dotenv
load_dotenv()


from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
import uuid
import hashlib
import secrets
import re
import json
from datetime import datetime, timedelta
from io import BytesIO

from modules.resume_parser import ResumeParser
from modules.rag_pipeline import RAGPipeline
from modules.question_generator import QuestionGenerator
from modules.llm_service import LLMService
from modules.database import Database
from modules.session_manager import SessionManager
from modules.evaluation import CandidateEvaluator
from modules.transcription import Transcriber

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Candidate Screening System",
    description="Hybrid Agentic RAG-powered interview platform with Gemini",
    version="2.0.0",
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
cors_origins_env = os.getenv("CORS_ORIGINS")
cors_origins = []
if cors_origins_env:
    try:
        cors_origins = json.loads(cors_origins_env)
    except Exception:
        cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

# Safe defaults if not specified or contains wildcard (since allow_credentials=True prohibits wildcard)
if not cors_origins or "*" in cors_origins:
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Services ──────────────────────────────────────────────────────────────────
db              = Database()
session_manager = SessionManager(db)
resume_parser   = ResumeParser()
rag_pipeline    = RAGPipeline()
llm_service     = LLMService()
question_generator = QuestionGenerator(rag_pipeline, llm_service)
evaluator       = CandidateEvaluator()
transcriber     = Transcriber()

# ─── JWT ───────────────────────────────────────────────────────────────────────
import jwt
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

JWT_SECRET    = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {
            "id":       user_id,
            "username": payload.get("username"),
            "email":    payload.get("email"),
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ─── Auth helpers ──────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt_hex, key_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual   = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return secrets.compare_digest(expected, actual)
    except Exception:
        return False


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


# ─── Pydantic models ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email:    str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token returned by @react-oauth/google


class RoleSelection(BaseModel):
    role: str


class AnswerSubmission(BaseModel):
    session_id:       str
    question_id:      str
    answer:           str
    duration_seconds: Optional[int] = 0


class SkipQuestion(BaseModel):
    session_id:  str
    question_id: str


class InterviewSummaryResponse(BaseModel):
    session_id:      str
    candidate_name:  str
    role:            str
    total_questions: int
    answers:         List[dict]
    analysis:        Optional[dict] = None


# ══════════════════════════════════════════════════════════════════════════════
# API Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Candidate Screening System v2.0"}


# ─── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    username = req.username.strip()
    email    = req.email.strip()
    password = req.password

    if len(username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if not is_valid_email(email):
        raise HTTPException(400, "Invalid email format")
    if db.get_user_by_username(username):
        raise HTTPException(400, "Username already taken")
    if db.get_user_by_email(email):
        raise HTTPException(400, "Email already registered")

    user_id = str(uuid.uuid4())
    success = db.create_user(user_id, username, email, hash_password(password))
    if not success:
        raise HTTPException(500, "Could not create user")
    return {"success": True, "message": "User registered successfully"}


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = db.get_user_by_username(req.username.strip())
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")

    token = create_access_token({
        "id":       user["id"],
        "username": user["username"],
        "email":    user["email"],
    })
    return {
        "success": True,
        "token":   token,
        "user": {
            "user_id":  user["id"],
            "username": user["username"],
            "email":    user["email"],
        },
    }


@app.post("/api/auth/google")
async def google_auth(req: GoogleAuthRequest):
    """
    Verify a Google ID token from @react-oauth/google.
    Upsert the user (by google_id → by email → create new) and return an app JWT.
    """
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com":
        raise HTTPException(500, "Google OAuth is not configured. Set GOOGLE_CLIENT_ID in backend .env")

    try:
        id_info = google_id_token.verify_oauth2_token(
            req.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(401, f"Invalid Google token: {e}")

    google_id = id_info["sub"]
    email     = id_info.get("email", "")
    name      = id_info.get("name") or id_info.get("given_name") or email.split("@")[0]

    # 1. Check by google_id first (returning OAuth user)
    user = db.get_user_by_google_id(google_id)

    if not user:
        # 2. Check by email (existing password-based account → link it)
        existing = db.get_user_by_email(email)
        if existing:
            db.update_user_google_id(existing["id"], google_id)
            user = existing
        else:
            # 3. Brand-new user — create OAuth account
            user_id = str(uuid.uuid4())
            # Ensure username uniqueness if Google name clashes
            base_username = re.sub(r"[^a-zA-Z0-9_]", "", name.replace(" ", "_")) or "user"
            username = base_username
            suffix = 1
            while db.get_user_by_username(username):
                username = f"{base_username}_{suffix}"
                suffix += 1
            success = db.create_oauth_user(user_id, username, email, google_id)
            if not success:
                raise HTTPException(500, "Could not create user account")
            user = {"id": user_id, "username": username, "email": email}

    token = create_access_token({
        "id":       user["id"],
        "username": user["username"],
        "email":    user["email"],
    })
    logger.info(f"Google OAuth login: {email}")
    return {
        "success": True,
        "token":   token,
        "user": {
            "user_id":  user["id"],
            "username": user["username"],
            "email":    user["email"],
        },
    }


# ─── Resume Upload ─────────────────────────────────────────────────────────────

@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload and parse a resume file (PDF/DOCX/TXT).
    Returns structured resume data including knowledge graph.
    """
    try:
        if not file.filename.lower().endswith((".pdf", ".txt", ".docx")):
            raise HTTPException(400, "Invalid file type. Use PDF, TXT, or DOCX.")

        content = await file.read()

        try:
            resume_data = resume_parser.parse(content, file.filename)
        except Exception as e:
            logger.error(f"Resume parsing error: {e}")
            raise HTTPException(400, f"Could not parse resume: {e}")

        logger.info(
            f"Resume parsed for {resume_data.get('candidate_name')} | "
            f"{len(resume_data.get('skills', []))} skills | "
            f"{len(resume_data.get('projects', {}))} projects"
        )

        return {
            "success": True,
            "data":    resume_data,
            "extracted_fields": {
                "name":           resume_data.get("candidate_name", "Unknown"),
                "skills":         resume_data.get("skills", []),
                "tools":          resume_data.get("tools", []),
                "certifications": resume_data.get("certifications", []),
                "experience":     resume_data.get("experience_years", 0),
                "domain":         resume_data.get("domain", "General"),
                "projects": (
                    list(resume_data.get("projects").keys())
                    if isinstance(resume_data.get("projects"), dict)
                    else (
                        [
                            (p.get("name") or p.get("title") or str(p)) if isinstance(p, dict) else str(p)
                            for p in resume_data.get("projects")
                            if p
                        ]
                        if isinstance(resume_data.get("projects"), list)
                        else []
                    )
                ),
                "knowledge_graph": resume_data.get("knowledge_graph", {}),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(500, str(e))


# ─── Role Selection ────────────────────────────────────────────────────────────

@app.post("/api/select-role")
async def select_role(
    role_data: RoleSelection,
    current_user: dict = Depends(get_current_user),
):
    """Select target job role and load its knowledge base."""
    SUPPORTED_ROLES = [
        "Backend Engineer", "AI/ML Engineer", "Full Stack Engineer",
        "Data Scientist", "DevOps Engineer", "Frontend Developer", "Data Analyst",
    ]
    if role_data.role not in SUPPORTED_ROLES:
        raise HTTPException(
            400,
            f"Unsupported role. Choose from: {', '.join(SUPPORTED_ROLES)}",
        )
    try:
        kb_status = rag_pipeline.load_knowledge_base(role_data.role)
        return {
            "success":              True,
            "role":                 role_data.role,
            "knowledge_base_loaded": kb_status,
            "message":              f"Knowledge base for {role_data.role} loaded",
        }
    except Exception as e:
        logger.error(f"Role selection error: {e}")
        raise HTTPException(500, str(e))


# ─── Start Interview ───────────────────────────────────────────────────────────

@app.post("/api/start-interview")
async def start_interview(
    resume_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Initialise an interview session and return the first question.
    Builds the per-session resume FAISS index.
    """
    try:
        if not resume_data.get("candidate_name"):
            raise HTTPException(400, "candidate_name required")
        if not resume_data.get("role"):
            raise HTTPException(400, "role required")

        total_questions = int(resume_data.get("total_questions", 5))
        role = resume_data["role"]

        # Ensure role KB is loaded
        rag_pipeline.load_knowledge_base(role)

        # Create session
        session = session_manager.create_session(
            candidate_name=resume_data["candidate_name"],
            role=role,
            resume_data=resume_data,
            user_id=current_user["id"],
            total_questions=total_questions,
        )
        session_id = session["session_id"]

        # Build per-session resume FAISS index
        rag_pipeline.build_resume_index(session_id, resume_data)

        # Initialise question generator state
        question_generator.init_session(session_id)

        # Generate first question
        question = question_generator.generate_question(
            session_id=session_id,
            resume_data=resume_data,
            question_number=1,
            previous_context=None,
        )

        db.store_question(session_id, question)

        logger.info(f"Interview started: {session_id}")
        return {
            "success":         True,
            "session_id":      session_id,
            "question":        question,
            "question_number": 1,
            "total_questions": total_questions,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview start error: {e}")
        raise HTTPException(500, str(e))


# ─── Resume Interview ──────────────────────────────────────────────────────────

@app.post("/api/resume-interview/{session_id}")
async def resume_interview(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Resume an in-progress interview session.
    Rebuilds the FAISS index and restores the interview state.
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(403, "Unauthorized")
        if session.get("status") != "in_progress":
            raise HTTPException(400, "Only in-progress interviews can be resumed")

        role = session["role"]
        resume_data = session["resume_data"]
        total_questions = _safe_total_questions(session)

        # Ensure role KB is loaded
        rag_pipeline.load_knowledge_base(role)

        # Build per-session resume FAISS index
        rag_pipeline.build_resume_index(session_id, resume_data)

        # Restore question generator state
        qa_pairs = db.get_qa_pairs(session_id)
        question_generator.init_session(session_id)
        state = question_generator._session_state[session_id]

        for pair in qa_pairs:
            question_text = pair["question"]
            category = pair["category"]
            state["asked_texts"].append(question_text)
            state["covered_categories"].append(category)
            try:
                if not hasattr(question_generator, "_embed_model"):
                    from sentence_transformers import SentenceTransformer
                    question_generator._embed_model = SentenceTransformer("all-MiniLM-L6-v2")
                emb = question_generator._embed_model.encode([question_text], convert_to_numpy=True)
                state["asked_embeddings"].append(emb)
            except Exception as e:
                logger.warning(f"Could not restore embedding during resume: {e}")

        # Determine current progress & active question
        answer_count = db.get_answer_count(session_id)

        # Find first unanswered question
        active_question = None
        for pair in qa_pairs:
            if pair.get("answer") is None:
                active_question = {
                    "question_id": f"{session_id}_q{pair['question_number']}",
                    "question_number": pair["question_number"],
                    "question_text": pair["question"],
                    "question_type": pair["question_type"],
                    "difficulty": pair["difficulty"],
                    "category": pair["category"],
                    "expected_depth": {
                        "Basic": "2-3 minutes, focus on fundamentals",
                        "Intermediate": "3-5 minutes, demonstrate working knowledge",
                    }.get(pair["difficulty"], "3-5 minutes"),
                    "context_used": []
                }
                break

        # If all questions asked are answered, generate the next one
        if not active_question:
            next_q_num = answer_count + 1
            if next_q_num <= total_questions:
                previous_context = None
                if answer_count > 0:
                    last_answered = None
                    for pair in reversed(qa_pairs):
                        if pair.get("answer") is not None:
                            last_answered = pair
                            break
                    if last_answered:
                        previous_context = {
                            "previous_question": last_answered["question"],
                            "previous_answer": last_answered["answer"]
                        }

                active_question = question_generator.generate_question(
                    session_id=session_id,
                    resume_data=resume_data,
                    question_number=next_q_num,
                    previous_context=previous_context
                )
                db.store_question(session_id, active_question)
            else:
                db.complete_session(session_id)
                session_manager.complete_session(session_id)
                return {
                    "success": True,
                    "interview_complete": True,
                    "message": "Interview already completed!"
                }

        logger.info(f"Interview resumed: {session_id} at question {active_question['question_number']}")
        return {
            "success": True,
            "session_id": session_id,
            "question": active_question,
            "question_number": active_question["question_number"],
            "total_questions": total_questions,
            "resume_data": resume_data,
            "role": role
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview resume error: {e}")
        raise HTTPException(500, str(e))


# ─── Submit Answer ─────────────────────────────────────────────────────────────

@app.post("/api/submit-answer")
async def submit_answer(
    session_id:       str  = Form(...),
    question_id:      str  = Form(...),
    answer:           str  = Form(...),
    duration_seconds: Optional[int]       = Form(0),
    video:            Optional[UploadFile] = File(None),
    current_user:     dict                = Depends(get_current_user),
):
    """Submit a candidate answer and receive the next question.

    Transcript priority:
      1. Gemini multimodal (server-side) — most accurate
      2. OpenAI Whisper API (server-side) — robust fallback
      3. Browser Web Speech API draft (client-side) — last resort
    """
    try:
        if not answer.strip() and not video:
            raise HTTPException(400, "Answer cannot be empty")

        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(403, "Unauthorized")

        # ── Save video file ─────────────────────────────────────────────────
        video_path  = None
        video_bytes = b""

        if video:
            try:
                os.makedirs("recordings", exist_ok=True)
                video_bytes = await video.read()
                video_path  = f"recordings/{session_id}_{question_id}.webm"
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
                logger.info(
                    f"Video saved: {video_path} "
                    f"({len(video_bytes) // 1024} KB)"
                )
            except Exception as ve:
                logger.error(f"Video save failed: {ve}")
                video_bytes = b""

        # ── Server-side transcription ───────────────────────────────────────
        # transcriber.transcribe() returns (text, source_label)
        # source_label: 'gemini_multimodal' | 'openai_whisper' | 'browser_stt' | 'empty'
        final_answer, transcript_source = transcriber.transcribe(
            video_bytes=video_bytes,
            fallback_text=answer.strip(),
        )

        # Guard: ensure we always have something stored
        if not final_answer:
            final_answer = answer.strip() or "[No response]"

        logger.info(
            f"Transcript for {question_id}: source={transcript_source}, "
            f"length={len(final_answer)} chars"
        )

        # ── Persist answer ─────────────────────────────────────────────────
        db.store_answer(
            session_id=session_id,
            question_id=question_id,
            answer=final_answer,
            duration_seconds=duration_seconds,
            video_path=video_path,
            transcript_source=transcript_source,
        )

        answer_count    = db.get_answer_count(session_id)
        total_questions = _safe_total_questions(session)

        if answer_count >= total_questions:
            db.complete_session(session_id)
            if session_id in session_manager.active_sessions:
                session_manager.active_sessions[session_id]["status"] = "completed"
            return {
                "success": True,
                "interview_complete": True,
                "message": "Interview completed!",
                "transcript_source": transcript_source,
            }

        # ── Generate next question ─────────────────────────────────────────
        resume_data   = session["resume_data"]
        next_question = question_generator.generate_question(
            session_id=session_id,
            resume_data=resume_data,
            question_number=answer_count + 1,
            previous_context={
                "previous_question": db.get_last_question(session_id),
                "previous_answer":   final_answer,
            },
        )
        db.store_question(session_id, next_question)

        return {
            "success":            True,
            "interview_complete": False,
            "question":           next_question,
            "question_number":    answer_count + 1,
            "total_questions":    total_questions,
            "transcript_source":  transcript_source,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit answer error: {e}")
        raise HTTPException(500, str(e))



# ─── Skip Question ─────────────────────────────────────────────────────────────

@app.post("/api/skip-question")
async def skip_question(
    skip_data:    SkipQuestion,
    current_user: dict = Depends(get_current_user),
):
    """Skip the current question and receive the next one."""
    try:
        session = session_manager.get_session(skip_data.session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(403, "Unauthorized")

        db.store_answer(
            session_id=skip_data.session_id,
            question_id=skip_data.question_id,
            answer="[SKIPPED]",
        )

        answer_count    = db.get_answer_count(skip_data.session_id)
        total_questions = _safe_total_questions(session)

        if answer_count >= total_questions:
            db.complete_session(skip_data.session_id)
            if skip_data.session_id in session_manager.active_sessions:
                session_manager.active_sessions[skip_data.session_id]["status"] = "completed"
            return {"success": True, "interview_complete": True, "message": "Interview completed!"}

        resume_data = session["resume_data"]
        next_question = question_generator.generate_question(
            session_id=skip_data.session_id,
            resume_data=resume_data,
            question_number=answer_count + 1,
            previous_context={
                "previous_question": db.get_last_question(skip_data.session_id),
                "previous_answer":   None,
            },
        )
        db.store_question(skip_data.session_id, next_question)

        return {
            "success":           True,
            "interview_complete": False,
            "question":          next_question,
            "question_number":   answer_count + 1,
            "total_questions":   total_questions,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skip question error: {e}")
        raise HTTPException(500, str(e))


# ─── Interview Summary ─────────────────────────────────────────────────────────

@app.get("/api/interview-summary/{session_id}")
async def get_interview_summary(
    session_id:   str,
    current_user: dict = Depends(get_current_user),
):
    """
    Return complete interview summary with Q&A pairs and
    a Gemini-generated candidate evaluation report.
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        session_user_id = session.get("user_id")
        if session_user_id and session_user_id != current_user["id"]:
            raise HTTPException(403, "Unauthorized")

        qa_pairs = db.get_qa_pairs(session_id)
        resume_data = session.get("resume_data") or {}
        role        = session.get("role", "")

        # Gemini-powered evaluation report
        try:
            eval_report = evaluator.evaluate(
                session_id=session_id,
                qa_pairs=qa_pairs,
                resume_data=resume_data,
                role=role,
            )
            evaluation_dict = eval_report.to_dict()
        except Exception as eval_err:
            logger.error(f"Evaluation error: {eval_err}")
            evaluation_dict = None

        # Legacy analysis (kept for backward compatibility)
        legacy_analysis = _legacy_analyze(qa_pairs, session)

        return {
            "success": True,
            "summary": {
                "session_id":      session_id,
                "candidate_name":  session["candidate_name"],
                "role":            role,
                "timestamp":       session.get("created_at", datetime.now().isoformat()),
                "total_questions": session.get("total_questions", len(qa_pairs)),
                "qa_pairs":        qa_pairs,
                "analysis":        legacy_analysis,
                "evaluation_report": evaluation_dict,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary retrieval error: {e}")
        raise HTTPException(500, str(e))


# ─── Dedicated Evaluation Endpoint ────────────────────────────────────────────

@app.get("/api/evaluation/{session_id}")
async def get_evaluation(
    session_id:   str,
    current_user: dict = Depends(get_current_user),
):
    """
    Fetch or regenerate the candidate evaluation report for a session.
    Can be called after interview completion.
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(403, "Unauthorized")

        qa_pairs    = db.get_qa_pairs(session_id)
        resume_data = session.get("resume_data") or {}
        role        = session.get("role", "")

        if not qa_pairs:
            raise HTTPException(400, "No answers found. Complete the interview first.")

        eval_report = evaluator.evaluate(
            session_id=session_id,
            qa_pairs=qa_pairs,
            resume_data=resume_data,
            role=role,
        )

        return {
            "success":           True,
            "session_id":        session_id,
            "candidate_name":    session["candidate_name"],
            "role":              role,
            "evaluation_report": eval_report.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(500, str(e))


# ─── Sessions List ─────────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    try:
        sessions = db.list_sessions_for_user(current_user["id"])
        return {"success": True, "sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        raise HTTPException(500, str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id:   str,
    current_user: dict = Depends(get_current_user),
):
    try:
        success = db.delete_session(session_id, current_user["id"])
        if not success:
            raise HTTPException(404, "Session not found or unauthorized")
        if session_id in session_manager.active_sessions:
            del session_manager.active_sessions[session_id]
        return {"success": True, "message": "Session deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(500, str(e))


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _safe_total_questions(session: dict) -> int:
    total = session.get("total_questions")
    try:
        return int(total) if total is not None else 5
    except (ValueError, TypeError):
        return 5


def _legacy_analyze(qa_pairs: List[dict], session: dict) -> dict:
    """Simple length-based analysis kept for backward compatibility."""
    if not qa_pairs:
        return {
            "depth_of_knowledge": "Insufficient data",
            "technical_accuracy": 0.0,
            "communication_clarity": "N/A",
            "domain_relevance": "N/A",
            "recommendations": ["Complete the interview to get analysis"],
        }
    avg_len = sum(len(qa.get("answer", "")) for qa in qa_pairs) / len(qa_pairs)
    if avg_len > 500:
        depth, acc = "Excellent", 0.9
    elif avg_len > 300:
        depth, acc = "Good", 0.75
    elif avg_len > 100:
        depth, acc = "Fair", 0.6
    else:
        depth, acc = "Needs Improvement", 0.4

    return {
        "depth_of_knowledge":   depth,
        "technical_accuracy":   acc,
        "communication_clarity": "Clear" if avg_len > 200 else "Could be clearer",
        "domain_relevance":     "Strong" if session.get("role") else "N/A",
        "recommendations": [
            "Strong fundamentals demonstrated" if acc > 0.7 else "Consider more practice",
            "Good communication skills" if avg_len > 300 else "Be more detailed in answers",
            "Ready for next round" if acc > 0.75 else "Review key concepts",
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Startup / Shutdown
# ══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Candidate Screening System v2.0")
    try:
        db.initialize()
        rag_pipeline.initialize()
        logger.info("✅ System initialised successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    try:
        db.close()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)