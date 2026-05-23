"""
Question Generator Module
Generates resume-grounded interview questions with:
  - Hybrid RAG context (FAISS + BM25)
  - 6-category rotation (conceptual, project-based, debugging,
    deployment, scenario-based, real-world)
  - Cosine-similarity deduplication (threshold = 0.75)
  - Resume grounding validation (hallucination rejection + content check)
  - Difficulty capped at beginner → intermediate
"""

import logging
import re
from collections import deque
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ─── Category rotation ─────────────────────────────────────────────────────────
CATEGORY_ROTATION = [
    "conceptual",
    "project-based",
    "debugging",
    "deployment",
    "scenario-based",
    "real-world",
]

# Deduplication threshold
SIM_THRESHOLD = 0.75  # More aggressive deduplication

# Max regeneration attempts before giving up
MAX_RETRIES = 3


class QuestionGenerator:
    """
    Generates personalized, resume-grounded interview questions.
    Integrates LLMService (Gemini) + Hybrid RAG pipeline.
    """

    def __init__(self, rag_pipeline, llm_service=None):
        """
        Args:
            rag_pipeline: RAGPipeline instance (hybrid FAISS + BM25)
            llm_service: LLMService instance (Gemini). If None, created lazily.
        """
        self.rag = rag_pipeline
        self._llm = llm_service  # injected or lazy

        # Per-session in-memory state (supplements session_manager)
        # key: session_id → {asked_embeddings, asked_texts, category_queue, covered}
        self._session_state: Dict[str, Dict] = {}

        logger.info("QuestionGenerator initialised")

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def init_session(self, session_id: str):
        """Initialise per-session state. Call once when interview starts."""
        self._session_state[session_id] = {
            "asked_embeddings": [],   # List[np.ndarray]
            "asked_texts": [],        # List[str]
            "category_queue": deque(CATEGORY_ROTATION * 3),  # enough for 18 Qs
            "covered_categories": [],
            "covered_skills": set(),
        }

    def generate_question(
        self,
        session_id: str,
        resume_data: Dict,
        question_number: int,
        previous_context: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate a unique, resume-grounded interview question.

        Args:
            session_id: Interview session ID
            resume_data: Structured resume (from ResumeParser)
            question_number: 1-indexed question number
            previous_context: {"previous_question": str, "previous_answer": str}

        Returns:
            Dict with question metadata
        """
        # Ensure session state exists
        if session_id not in self._session_state:
            self.init_session(session_id)

        role = resume_data.get("role", "Backend Engineer")
        state = self._session_state[session_id]
        difficulty = self._difficulty(resume_data.get("experience_years", 0))

        # Pick next category from rotation queue
        category = self._next_category(state)

        # Build retrieval query
        query = self._build_query(resume_data, question_number, category, previous_context)

        # Hybrid RAG retrieval
        context_chunks = self.rag.retrieve_hybrid(
            session_id=session_id,
            role=role,
            query=query,
            top_k=6,
        )

        # Separate resume vs. role context
        resume_ctx = [c["content"] for c in context_chunks if c.get("source") == "resume"]
        role_ctx   = [c["content"] for c in context_chunks if c.get("source") == "role"]

        # Generation + validation loop
        question_text = None
        for attempt in range(MAX_RETRIES):
            candidate = self._call_llm(
                role=role,
                resume_data=resume_data,
                resume_context=resume_ctx,
                rag_context=role_ctx,
                difficulty=difficulty,
                category=category,
                previous_context=previous_context,
                state=state,
            )

            if not candidate or len(candidate) < 15:
                continue

            # 1. Grounding validation — reject hallucinated tech
            if not self._is_grounded(candidate, resume_data):
                logger.warning(f"Attempt {attempt+1}: Question failed grounding — '{candidate[:60]}...'")
                continue

            # 2. Deduplication — reject if too similar to prior questions
            if self._is_duplicate(candidate, state):
                logger.warning(f"Attempt {attempt+1}: Question too similar to previous")
                continue

            # Passed both checks
            question_text = candidate
            break

        # Absolute fallback
        if not question_text:
            question_text = self._fallback_question(resume_data, category, question_number)

        # Update session state
        self._update_state(state, question_text, category, resume_data)

        return {
            "question_id": f"{session_id}_q{question_number}",
            "question_number": question_number,
            "question_text": question_text,
            "question_type": category,
            "difficulty": difficulty,
            "category": category,
            "context_used": [c.get("content", "")[:80] for c in context_chunks],
            "expected_depth": self._expected_depth(difficulty),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # LLM Integration
    # ──────────────────────────────────────────────────────────────────────────

    def _call_llm(
        self,
        role: str,
        resume_data: Dict,
        resume_context: List[str],
        rag_context: List[str],
        difficulty: str,
        category: str,
        previous_context: Optional[Dict],
        state: Dict,
    ) -> str:
        """Delegate to LLMService.generate_question()."""
        llm = self._get_llm()
        asked = state.get("asked_texts", [])
        return llm.generate_question(
            role=role,
            resume_context=resume_context,
            rag_context=rag_context,
            difficulty=difficulty,
            question_type=category,
            skills=resume_data.get("skills", []),
            domain=resume_data.get("domain", "General"),
            previous_questions=asked[-5:] if asked else [],
            resume_data=resume_data,
        )

    def _get_llm(self):
        if self._llm is None:
            from modules.llm_service import LLMService
            self._llm = LLMService()
        return self._llm

    # ──────────────────────────────────────────────────────────────────────────
    # Grounding Validation
    # ──────────────────────────────────────────────────────────────────────────

    def _is_grounded(self, question: str, resume_data: Dict) -> bool:
        """
        IMPROVED: Verify that question is actually about resume content.
        Checks:
        1. Mentions specific skills/projects/tools from resume
        2. Doesn't use generic "your main project" without naming it
        3. Doesn't introduce banned advanced topics
        """
        kg = resume_data.get("knowledge_graph") or {}
        allowed = set(kg.get("all_allowed_tech") or [])

        # Build comprehensive allowed set
        skills = resume_data.get("skills") or []
        tools = resume_data.get("tools") or []
        allowed.update(s.lower() for s in skills)
        allowed.update(t.lower() for t in tools)

        # Add project names
        projects = resume_data.get("projects") or {}
        if isinstance(projects, dict):
            allowed.update(p.lower() for p in projects.keys())

        # Add company names
        for exp in (resume_data.get("experience") or []):
            if isinstance(exp, dict) and exp.get("company"):
                allowed.add(exp.get("company").lower())

        # Also add raw resume words
        raw_text = (resume_data.get("raw_text") or "").lower()
        raw_words = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9_\-.]{2,30}\b", raw_text))
        allowed = allowed | raw_words

        q_lower = question.lower()

        # ✓ NEW: Question must mention something from resume
        resume_mentioned = False

        # Check 1: Specific skill?
        for skill in skills:
            if skill.lower() in q_lower:
                resume_mentioned = True
                logger.debug(f"✓ Grounded: mentions skill '{skill}'")
                break

        # Check 2: Specific project?
        if not resume_mentioned and isinstance(projects, dict):
            for proj in projects.keys():
                if proj.lower() in q_lower:
                    resume_mentioned = True
                    logger.debug(f"✓ Grounded: mentions project '{proj}'")
                    break

        # Check 3: Technology/tool?
        if not resume_mentioned:
            for tech in allowed:
                if len(tech) > 2 and tech in q_lower:
                    resume_mentioned = True
                    logger.debug(f"✓ Grounded: mentions tech '{tech}'")
                    break

        # ✓ NEW: Reject generic "your project" without naming it
        if "your project" in q_lower or "your main project" in q_lower:
            if isinstance(projects, dict) and projects:
                has_specific_name = any(
                    proj.lower() in q_lower for proj in projects.keys()
                )
                if not has_specific_name:
                    logger.debug("Grounding fail: Generic 'your project' without naming it")
                    return False

        if not resume_mentioned:
            logger.debug(f"Grounding fail: Doesn't mention resume content")
            return False

        # ✓ EXISTING: Check banned advanced topics
        banned_unless_in_resume = {
            "kubernetes", "k8s", "terraform", "ansible", "kafka", "rabbitmq",
            "microservices", "prometheus", "grafana", "mlflow", "kubeflow",
            "sagemaker", "valgrind", "zookeeper", "consul",
        }

        for banned in banned_unless_in_resume:
            if banned in q_lower and banned not in allowed:
                logger.debug(f"Grounding fail: '{banned}' not in resume")
                return False

        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Deduplication
    # ──────────────────────────────────────────────────────────────────────────

    def _is_duplicate(self, question: str, state: Dict) -> bool:
        """Return True if question is too similar to any previously asked question."""
        embeddings = state.get("asked_embeddings", [])
        if not embeddings:
            return False

        try:
            from sentence_transformers import SentenceTransformer
            # Use the same model as RAG pipeline
            if not hasattr(self, "_embed_model"):
                self._embed_model = SentenceTransformer("all-MiniLM-L6-v2")

            q_emb = self._embed_model.encode([question], convert_to_numpy=True)
            prev_embs = np.vstack(embeddings)

            from sklearn.metrics.pairwise import cosine_similarity
            sims = cosine_similarity(q_emb, prev_embs)[0]
            if np.max(sims) >= SIM_THRESHOLD:
                return True
        except Exception as e:
            logger.warning(f"Deduplication error (skipping check): {e}")

        return False

    # ──────────────────────────────────────────────────────────────────────────
    # Session State Management
    # ──────────────────────────────────────────────────────────────────────────

    def _update_state(self, state: Dict, question: str, category: str, resume_data: Dict):
        """Update in-memory session state after a question is accepted."""
        state["asked_texts"].append(question)
        state["covered_categories"].append(category)

        # Store embedding for deduplication
        try:
            if not hasattr(self, "_embed_model"):
                from sentence_transformers import SentenceTransformer
                self._embed_model = SentenceTransformer("all-MiniLM-L6-v2")
            emb = self._embed_model.encode([question], convert_to_numpy=True)
            state["asked_embeddings"].append(emb)
        except Exception as e:
            logger.warning(f"Could not store question embedding: {e}")

        # Mark skills covered
        skills = resume_data.get("skills") or []
        q_lower = question.lower()
        for skill in skills:
            if skill.lower() in q_lower:
                state["covered_skills"].add(skill.lower())

    def _next_category(self, state: Dict) -> str:
        """Pop the next category from the rotation queue."""
        q: deque = state.get("category_queue", deque(CATEGORY_ROTATION))
        if q:
            cat = q.popleft()
            # Never repeat the immediately preceding category
            if state["covered_categories"] and cat == state["covered_categories"][-1] and len(q) > 0:
                q.append(cat)
                cat = q.popleft()
            return cat
        return CATEGORY_ROTATION[len(state.get("covered_categories", [])) % len(CATEGORY_ROTATION)]

    # ──────────────────────────────────────────────────────────────────────────
    # Query Building
    # ──────────────────────────────────────────────────────────────────────────

    def _build_query(
        self,
        resume_data: Dict,
        question_number: int,
        category: str,
        previous_context: Optional[Dict],
    ) -> str:
        """Build a semantically rich retrieval query."""
        skills = (resume_data.get("skills") or [])[:3]
        
        projects_raw = resume_data.get("projects") or {}
        if isinstance(projects_raw, dict):
            projects_list = list(projects_raw.keys())
        elif isinstance(projects_raw, list):
            projects_list = []
            for p in projects_raw:
                if isinstance(p, dict):
                    projects_list.append(p.get("name") or p.get("title") or str(p))
                elif p:
                    projects_list.append(str(p))
        else:
            projects_list = []
        projects = projects_list[:2]
        
        role = resume_data.get("role", "software engineer")

        skill_str   = ", ".join(skills)   if skills   else "technical skills"
        project_str = ", ".join(projects) if projects else "projects"

        category_queries = {
            "conceptual":    f"fundamental concepts and theory behind {skill_str} in {role}",
            "project-based": f"implementation details and challenges in projects: {project_str}",
            "debugging":     f"debugging and troubleshooting errors in {skill_str} applications",
            "deployment":    f"deploying and managing {skill_str} projects in production basics",
            "scenario-based":f"real-world problem solving scenarios using {skill_str}",
            "real-world":    f"practical industry applications of {skill_str} for {role}",
        }

        query = category_queries.get(category, f"{skill_str} {role}")

        # Adapt if previous answer was very short (likely needs probing)
        if previous_context and len(previous_context.get("previous_answer") or "") < 50:
            query += " — follow-up clarification"

        return query

    # ──────────────────────────────────────────────────────────────────────────
    # Difficulty & Fallback
    # ──────────────────────────────────────────────────────────────────────────

    def _difficulty(self, experience_years: int) -> str:
        """Map experience years to difficulty level (capped at Intermediate)."""
        if experience_years <= 0:
            return "Basic"
        elif experience_years <= 3:
            return "Intermediate"
        else:
            return "Intermediate"  # Never generate Advanced as per requirement

    def _expected_depth(self, difficulty: str) -> str:
        return {
            "Basic":        "2-3 minutes, focus on fundamentals",
            "Intermediate": "3-5 minutes, demonstrate working knowledge",
        }.get(difficulty, "3-5 minutes")

    def _fallback_question(self, resume_data: Dict, category: str, question_number: int) -> str:
        """
        IMPROVED: Generate specific, resume-grounded fallback questions.
        Uses actual project/skill names instead of generic "your main project".
        """
        skills = resume_data.get("skills") or []

        projects_raw = resume_data.get("projects") or {}
        projects = []
        if isinstance(projects_raw, dict):
            projects = list(projects_raw.keys())
        elif isinstance(projects_raw, list):
            projects = []
            for p in projects_raw:
                if isinstance(p, dict):
                    projects.append(p.get("name") or p.get("title") or str(p))
                elif p:
                    projects.append(str(p))

        # Validate they exist before using
        if not skills and not projects:
            return "Tell me about your technical experience and the key projects you're most proud of."

        skill = skills[0] if skills else None
        project = projects[0] if projects else None

        fallbacks = {
            "conceptual": (
                f"Explain the core concepts of {skill} and how you applied it in {project}."
                if skill and project else
                f"Walk me through how {skill or 'your primary technology'} works."
            ),
            "project-based": (
                f"Tell me about the technical architecture of {project}. What were the main components?"
                if project else
                f"Walk me through how you built one of your key projects."
            ),
            "debugging": (
                f"Describe a challenging bug you encountered while building {project}."
                if project else
                f"Tell me about a bug you encountered in your work and how you fixed it."
            ),
            "deployment": (
                f"How did you deploy {project} to make it accessible to users?"
                if project else
                f"Tell me about your experience deploying applications."
            ),
            "scenario-based": (
                f"If you had to add a significant new feature to {project}, how would you approach it?"
                if project else
                f"How would you approach adding a new feature to one of your main projects?"
            ),
            "real-world": (
                f"What lessons from building {project} would you apply to solve new problems?"
                if project else
                f"Tell me about applying your {skill} skills to solve a real-world problem."
            ),
        }

        return fallbacks.get(category, f"Tell me about your experience with {skill}.")