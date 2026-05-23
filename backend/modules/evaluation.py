"""
Candidate Evaluation Module
Generates a comprehensive skill analysis report using Gemini API.
Analyzes technical depth, communication, confidence, and interview readiness.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


@dataclass
class EvaluationReport:
    """Structured evaluation report for a candidate."""
    session_id: str
    candidate_name: str
    role: str

    # Per-skill scores (0-100)
    skill_scores: Dict[str, int]

    # Category scores (0-100)
    technical_score: int
    communication_score: int
    confidence_score: int

    # Final composite
    final_score: int
    interview_readiness: str   # "Strong" | "Moderate" | "Needs Preparation"

    # Qualitative analysis
    strengths: List[str]
    weak_areas: List[str]
    improvement_suggestions: List[str]

    # Meta
    questions_answered: int
    questions_skipped: int
    avg_answer_length: int
    generation_method: str  # "gemini" | "heuristic"

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Gemini evaluation prompt ──────────────────────────────────────────────────
_EVALUATION_PROMPT = """
You are an expert technical interviewer and talent evaluator.
Analyze the following interview transcript and generate a structured evaluation report.
Return ONLY a valid JSON object — no markdown, no explanation.

JSON Schema:
{{
  "skill_scores": {{
    "<skill_name>": <integer 0-100>,
    ...
  }},
  "technical_score": <integer 0-100>,
  "communication_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "final_score": <integer 0-100>,
  "interview_readiness": "<Strong|Moderate|Needs Preparation>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weak_areas": ["<area 1>", "<area 2>"],
  "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>", "<suggestion 3>"]
}}

SCORING GUIDELINES:
- skill_scores: Score each skill mentioned in the resume AND discussed in the interview (0-100)
  - 90-100: Expert level, highly detailed responses
  - 70-89: Good working knowledge, clear explanations
  - 50-69: Basic understanding, some gaps
  - 30-49: Limited knowledge, superficial answers
  - 0-29: Little to no demonstrated knowledge
- technical_score: Overall technical depth across all answers
- communication_score: Clarity, structure, and articulation of answers
- confidence_score: Certainty, directness, and completeness of responses (penalize "I don't know" or very short answers)
- final_score: Weighted composite (60% technical, 25% communication, 15% confidence)
- interview_readiness:
  - "Strong" if final_score >= 70
  - "Moderate" if final_score >= 50
  - "Needs Preparation" otherwise
- strengths: 3 specific technical or behavioral strengths demonstrated
- weak_areas: 2 specific areas where knowledge gaps were evident
- improvement_suggestions: 3 actionable, specific suggestions tailored to their resume

IMPORTANT:
- Base scores ONLY on actual answers given, not resume claims
- If a question was SKIPPED, that skill scores lower
- Be honest but constructive — this helps candidates improve
- Suggestions must be specific to technologies/projects in their resume

Candidate Profile:
  Name: {candidate_name}
  Role: {role}
  Experience: {experience_years} years
  Skills: {skills}
  Projects: {projects}

