"""
Database Module
Handles all data persistence and retrieval
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Database:
    """SQLite database handler for interview system"""
    
    def __init__(self, db_path: str = "interview_system.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
    
    def initialize(self):
        """Create database tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migration: Check if username column exists, if not add it
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if "username" not in columns:
                logger.info("Migrating users table: adding username column...")
                # Add username column
                cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
                # Migrate email to username for existing users
                cursor.execute("UPDATE users SET username = email WHERE username IS NULL")
                # Add unique constraint on username
                try:
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON users(username)")
                except:
                    pass
                self.conn.commit()
                logger.info("Migration completed")
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    candidate_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    resume_data TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    status TEXT DEFAULT 'in_progress',
                    user_id TEXT,
                    total_questions INTEGER DEFAULT 5
                )
            ''')
            
            # Check if user_id and total_questions columns exist in sessions table (migrations)
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [col[1] for col in cursor.fetchall()]
            if "user_id" not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")
                self.conn.commit()
            if "total_questions" not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN total_questions INTEGER DEFAULT 5")
                self.conn.commit()
            
            # Questions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    question_number INTEGER,
                    question_text TEXT NOT NULL,
                    question_type TEXT,
                    difficulty TEXT,
                    category TEXT,
                    context_used TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            ''')
            
            # Answers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS answers (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    answer_text TEXT,
                    duration_seconds INTEGER,
                    quality_score FLOAT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            ''')
            
            # Interview metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interview_metadata (
                    session_id TEXT PRIMARY KEY,
                    total_duration INTEGER,
                    average_answer_length FLOAT,
                    overall_performance FLOAT,
                    notes TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            ''')
            # Migration for answers table (add video_path if not exists)
            cursor.execute("PRAGMA table_info(answers)")
            columns = [col[1] for col in cursor.fetchall()]
            if "video_path" not in columns:
                logger.info("Migrating answers table: adding video_path column...")
                cursor.execute("ALTER TABLE answers ADD COLUMN video_path TEXT")
                self.conn.commit()
            if "duration_seconds" not in columns:
                logger.info("Migrating answers table: adding duration_seconds column...")
                cursor.execute("ALTER TABLE answers ADD COLUMN duration_seconds INTEGER")
                self.conn.commit()
            
            self.conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def create_session(self, session_data: Dict) -> str:
        """Create new interview session"""
        try:
            cursor = self.conn.cursor()
            session_id = session_data["session_id"]
            
            cursor.execute('''
                INSERT INTO sessions 
                (id, candidate_name, role, email, phone, resume_data, created_at, updated_at, status, user_id, total_questions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                session_data.get("candidate_name"),
                session_data.get("role"),
                session_data.get("email"),
                session_data.get("phone"),
                json.dumps(session_data.get("resume_data", {})),
                datetime.now(),
                datetime.now(),
                "in_progress",
                session_data.get("user_id"),
                session_data.get("total_questions", 5)
            ))
            
            self.conn.commit()
            logger.info(f"Session created: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise

    def create_user(self, user_id: str, username: str, email: str, password_hash: str) -> bool:
        """Create a new user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (id, username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, datetime.now()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "email": row[2], "password_hash": row[3]}
            return None
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username, email, password_hash FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "email": row[2], "password_hash": row[3]}
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete an interview session and its dependent questions, answers, and metadata"""
        try:
            cursor = self.conn.cursor()
            # Verify ownership
            cursor.execute('SELECT id FROM sessions WHERE id = ? AND user_id = ?', (session_id, user_id))
            if not cursor.fetchone():
                logger.warning(f"Unauthorized or non-existent delete attempt of session {session_id} by user {user_id}")
                return False
                
            cursor.execute('DELETE FROM answers WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM questions WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM interview_metadata WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            self.conn.commit()
            logger.info(f"Session {session_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False

    def list_sessions_for_user(self, user_id: str) -> List[Dict]:
        """List all sessions belonging to a specific user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, candidate_name, role, created_at, status 
                FROM sessions 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "candidate_name": row[1],
                    "role": row[2],
                    "created_at": row[3],
                    "status": row[4]
                })
            
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions for user {user_id}: {str(e)}")
            return []
    
    def store_question(self, session_id: str, question: Dict) -> str:
        """Store interview question (UPSERT style to handle retries/race conditions)"""
        try:
            cursor = self.conn.cursor()
            question_id = question.get("question_id", "")
            
            # Use UPSERT style checking to handle potential duplicate inserts from concurrent requests
            cursor.execute('SELECT id FROM questions WHERE id = ?', (question_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE questions 
                    SET question_text = ?, question_type = ?, difficulty = ?, 
                        category = ?, context_used = ?, created_at = ?
                    WHERE id = ?
                ''', (
                    question.get("question_text"),
                    question.get("question_type"),
                    question.get("difficulty"),
                    question.get("category"),
                    json.dumps(question.get("context_used", [])),
                    datetime.now(),
                    question_id
                ))
                logger.info(f"Question updated in database: {question_id}")
            else:
                cursor.execute('''
                    INSERT INTO questions 
                    (id, session_id, question_number, question_text, question_type, 
                     difficulty, category, context_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question_id,
                    session_id,
                    question.get("question_number"),
                    question.get("question_text"),
                    question.get("question_type"),
                    question.get("difficulty"),
                    question.get("category"),
                    json.dumps(question.get("context_used", [])),
                    datetime.now()
                ))
                logger.info(f"Question stored in database: {question_id}")
            
            self.conn.commit()
            return question_id
            
        except Exception as e:
            logger.error(f"Error storing question: {str(e)}")
            raise
    
    def store_answer(self, session_id: str, question_id: str, answer: str, duration_seconds: int = 0, video_path: Optional[str] = None) -> str:
        """Store candidate answer"""
        try:
            cursor = self.conn.cursor()
            answer_id = f"{question_id}_ans"
            
            # Use UPSERT style checking to handle potential client retries
            cursor.execute('SELECT id FROM answers WHERE id = ?', (answer_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE answers 
                    SET answer_text = ?, duration_seconds = ?, video_path = ?, created_at = ?
                    WHERE id = ?
                ''', (answer, duration_seconds, video_path, datetime.now(), answer_id))
            else:
                cursor.execute('''
                    INSERT INTO answers 
                    (id, session_id, question_id, answer_text, duration_seconds, video_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    answer_id,
                    session_id,
                    question_id,
                    answer,
                    duration_seconds,
                    video_path,
                    datetime.now()
                ))
            
            # Update session updated_at
            cursor.execute(
                'UPDATE sessions SET updated_at = ? WHERE id = ?',
                (datetime.now(), session_id)
            )
            
            self.conn.commit()
            logger.info(f"Answer stored/updated for question: {question_id}")
            return answer_id
            
        except Exception as e:
            logger.error(f"Error storing answer: {str(e)}")
            raise
    
    def get_qa_pairs(self, session_id: str) -> List[Dict]:
        """Get all Q&A pairs for a session"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT 
                    q.question_number,
                    q.question_text,
                    q.question_type,
                    q.difficulty,
                    q.category,
                    a.answer_text,
                    a.created_at
                FROM questions q
                LEFT JOIN answers a ON q.id = a.question_id
                WHERE q.session_id = ?
                ORDER BY q.question_number
            ''', (session_id,))
            
            pairs = []
            for row in cursor.fetchall():
                pairs.append({
                    "question_number": row[0],
                    "question": row[1],
                    "question_type": row[2],
                    "difficulty": row[3],
                    "category": row[4],
                    "answer": row[5],
                    "answered_at": row[6]
                })
            
            return pairs
            
        except Exception as e:
            logger.error(f"Error retrieving Q&A pairs: {str(e)}")
            return []
    
    def get_question_count(self, session_id: str) -> int:
        """Get number of questions asked in session"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM questions WHERE session_id = ?',
                (session_id,)
            )
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Error getting question count: {str(e)}")
            return 0
    
    def get_answer_count(self, session_id: str) -> int:
        """Get number of answers submitted in session"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM answers WHERE session_id = ?',
                (session_id,)
            )
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Error getting answer count: {str(e)}")
            return 0
    
    def get_last_question(self, session_id: str) -> Optional[str]:
        """Get the last question asked in a session"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT question_text FROM questions 
                WHERE session_id = ?
                ORDER BY question_number DESC
                LIMIT 1
            ''', (session_id,))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting last question: {str(e)}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''SELECT id, candidate_name, role, email, phone, resume_data, 
                   created_at, status, user_id, total_questions FROM sessions WHERE id = ?''',
                (session_id,)
            )
            
            result = cursor.fetchone()
            if not result:
                return None
            
            return {
                "session_id": result[0],
                "candidate_name": result[1],
                "role": result[2],
                "email": result[3],
                "phone": result[4],
                "resume_data": json.loads(result[5]) if result[5] else {},
                "created_at": result[6],
                "status": result[7],
                "user_id": result[8],
                "total_questions": result[9]
            }
            
        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
            return None
    
    def list_sessions(self) -> List[Dict]:
        """List all interview sessions"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, candidate_name, role, created_at, status 
                FROM sessions 
                ORDER BY created_at DESC
            ''')
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "candidate_name": row[1],
                    "role": row[2],
                    "created_at": row[3],
                    "status": row[4]
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
    
    def complete_session(self, session_id: str) -> bool:
        """Mark session as completed"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?',
                ("completed", datetime.now(), session_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error completing session: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")