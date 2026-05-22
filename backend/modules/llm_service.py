"""
LLM Service Module
Handles personalized interview question generation via Gemini API.

STRICT RESUME-GROUNDING RULES:
- Questions are 85% based on candidate's actual resume (projects, skills, tools)
- Only 15% general role/domain knowledge context
- NEVER introduce technologies not in the resume
- NEVER ask about microservices, distributed systems, advanced DevOps,
  async concurrency, or enterprise migration unless explicitly in the resume
- Difficulty: beginner to intermediate ONLY
- Questions must be natural, human-like, and non-repetitive
"""

import os
import re
import logging
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

ROLE_SKILLS_MAPPING = {
    "Backend Engineer":    ["python", "java", "node.js", "fastapi", "django", "spring",
                            "docker", "apis", "databases", "postgresql", "mysql", "redis",
                            "mongodb", "sqlite", "rest api", "git", "c#", "go", "rust"],
    "AI/ML Engineer":      ["python", "tensorflow", "pytorch", "scikit-learn", "nlp",
                            "deep learning", "machine learning", "keras", "pandas", "numpy",
                            "opencv", "gemini", "openai", "huggingface", "transformers"],
    "Full Stack Engineer": ["react", "node.js", "javascript", "typescript", "html", "css",
                            "vue", "angular", "python", "fastapi", "django", "databases",
                            "apis", "sql", "git", "vite"],
    "Data Scientist":      ["python", "sql", "pandas", "numpy", "statistics",
                            "scikit-learn", "machine learning", "r", "tableau", "power bi"],
    "DevOps Engineer":     ["docker", "kubernetes", "jenkins", "aws", "gcp", "terraform",
                            "ci/cd", "ansible", "git", "linux", "bash", "github actions"],
    "Frontend Developer":  ["react", "vue", "angular", "javascript", "typescript",
                            "html", "css", "next.js", "vite", "jest"],
    "Data Analyst":        ["sql", "python", "pandas", "excel", "tableau", "power bi",
                            "statistics", "data visualization", "r", "bigquery"],
}

# Advanced topics banned unless explicitly in resume
_BANNED_ADVANCED = {
    "infrastructure":  ["kubernetes", "k8s", "terraform", "ansible", "cloudformation",
                        "prometheus", "grafana", "autoscaling", "high availability"],
    "distributed":     ["microservices", "kafka", "rabbitmq", "zookeeper", "event-driven",
                        "message queue", "distributed system", "saga pattern", "cqrs"],
    "migration":       ["legacy migration", "monolith to microservices", "enterprise migration"],
    "memory_leak":     ["valgrind", "heap dump", "memory profiling", "memory leak"],
    "mlops":           ["kubeflow", "mlflow", "sagemaker", "feature store", "model pipeline"],
    "async_concurrency": ["asyncio", "async/await", "threading", "multiprocessing",
                          "event loop", "coroutine", "celery"],
}


