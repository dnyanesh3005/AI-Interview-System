"""
Session Manager Module
Manages interview session lifecycle
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages interview session lifecycle"""
    
    def __init__(self, db):
        """
        Initialize session manager
        
        Args:
            db: Database instance
        """
        self.db = db
        self.active_sessions = {}
    
    def create_session(
        self,
        candidate_name: str,
        role: str,
        resume_data: Dict
    ) -> Dict:
        """
        Create new interview session
        
        Args:
            candidate_name: Candidate's name
            role: Target job role
            resume_data: Extracted resume data
            
        Returns:
            Dictionary with session information
        """
        try:
            session_id = str(uuid.uuid4())
            
            session_data = {
                "session_id": session_id,
                "candidate_name": candidate_name,
                "role": role,
                "email": resume_data.get("email"),
                "phone": resume_data.get("phone"),
                "resume_data": resume_data,
                "created_at": datetime.now().isoformat(),
                "status": "in_progress",
                "question_count": 0,
                "answer_count": 0
            }
            
            # Persist to database
            self.db.create_session(session_data)
            
            # Keep in memory for quick access
            self.active_sessions[session_id] = session_data
            
            logger.info(f"Session created: {session_id} for {candidate_name}")
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session details
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None
        """
        try:
            # Check memory first
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            # Fetch from database
            session = self.db.get_session(session_id)
            if session:
                self.active_sessions[session_id] = session
            
            return session
            
        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
            return None
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID
            updates: Dictionary with updates
            
        Returns:
            Success status
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            session.update(updates)
            self.active_sessions[session_id] = session
            
            logger.info(f"Session updated: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            return False
    
    def increment_question_count(self, session_id: str) -> bool:
        """Increment question count"""
        try:
            session = self.get_session(session_id)
            if session:
                session["question_count"] = session.get("question_count", 0) + 1
                self.active_sessions[session_id] = session
                return True
            return False
        except Exception as e:
            logger.error(f"Error incrementing question count: {str(e)}")
            return False
    
    def increment_answer_count(self, session_id: str) -> bool:
        """Increment answer count"""
        try:
            session = self.get_session(session_id)
            if session:
                session["answer_count"] = session.get("answer_count", 0) + 1
                self.active_sessions[session_id] = session
                return True
            return False
        except Exception as e:
            logger.error(f"Error incrementing answer count: {str(e)}")
            return False
    
    def complete_session(self, session_id: str) -> bool:
        """Mark session as completed"""
        try:
            success = self.db.complete_session(session_id)
            if success:
                session = self.active_sessions.get(session_id)
                if session:
                    session["status"] = "completed"
            return success
        except Exception as e:
            logger.error(f"Error completing session: {str(e)}")
            return False
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
        try:
            return self.db.list_sessions()
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
    
    def get_session_progress(self, session_id: str) -> Dict:
        """Get session progress"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {}
            
            question_count = self.db.get_question_count(session_id)
            
            return {
                "session_id": session_id,
                "candidate_name": session.get("candidate_name"),
                "role": session.get("role"),
                "questions_asked": question_count,
                "questions_answered": session.get("answer_count", 0),
                "status": session.get("status"),
                "progress_percentage": (session.get("answer_count", 0) / max(question_count, 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting session progress: {str(e)}")
            return {}