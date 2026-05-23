"""
Session Manager Module
Manages interview session lifecycle with full interview state tracking:
  - Asked question embeddings (for deduplication)
  - Covered skills tracking
  - Category rotation history
  - Question difficulty history
"""

import logging
import uuid
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# 6-category rotation sequence
CATEGORY_ROTATION = [
    "conceptual",
    "project-based",
    "debugging",
    "deployment",
    "scenario-based",
    "real-world",
]


class SessionManager:
    """Manages interview session lifecycle with full state tracking."""

    def __init__(self, db):
        self.db = db
        self.active_sessions: Dict[str, Dict] = {}

    # ──────────────────────────────────────────────────────────────────────────
    # Session CRUD
    # ──────────────────────────────────────────────────────────────────────────

    def create_session(
        self,
        candidate_name: str,
        role: str,
        resume_data: Dict,
        user_id: Optional[str] = None,
        total_questions: int = 5,
    ) -> Dict:
        """
        Create a new interview session with full state initialisation.

        Returns:
            Session data dictionary (also persisted to DB)
        """
        try:
            session_id = str(uuid.uuid4())

            session_data = {
                # Identity
                "session_id":     session_id,
                "candidate_name": candidate_name,
                "role":           role,
                "email":          resume_data.get("email"),
                "phone":          resume_data.get("phone"),
                "resume_data":    resume_data,
                "user_id":        user_id,

                # Lifecycle
                "created_at":     datetime.now().isoformat(),
                "status":         "in_progress",
                "total_questions": total_questions,
                "question_count": 0,
                "answer_count":   0,

                # ── Interview state tracking ──────────────────────────────────
                # Previously asked question texts (for LLM prompt context)
                "asked_question_texts":      [],
                # Numpy embeddings stored separately in QuestionGenerator
                # (too large to serialize to SQLite — managed in-memory only)

                # Skills explicitly covered in questions
                "covered_skills":            [],

                # Category rotation history
                "covered_categories":        [],

                # Rotating category queue (deque serialised as list)
                "category_queue":            list(CATEGORY_ROTATION) * 3,

                # Difficulty progression
                "question_difficulty_history": [],
            }

            # Persist to database
            self.db.create_session(session_data)

            # Keep in memory
            self.active_sessions[session_id] = session_data

            logger.info(f"Session created: {session_id} for {candidate_name} ({role})")
            return session_data

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session — memory first, then DB."""
        try:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]

            session = self.db.get_session(session_id)
            if session:
                self.active_sessions[session_id] = session
            return session

        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Merge updates into session data."""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            session.update(updates)
            self.active_sessions[session_id] = session
            return True
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False

    def complete_session(self, session_id: str) -> bool:
        """Mark session as completed."""
        try:
            success = self.db.complete_session(session_id)
            if success:
                session = self.active_sessions.get(session_id)
                if session:
                    session["status"] = "completed"
            return success
        except Exception as e:
            logger.error(f"Error completing session {session_id}: {e}")
            return False

    def list_sessions(self) -> List[Dict]:
        try:
            return self.db.list_sessions()
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────────
    # Interview State Management
    # ──────────────────────────────────────────────────────────────────────────

    def get_state(self, session_id: str) -> Dict:
        """Return the interview state sub-dictionary for a session."""
        session = self.get_session(session_id)
        if not session:
            return {}
        return {
            "asked_question_texts":       session.get("asked_question_texts", []),
            "covered_skills":             session.get("covered_skills", []),
            "covered_categories":         session.get("covered_categories", []),
            "category_queue":             deque(session.get("category_queue", list(CATEGORY_ROTATION) * 3)),
            "question_difficulty_history": session.get("question_difficulty_history", []),
        }

    def update_state(self, session_id: str, question_text: str,
                     category: str, difficulty: str,
                     new_skills_covered: List[str] = None) -> bool:
        """
        Update interview state after a question is accepted.

        Args:
            session_id: Session ID
            question_text: The accepted question text
            category: The question category
            difficulty: The difficulty level used
            new_skills_covered: Skills identified in the question
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            # Append question text
            texts = session.get("asked_question_texts", [])
            texts.append(question_text)
            session["asked_question_texts"] = texts

            # Update covered categories
            cats = session.get("covered_categories", [])
            cats.append(category)
            session["covered_categories"] = cats

            # Update category queue
            q = deque(session.get("category_queue", list(CATEGORY_ROTATION) * 3))
            if q:
                q.popleft()
            session["category_queue"] = list(q)

            # Update covered skills
            covered = list(session.get("covered_skills", []))
            for skill in (new_skills_covered or []):
                if skill not in covered:
                    covered.append(skill)
            session["covered_skills"] = covered

            # Update difficulty history
            diffs = session.get("question_difficulty_history", [])
            diffs.append(difficulty)
            session["question_difficulty_history"] = diffs

            self.active_sessions[session_id] = session
            return True

        except Exception as e:
            logger.error(f"Error updating state for {session_id}: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Counter Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def increment_question_count(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if session:
                session["question_count"] = session.get("question_count", 0) + 1
                self.active_sessions[session_id] = session
                return True
            return False
        except Exception as e:
            logger.error(f"Error incrementing question count: {e}")
            return False

    def increment_answer_count(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if session:
                session["answer_count"] = session.get("answer_count", 0) + 1
                self.active_sessions[session_id] = session
                return True
            return False
        except Exception as e:
            logger.error(f"Error incrementing answer count: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Progress
    # ──────────────────────────────────────────────────────────────────────────

    def get_session_progress(self, session_id: str) -> Dict:
        try:
            session = self.get_session(session_id)
            if not session:
                return {}

            total = session.get("total_questions")
            try:
                total = int(total) if total is not None else 5
            except (ValueError, TypeError):
                total = 5

            answer_count = self.db.get_answer_count(session_id)

            return {
                "session_id":         session_id,
                "candidate_name":     session.get("candidate_name"),
                "role":               session.get("role"),
                "questions_asked":    answer_count,
                "questions_answered": answer_count,
                "covered_categories": session.get("covered_categories", []),
                "covered_skills":     session.get("covered_skills", []),
                "status":             session.get("status"),
                "progress_percentage": (answer_count / max(total, 1)) * 100,
            }

        except Exception as e:
            logger.error(f"Error getting session progress: {e}")
            return {}