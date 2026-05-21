"""
FastAPI Backend for AI-Powered Candidate Screening System
Core orchestration and API endpoints - PRODUCTION READY
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
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
from datetime import datetime
from io import BytesIO

from modules.resume_parser import ResumeParser
from modules.rag_pipeline import RAGPipeline
from modules.question_generator import QuestionGenerator
from modules.database import Database
from modules.session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Candidate Screening System",
    description="RAG-powered interview system",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database()
session_manager = SessionManager(db)
resume_parser = ResumeParser()
rag_pipeline = RAGPipeline()
question_generator = QuestionGenerator(rag_pipeline)

# Active user tokens store (in-memory)
ACTIVE_TOKENS = {}

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    if token not in ACTIVE_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return ACTIVE_TOKENS[token]

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt_hex, key_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return secrets.compare_digest(expected_key, actual_key)
    except Exception:
        return False

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

# ============ Data Models ============

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RoleSelection(BaseModel):
    role: str

class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    answer: str
    duration_seconds: Optional[int] = 0

class SkipQuestion(BaseModel):
    session_id: str
    question_id: str

class InterviewSummaryResponse(BaseModel):
    session_id: str
    candidate_name: str
    role: str
    total_questions: int
    answers: List[dict]
    analysis: Optional[dict] = None

# ============ API Endpoints ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Candidate Screening System"}

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    username = req.username.strip()
    email = req.email.strip()
    password = req.password
    
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
        
    # Check if username or email already exists
    if db.get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username is already taken")
    if db.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email is already registered")
        
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)
    
    success = db.create_user(user_id, username, email, pw_hash)
    if not success:
        raise HTTPException(status_code=500, detail="Could not create user")
        
    return {"success": True, "message": "User registered successfully"}

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    username = req.username.strip()
    password = req.password
    
    user = db.get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    token = str(uuid.uuid4())
    ACTIVE_TOKENS[token] = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"]
    }
    
    return {
        "success": True,
        "token": token,
        "user": {
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an interview session and its related data"""
    try:
        # Check ownership and delete
        success = db.delete_session(session_id, current_user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")
        
        # Remove from session manager cache
        if session_id in session_manager.active_sessions:
            del session_manager.active_sessions[session_id]
            
        return {"success": True, "message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Upload and process candidate resume
    
    Returns: Extracted resume data and metadata
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.txt', '.docx')):
            raise HTTPException(status_code=400, detail="Invalid file type. Use PDF, TXT, or DOCX")
        
        # Read file content
        content = await file.read()
        
        # Parse resume
        try:
            resume_data = resume_parser.parse(content, file.filename)
        except Exception as e:
            logger.error(f"Resume parsing error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Could not parse resume: {str(e)}")
        
        logger.info(f"Resume processed: {resume_data.get('candidate_name')}")
        
        return {
            "success": True,
            "data": resume_data,
            "extracted_fields": {
                "name": resume_data.get("candidate_name", "Unknown"),
                "skills": resume_data.get("skills", []),
                "experience": resume_data.get("experience_years", 0),
                "domain": resume_data.get("domain", "General"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/select-role")
async def select_role(role_data: RoleSelection, current_user: dict = Depends(get_current_user)):
    """
    User selects target role
    
    Returns: Role information and knowledge base status
    """
    try:
        supported_roles = [
            "Backend Engineer",
            "AI/ML Engineer",
            "Full Stack Engineer",
            "Data Scientist",
            "DevOps Engineer",
            "Frontend Developer",
            "Data Analyst"
        ]
        
        if role_data.role not in supported_roles:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported role. Choose from: {', '.join(supported_roles)}"
            )
        
        # Load role-specific knowledge base
        kb_status = rag_pipeline.load_knowledge_base(role_data.role)
        
        return {
            "success": True,
            "role": role_data.role,
            "knowledge_base_loaded": kb_status,
            "message": f"Knowledge base for {role_data.role} loaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Role selection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start-interview")
async def start_interview(resume_data: dict, current_user: dict = Depends(get_current_user)):
    """
    Initialize interview session
    
    Returns: Session ID and first question
    """
    try:
        # Validate input
        if not resume_data.get("candidate_name"):
            raise HTTPException(status_code=400, detail="Candidate name required")
        if not resume_data.get("role"):
            raise HTTPException(status_code=400, detail="Role required")
        
        total_questions = resume_data.get("total_questions", 5)
        
        # Create session
        session = session_manager.create_session(
            candidate_name=resume_data.get("candidate_name"),
            role=resume_data.get("role"),
            resume_data=resume_data,
            user_id=current_user["id"],
            total_questions=total_questions
        )
        
        # Generate first question
        question = question_generator.generate_question(
            session_id=session["session_id"],
            resume_data=resume_data,
            question_number=1,
            previous_context=None
        )
        
        # Store question in database
        db.store_question(session["session_id"], question)
        
        logger.info(f"Interview started: {session['session_id']}")
        
        return {
            "success": True,
            "session_id": session["session_id"],
            "question": question,
            "question_number": 1,
            "total_questions": total_questions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview initialization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/submit-answer")
async def submit_answer(answer_data: AnswerSubmission, current_user: dict = Depends(get_current_user)):
    """
    Submit candidate answer and get next question
    
    Returns: Next question or completion status
    """
    try:
        # Validate input
        if not answer_data.answer.strip():
            raise HTTPException(status_code=400, detail="Answer cannot be empty")
        
        # Get session data
        session = session_manager.get_session(answer_data.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unauthorized access to this session")
            
        # Store answer
        db.store_answer(
            session_id=answer_data.session_id,
            question_id=answer_data.question_id,
            answer=answer_data.answer
        )
        
        question_count = db.get_question_count(answer_data.session_id)
        total_questions = session.get("total_questions", 5)
        
        # Check if interview is complete
        if question_count >= total_questions:  # Total questions
            db.complete_session(answer_data.session_id)
            if answer_data.session_id in session_manager.active_sessions:
                session_manager.active_sessions[answer_data.session_id]["status"] = "completed"
            return {
                "success": True,
                "interview_complete": True,
                "message": "Interview completed!"
            }
        
        # Generate next question with context
        next_question = question_generator.generate_question(
            session_id=answer_data.session_id,
            resume_data=session["resume_data"],
            question_number=question_count + 1,
            previous_context={
                "previous_question": db.get_last_question(answer_data.session_id),
                "previous_answer": answer_data.answer
            }
        )
        
        # Store next question
        db.store_question(answer_data.session_id, next_question)
        
        return {
            "success": True,
            "interview_complete": False,
            "question": next_question,
            "question_number": question_count + 1,
            "total_questions": total_questions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer submission error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/skip-question")
async def skip_question(skip_data: SkipQuestion, current_user: dict = Depends(get_current_user)):
    """
    Skip the current question and receive the next one.

    Returns: Next question or completion status
    """
    try:
        # Get session data
        session = session_manager.get_session(skip_data.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unauthorized access to this session")

        # Store a skipped placeholder answer so question_count advances
        db.store_answer(
            session_id=skip_data.session_id,
            question_id=skip_data.question_id,
            answer="[SKIPPED]"
        )

        question_count = db.get_question_count(skip_data.session_id)
        total_questions = session.get("total_questions", 5)

        # Check if interview is complete
        if question_count >= total_questions:
            db.complete_session(skip_data.session_id)
            if skip_data.session_id in session_manager.active_sessions:
                session_manager.active_sessions[skip_data.session_id]["status"] = "completed"
            return {
                "success": True,
                "interview_complete": True,
                "message": "Interview completed!"
            }

        # Generate next question
        next_question = question_generator.generate_question(
            session_id=skip_data.session_id,
            resume_data=session["resume_data"],
            question_number=question_count + 1,
            previous_context={
                "previous_question": db.get_last_question(skip_data.session_id),
                "previous_answer": None
            }
        )

        db.store_question(skip_data.session_id, next_question)
        logger.info(f"Question skipped in session {skip_data.session_id}")

        return {
            "success": True,
            "interview_complete": False,
            "question": next_question,
            "question_number": question_count + 1,
            "total_questions": total_questions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skip question error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interview-summary/{session_id}")
async def get_interview_summary(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get complete interview summary and analysis
    
    Returns: Structured summary with Q&A and insights
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unauthorized access to this session")
        
        qa_pairs = db.get_qa_pairs(session_id)
        
        # Analyze performance
        analysis = analyze_performance(qa_pairs, session)
        
        return {
            "success": True,
            "summary": {
                "session_id": session_id,
                "candidate_name": session["candidate_name"],
                "role": session["role"],
                "timestamp": session.get("created_at", datetime.now().isoformat()),
                "total_questions": session.get("total_questions", len(qa_pairs)),
                "qa_pairs": qa_pairs,
                "analysis": analysis
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """Get all interview sessions"""
    try:
        sessions = db.list_sessions_for_user(current_user["id"])
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ Helper Functions ============

def analyze_performance(qa_pairs: List[dict], session: dict) -> dict:
    """
    Analyze candidate performance based on answers
    
    Returns: Performance metrics and insights
    """
    if not qa_pairs:
        return {
            "depth_of_knowledge": "Insufficient data",
            "technical_accuracy": 0.0,
            "communication_clarity": "N/A",
            "domain_relevance": "N/A",
            "recommendations": ["Complete the interview to get analysis"]
        }
    
    # Calculate metrics
    avg_answer_length = sum(len(qa.get("answer", "")) for qa in qa_pairs) / len(qa_pairs) if qa_pairs else 0
    
    # Determine depth based on answer length and content
    if avg_answer_length > 500:
        depth = "Excellent"
        accuracy = 0.9
    elif avg_answer_length > 300:
        depth = "Good"
        accuracy = 0.75
    elif avg_answer_length > 100:
        depth = "Fair"
        accuracy = 0.6
    else:
        depth = "Needs Improvement"
        accuracy = 0.4
    
    analysis = {
        "depth_of_knowledge": depth,
        "technical_accuracy": accuracy,
        "communication_clarity": "Clear" if avg_answer_length > 200 else "Could be clearer",
        "domain_relevance": "Strong" if session.get("role") else "N/A",
        "recommendations": [
            "Strong fundamentals demonstrated" if accuracy > 0.7 else "Consider more practice",
            "Good communication skills" if avg_answer_length > 300 else "Be more detailed in answers",
            "Ready for next interview round" if accuracy > 0.75 else "Review key concepts"
        ]
    }
    return analysis

# ============ Startup & Shutdown ============

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting up AI Candidate Screening System")
    try:
        db.initialize()
        rag_pipeline.initialize()
        logger.info("✅ System initialized successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down system")
    try:
        db.close()
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)