class LLMService:
    """Interface for Gemini-powered interview question generation."""

    def __init__(self):
        self.gemini_key   = os.getenv("GEMINI_API_KEY")
        self.openai_key   = os.getenv("OPENAI_API_KEY")
        if self.gemini_key:
            logger.info("LLMService: Gemini API configured")
        elif self.openai_key:
            logger.info("LLMService: OpenAI API configured")
        else:
            logger.warning("LLMService: No API key found — question generation will fail")

    # ──────────────────────────────────────────────────────────────────────────
    # Question Generation
    # ──────────────────────────────────────────────────────────────────────────

    def generate_question(
        self,
        role: str,
        resume_context: List[str],
        rag_context: List[str],
        difficulty: str,
        question_type: str,
        skills: List[str],
        domain: str,
        previous_questions: List[str] = None,
        resume_data: dict = None,
    ) -> str:
        """
        Generate a single, personalized interview question.

        Returns the question text string, or an error string if both APIs fail.
        """
        prompt = self._build_question_prompt(
            role=role,
            resume_context=resume_context,
            rag_context=rag_context,
            difficulty=difficulty,
            question_type=question_type,
            skills=skills,
            domain=domain,
            previous_questions=previous_questions or [],
            resume_data=resume_data,
        )

        # 1. Try Gemini
        if self.gemini_key:
            result = self._call_gemini(prompt)
            if result:
                return result

        # 2. Try OpenAI
        if self.openai_key:
            result = self._call_openai(prompt)
            if result:
                return result

        logger.error("All LLM APIs failed — returning error string")
        return "ERROR: Could not generate question. Please configure a valid API key."

    # ──────────────────────────────────────────────────────────────────────────
    # Gemini / OpenAI Callers
    # ──────────────────────────────────────────────────────────────────────────

    def _call_gemini(self, prompt: str) -> Optional[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            text = response.text.strip()
            logger.info("Question generated via Gemini")
            return text
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            return None

    def _call_openai(self, prompt: str) -> Optional[str]:
        try:
            import openai
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer."},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.7,
                max_tokens=200,
            )
            text = response.choices[0].message["content"].strip()
            logger.info("Question generated via OpenAI")
            return text
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # Prompt Building — Question Generation
    # ──────────────────────────────────────────────────────────────────────────

    def _build_question_prompt(
        self,
        role: str,
        resume_context: List[str],
        rag_context: List[str],
        difficulty: str,
        question_type: str,
        skills: List[str],
        domain: str,
        previous_questions: List[str],
        resume_data: Optional[dict],
    ) -> str:
        """Build the strict resume-grounded question generation prompt."""

        # ── Candidate profile from resume_data ──────────────────────────────
        candidate_name  = "Candidate"
        experience_years = 0
        resume_skills_str   = "None"
        resume_projects_str = "None"
        knowledge_graph_str = "None"
        allowed_tech_str    = "Only technologies explicitly in the resume"

        if resume_data:
            candidate_name   = resume_data.get("candidate_name", "Candidate")
            experience_years = int(resume_data.get("experience_years") or 0)

            # Filter skills relevant to role
            role_kws = {k.lower() for k in ROLE_SKILLS_MAPPING.get(role, [])}
            raw_skills = resume_data.get("skills") or []
            relevant_skills = [s for s in raw_skills
                               if any(kw in s.lower() for kw in role_kws)] or raw_skills[:6]
            resume_skills_str = ", ".join(relevant_skills) or "None"

            # Projects
            projects = resume_data.get("projects") or {}
            if isinstance(projects, dict):
                proj_lines = []
                for name, det in list(projects.items())[:6]:
                    if isinstance(det, dict):
                        tech = ", ".join((det.get("skills") or []) + (det.get("tools") or []))
                        proj_lines.append(f"  - {name}: {tech or 'see resume'}")
                    else:
                        proj_lines.append(f"  - {name}")
                resume_projects_str = "\n".join(proj_lines) or "None"
            else:
                resume_projects_str = "\n".join(f"  - {p}" for p in (projects or []))

            # Knowledge graph
            kg = resume_data.get("knowledge_graph") or {}
            kg_lines = []
            if kg.get("projects"):
                kg_lines.append("Project → Skills mapping:")
                for pname, pdet in kg["projects"].items():
                    tech = ", ".join(pdet.get("skills") or [])
                    kg_lines.append(f"  '{pname}' uses: {tech or 'unspecified'}")
            if kg.get("experience"):
                kg_lines.append("Work Experience → Skills mapping:")
                for exp in kg["experience"]:
                    tech = ", ".join(exp.get("skills") or [])
                    job  = f"{exp.get('role','')} at {exp.get('company','')}"
                    kg_lines.append(f"  '{job}' applied: {tech or 'unspecified'}")
            knowledge_graph_str = "\n".join(kg_lines) or "None"

            # Allowed tech set
            allowed_tech = sorted(set(kg.get("all_allowed_tech") or []))
            allowed_tech_str = ", ".join(allowed_tech[:40]) or "Only technologies in resume"

        # ── Disallowed topics ────────────────────────────────────────────────
        full_resume_text = (resume_data.get("raw_text") or "").lower() if resume_data else ""
        disallowed_lines = []
        for category, keywords in _BANNED_ADVANCED.items():
            if not any(kw in full_resume_text for kw in keywords):
                pretty = {
                    "infrastructure":    "production infrastructure (Kubernetes, Terraform, Ansible, Prometheus)",
                    "distributed":       "distributed systems and microservices (Kafka, RabbitMQ, CAP theorem)",
                    "migration":         "legacy/enterprise system migration",
                    "memory_leak":       "memory leak debugging and profiling",
                    "mlops":             "advanced MLOps (Kubeflow, MLflow, SageMaker)",
                    "async_concurrency": "async/concurrency patterns (asyncio, threading, event loops)",
                }.get(category, category)
                disallowed_lines.append(f"  - Do NOT ask about: {pretty}")

        disallowed_block = (
            "BANNED TOPICS (not in resume — do not reference):\n" + "\n".join(disallowed_lines)
            if disallowed_lines else
            "Focus on practical project-level understanding."
        )

        # ── Previous questions ───────────────────────────────────────────────
        prev_qs = "\n".join(f"  - {q}" for q in (previous_questions or [])) or "  None"

        # ── Sanitize RAG context ─────────────────────────────────────────────
        allowed_words = set(re.findall(r"\b[a-z][a-z0-9_\-]{2,30}\b", full_resume_text))
        clean_rag = self._sanitize_rag(rag_context, allowed_words)

        return f"""Generate a single technical interview question for a {role} candidate.

══════════════════════════════════════════
STRICT GROUNDING RULES (read carefully):
══════════════════════════════════════════
1. Generate EXACTLY ONE question — no preamble, no explanation, just the question.
2. Ground the question 85% in the candidate's ACTUAL resume content (projects, skills, experience).
3. Use role/domain knowledge (15%) only to add context or industry framing.
4. ONLY mention technologies in this whitelist: {allowed_tech_str}
5. NEVER introduce technologies, architectures, or tools not in the whitelist.
6. NEVER mix technologies across unrelated projects.
7. Do NOT use phrases like "Based on your resume...", "I see that...", "I notice...".
8. Do NOT generate senior/enterprise-level questions.
9. Difficulty: {difficulty} — keep it beginner to intermediate.
10. Question category (focus on this type): {question_type}

{disallowed_block}

══════════════════════════════════════════
CANDIDATE PROFILE
══════════════════════════════════════════
Name: {candidate_name}
Role: {role}
Experience: {experience_years} years
Skills: {resume_skills_str}

Projects:
{resume_projects_str}

Resume Knowledge Graph (project-to-skills connections):
{knowledge_graph_str}

Resume Context (direct resume text — use this as primary source):
{chr(10).join(resume_context)[:1200]}

Role/Domain Context (15% usage only — secondary):
{chr(10).join(clean_rag)[:600]}

Previously Asked Questions (do NOT repeat or closely resemble these):
{prev_qs}

══════════════════════════════════════════
Generate the question now (output ONLY the question, ending with ?):
"""

    # ──────────────────────────────────────────────────────────────────────────
    # RAG Context Sanitizer
    # ──────────────────────────────────────────────────────────────────────────

    def _sanitize_rag(self, rag_context: List[str], allowed_words: set) -> List[str]:
        """Remove lines from RAG context that mention banned advanced topics not in resume."""
        banned = {
            "kubernetes", "k8s", "terraform", "ansible", "kafka", "rabbitmq",
            "prometheus", "grafana", "zookeeper", "microservices", "mlflow",
            "kubeflow", "sagemaker", "valgrind", "saga", "cqrs",
        }
        sanitized = []
        for chunk in rag_context:
            clean_lines = []
            for line in chunk.split("\n"):
                line_lower = line.lower()
                if any(b in line_lower and b not in allowed_words for b in banned):
                    continue
                clean_lines.append(line)
            if clean_lines:
                sanitized.append("\n".join(clean_lines))
        return sanitized

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers (backward compatibility)
    # ──────────────────────────────────────────────────────────────────────────

    def _is_allowed_topic(self, category: str, resume_data: dict, resume_context: List[str]) -> bool:
        """Check if an advanced topic is explicitly in the resume."""
        texts = []
        if resume_data:
            texts.append(resume_data.get("raw_text") or "")
            texts.extend(resume_data.get("skills") or [])
        texts.extend(resume_context or [])
        full = " ".join(texts).lower()
        keywords = {kw for kws in _BANNED_ADVANCED.values() for kw in kws}
        cat_kws  = _BANNED_ADVANCED.get(category, [])
        return any(kw in full for kw in cat_kws)

    def _clean_project_name(self, proj: str) -> str:
        if not proj:
            return "your project"
        title = proj.split("\n")[0].strip()
        title = title.split("|")[0].strip()
        title = re.split(r"\s+[\-\–\—]\s+", title)[0].strip()
        title = re.split(r"\s+[\(\[]", title)[0].strip()
        title = title.rstrip(" :,-–—")
        return title[:60].strip() if len(title) >= 3 else "your project"