Interview Transcript:
{transcript}
"""


class CandidateEvaluator:
    """Evaluates interview performance and generates a skill analysis report."""

    def __init__(self):
        self._gemini_key = os.getenv("GEMINI_API_KEY")

    # ─── Public API ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        session_id: str,
        qa_pairs: List[Dict],
        resume_data: Dict,
        role: str,
    ) -> EvaluationReport:
        """
        Generate a full evaluation report for a completed interview session.

        Args:
            session_id: The interview session ID
            qa_pairs: List of {"question": str, "answer": str} dicts
            resume_data: Structured resume dict (from ResumeParser)
            role: Target job role

        Returns:
            EvaluationReport dataclass
        """
        candidate_name = resume_data.get("candidate_name", "Candidate")

        # Stats
        answered = [qa for qa in qa_pairs if qa.get("answer") and qa["answer"] != "[SKIPPED]"]
        skipped  = [qa for qa in qa_pairs if not qa.get("answer") or qa["answer"] == "[SKIPPED]"]
        avg_len  = (
            sum(len(qa["answer"]) for qa in answered) // max(len(answered), 1)
        ) if answered else 0

        # Try Gemini first
        report_data = None
        method = "heuristic"
        if self._gemini_key and qa_pairs:
            report_data = self._gemini_evaluate(qa_pairs, resume_data, role)
            if report_data:
                method = "gemini"

        # Heuristic fallback
        if not report_data:
            report_data = self._heuristic_evaluate(qa_pairs, resume_data, role)

        return EvaluationReport(
            session_id=session_id,
            candidate_name=candidate_name,
            role=role,
            skill_scores=report_data.get("skill_scores", {}),
            technical_score=report_data.get("technical_score", 50),
            communication_score=report_data.get("communication_score", 50),
            confidence_score=report_data.get("confidence_score", 50),
            final_score=report_data.get("final_score", 50),
            interview_readiness=report_data.get("interview_readiness", "Moderate"),
            strengths=report_data.get("strengths", []),
            weak_areas=report_data.get("weak_areas", []),
            improvement_suggestions=report_data.get("improvement_suggestions", []),
            questions_answered=len(answered),
            questions_skipped=len(skipped),
            avg_answer_length=avg_len,
            generation_method=method,
        )

    # ─── Gemini Evaluation ─────────────────────────────────────────────────────

    def _gemini_evaluate(
        self,
        qa_pairs: List[Dict],
        resume_data: Dict,
        role: str,
    ) -> Optional[Dict]:
        """Call Gemini to generate a structured evaluation report."""
        try:
            from google import genai
            client = genai.Client(api_key=self._gemini_key)

            # Build transcript
            transcript_lines = []
            for i, qa in enumerate(qa_pairs, 1):
                q = qa.get("question") or qa.get("question_text", "")
                a = qa.get("answer", "[SKIPPED]")
                transcript_lines.append(f"Q{i}: {q}")
                transcript_lines.append(f"A{i}: {a}")
                transcript_lines.append("")

            # Projects summary
            projects_raw = resume_data.get("projects") or {}
            proj_summary_list = []
            if isinstance(projects_raw, dict):
                for name, d in list(projects_raw.items())[:5]:
                    if isinstance(d, dict):
                        tech = ", ".join((d.get('skills') or [])[:4])
                        proj_summary_list.append(f"{name}: {tech}")
                    else:
                        proj_summary_list.append(f"{name}")
            elif isinstance(projects_raw, list):
                for p in projects_raw[:5]:
                    if isinstance(p, dict):
                        name = p.get("name") or p.get("title") or "Project"
                        tech = ", ".join((p.get('skills') or [])[:4])
                        proj_summary_list.append(f"{name}: {tech}")
                    elif p:
                        proj_summary_list.append(str(p))
            proj_summary = "; ".join(proj_summary_list) or "None listed"

            prompt = _EVALUATION_PROMPT.format(
                candidate_name=resume_data.get("candidate_name", "Candidate"),
                role=role,
                experience_years=resume_data.get("experience_years", 0),
                skills=", ".join((resume_data.get("skills") or [])[:20]),
                projects=proj_summary,
                transcript="\n".join(transcript_lines)[:6000],
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

            data = json.loads(text)
            return self._validate_report_data(data)

        except json.JSONDecodeError as e:
            logger.warning(f"Gemini evaluation JSON error: {e}")
            return None
        except Exception as e:
            logger.error(f"Gemini evaluation failed: {e}")
            return None

    def _validate_report_data(self, data: Dict) -> Dict:
        """Ensure all required fields are present and within range."""
        def clamp(v, lo=0, hi=100):
            try:
                return max(lo, min(hi, int(v)))
            except Exception:
                return 50

        skill_scores = {}
        raw_ss = data.get("skill_scores") or {}
        for k, v in raw_ss.items():
            skill_scores[str(k)] = clamp(v)

        technical    = clamp(data.get("technical_score", 50))
        communication = clamp(data.get("communication_score", 50))
        confidence   = clamp(data.get("confidence_score", 50))

        # Recalculate final score with weights
        final = clamp(technical * 0.60 + communication * 0.25 + confidence * 0.15)

        readiness_raw = str(data.get("interview_readiness", ""))
        if "strong" in readiness_raw.lower():
            readiness = "Strong"
        elif "moderate" in readiness_raw.lower():
            readiness = "Moderate"
        else:
            readiness = "Needs Preparation"

        def ensure_list(v, default):
            if isinstance(v, list) and v:
                return [str(x) for x in v[:5]]
            return default

        return {
            "skill_scores": skill_scores,
            "technical_score": technical,
            "communication_score": communication,
            "confidence_score": confidence,
            "final_score": final,
            "interview_readiness": readiness,
            "strengths": ensure_list(
                data.get("strengths"),
                ["Completed the interview", "Engaged with technical questions"]
            ),
            "weak_areas": ensure_list(
                data.get("weak_areas"),
                ["Needs more practice articulating technical concepts"]
            ),
            "improvement_suggestions": ensure_list(
                data.get("improvement_suggestions"),
                ["Review project implementations in detail",
                 "Practice explaining technical choices verbally"]
            ),
        }

    # ─── Heuristic Fallback ────────────────────────────────────────────────────

    def _heuristic_evaluate(
        self,
        qa_pairs: List[Dict],
        resume_data: Dict,
        role: str,
    ) -> Dict:
        """Keyword + length-based heuristic evaluation when Gemini is unavailable."""
        answered = [
            qa for qa in qa_pairs
            if qa.get("answer") and qa["answer"] != "[SKIPPED]"
        ]
        skipped_count = len(qa_pairs) - len(answered)

        if not answered:
            return {
                "skill_scores": {},
                "technical_score": 0,
                "communication_score": 0,
                "confidence_score": 0,
                "final_score": 0,
                "interview_readiness": "Needs Preparation",
                "strengths": [],
                "weak_areas": ["No answers provided"],
                "improvement_suggestions": ["Attempt all interview questions"],
            }

        avg_len = sum(len(qa["answer"]) for qa in answered) // len(answered)
        all_answers = " ".join(qa["answer"] for qa in answered).lower()

        # Technical score (answer length + technical vocabulary density)
        tech_keywords = {"implement", "design", "algorithm", "database", "api",
                         "function", "class", "model", "train", "optimize",
                         "deploy", "debug", "test", "framework", "library"}
        tech_hits = sum(1 for kw in tech_keywords if kw in all_answers)
        technical = min(100, max(20, int(
            (min(avg_len, 600) / 600) * 50 + (tech_hits / len(tech_keywords)) * 50
        )))

        # Communication score (answer completeness)
        communication = min(100, max(20, int((min(avg_len, 400) / 400) * 100)))

        # Confidence (penalize skips)
        confidence = max(20, 80 - skipped_count * 15)

        final = int(technical * 0.60 + communication * 0.25 + confidence * 0.15)

        readiness = (
            "Strong" if final >= 70
            else "Moderate" if final >= 50
            else "Needs Preparation"
        )

        # Per-skill scores based on mention in answers
        skills = resume_data.get("skills") or []
        skill_scores = {}
        for skill in skills[:10]:
            if skill.lower() in all_answers:
                skill_scores[skill] = min(100, technical + 10)
            else:
                skill_scores[skill] = max(20, technical - 20)

        strengths = []
        if avg_len > 400:
            strengths.append("Provides detailed, comprehensive answers")
        if tech_hits >= 5:
            strengths.append("Demonstrates strong technical vocabulary")
        if skipped_count == 0:
            strengths.append("Attempted all questions — shows commitment")
        if not strengths:
            strengths.append("Engaged throughout the interview process")

        weak_areas = []
        if avg_len < 100:
            weak_areas.append("Answers are too brief — need more detail and explanation")
        if tech_hits < 3:
            weak_areas.append("Could incorporate more technical terminology")
        if skipped_count > 0:
            weak_areas.append(f"Skipped {skipped_count} question(s)")
        if not weak_areas:
            weak_areas.append("Review edge cases and error handling scenarios")

        suggestions = [
            "Practice explaining your project implementations step by step",
            "Review the core concepts of the technologies in your resume",
            "Record yourself answering questions to improve clarity and delivery",
        ]

        return {
            "skill_scores": skill_scores,
            "technical_score": technical,
            "communication_score": communication,
            "confidence_score": confidence,
            "final_score": final,
            "interview_readiness": readiness,
            "strengths": strengths[:3],
            "weak_areas": weak_areas[:3],
            "improvement_suggestions": suggestions,
        }
