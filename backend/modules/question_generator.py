"""
Question Generation Module
Generates contextual interview questions using RAG
"""

import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """Generate interview questions based on RAG context"""
    
    def __init__(self, rag_pipeline):
        """
        Initialize question generator
        
        Args:
            rag_pipeline: RAGPipeline instance for context retrieval
        """
        self.rag_pipeline = rag_pipeline
        
        # Question templates categorized by difficulty and type
        self.question_templates = {
            "Conceptual": [
                "Explain the key differences between {topic1} and {topic2}",
                "What are the main advantages and disadvantages of using {topic}?",
                "How does {concept} work in the context of {domain}?",
                "What are the best practices for {topic}?",
            ],
            "Applied": [
                "How would you implement {topic} in a real-world scenario?",
                "Design a solution for {problem} using {technology}",
                "Walk me through your approach to solving {problem}",
                "What trade-offs would you consider when {action}?",
            ],
            "Challenge": [
                "How would you optimize {system} for {constraint}?",
                "What are the potential issues with {approach} and how would you mitigate them?",
                "Given {constraints}, how would you design {system}?",
                "What's a complex problem you'd solve using {skill}?",
            ],
            "Experience": [
                "Tell me about your experience with {technology}",
                "Describe a project where you used {skill}",
                "What challenges did you face with {topic} and how did you overcome them?",
                "How have you applied {concept} in your previous work?",
            ]
        }
        
        logger.info("Question Generator initialized")
    
    def generate_question(
        self,
        session_id: str,
        resume_data: Dict,
        question_number: int,
        previous_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate an interview question based on resume and RAG context
        
        Args:
            session_id: Interview session ID
            resume_data: Extracted resume data
            question_number: Question number in sequence
            previous_context: Context from previous question/answer
            
        Returns:
            Dictionary with generated question and metadata
        """
        try:
            role = resume_data.get("role", "Backend Engineer")
            skills = resume_data.get("skills", [])
            domain = resume_data.get("domain", "General")
            experience_years = resume_data.get("experience_years", 0)
            
            # Determine question difficulty based on experience
            difficulty = self._determine_difficulty(experience_years, question_number)
            
            # Build retrieval query
            query = self._build_query(
                role=role,
                resume_data=resume_data,
                question_number=question_number,
                previous_context=previous_context
            )
            
            # Retrieve relevant context from knowledge base
            context_chunks = self.rag_pipeline.retrieve_context(role, query, top_k=3)
            
            # Select question type
            question_type = self._select_question_type(
                question_number=question_number,
                experience_years=experience_years,
                skills=skills
            )
            
            # Generate question using context
            question = self._create_question(
                role=role,
                question_type=question_type,
                difficulty=difficulty,
                skills=skills,
                domain=domain,
                context_chunks=context_chunks,
                previous_context=previous_context
            )
            
            return {
                "question_id": f"{session_id}_q{question_number}",
                "question_number": question_number,
                "question_text": question,
                "question_type": question_type,
                "difficulty": difficulty,
                "category": self._categorize_question(question, role),
                "context_used": [c.get("content", "")[:100] for c in context_chunks],
                "expected_depth": self._get_expected_depth(difficulty, question_type)
            }
            
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            # Return fallback question
            return self._get_fallback_question(question_number)
    
    def _build_query(
        self,
        role: str,
        resume_data: Dict,
        question_number: int,
        previous_context: Optional[Dict] = None
    ) -> str:
        """Build search query for RAG retrieval"""
        
        skills = ", ".join(resume_data.get("skills", [])[:3])
        domain = resume_data.get("domain", "General")
        
        # Different queries based on question progression
        if question_number == 1:
            query = f"fundamental concepts in {role} with focus on {domain}"
        elif question_number == 2:
            query = f"practical applications of {skills} in {role}"
        elif question_number == 3:
            query = f"system design and architecture in {role}"
        elif question_number == 4:
            query = f"advanced topics and optimization in {role}"
        else:
            query = f"edge cases and problem-solving approaches in {role}"
        
        # Adapt query if there's previous context
        if previous_context:
            prev_answer = previous_context.get("previous_answer", "")
            # Could enhance query based on previous answer quality
            if len(prev_answer) < 50:
                query += " detailed explanation required"
        
        return query
    
    def _determine_difficulty(self, experience_years: int, question_number: int) -> str:
        """Determine question difficulty"""
        
        # Adapt difficulty based on experience and question progression
        base_difficulty = {
            0: "Basic",      # 0 years
            1: "Intermediate",  # 1-2 years
            2: "Intermediate",  # 2-5 years
            3: "Advanced",      # 5+ years
        }
        
        years_category = min(3, experience_years // 2)
        base = base_difficulty.get(years_category, "Intermediate")
        
        # Increase difficulty with question progression
        if question_number >= 4:
            if base == "Basic":
                base = "Intermediate"
            elif base == "Intermediate":
                base = "Advanced"
        
        return base
    
    def _select_question_type(
        self,
        question_number: int,
        experience_years: int,
        skills: List[str]
    ) -> str:
        """Select question type based on progression"""
        
        types_sequence = ["Conceptual", "Applied", "Challenge", "Experience", "Challenge"]
        
        # For experienced candidates, adjust sequence
        if experience_years >= 5:
            types_sequence = ["Applied", "Challenge", "Challenge", "Experience", "Challenge"]
        elif experience_years >= 2:
            types_sequence = ["Conceptual", "Applied", "Challenge", "Experience", "Challenge"]
        
        return types_sequence[min(question_number - 1, len(types_sequence) - 1)]
    
    def _create_question(
        self,
        role: str,
        question_type: str,
        difficulty: str,
        skills: List[str],
        domain: str,
        context_chunks: List[Dict],
        previous_context: Optional[Dict] = None
    ) -> str:
        """Create the actual question using context"""
        
        # Get template
        template = self._select_template(question_type, difficulty, skills)
        
        # Extract key topics from context
        topics = self._extract_topics(context_chunks, skills)
        
        # Fill template with extracted information
        question = self._fill_template(template, topics, role, domain, skills)
        
        return question
    
    def _select_template(self, question_type: str, difficulty: str, skills: List[str]) -> str:
        """Select appropriate template for question"""
        
        templates = {
            "Conceptual": [
                "Explain the key differences between {topic1} and {topic2} in {role}.",
                "What are the main advantages of {topic} compared to traditional approaches?",
                "How does {concept} contribute to building {system}?",
                "What principles should guide {topic} in {role}?",
            ],
            "Applied": [
                "How would you implement {topic} for a {scale} system?",
                "Design an approach to solve {problem} using your {skill} expertise.",
                "Walk us through your thought process for {task}.",
                "What would be your practical approach to {problem}?",
            ],
            "Challenge": [
                "How would you scale {system} when {constraint}?",
                "What architectural changes would be needed if {scenario}?",
                "Given these constraints {constraints}, how would you optimize {system}?",
                "Design a system that handles {challenge} efficiently.",
            ],
            "Experience": [
                "Tell me about a time you worked with {topic} - what did you learn?",
                "Can you share an experience where you improved {system} using {skill}?",
                "Describe a challenging project where you applied {concept}.",
                "How have you used {skill} to solve real-world problems?",
            ]
        }
        
        q_templates = templates.get(question_type, templates["Applied"])
        
        # Select based on difficulty
        if difficulty == "Basic":
            return q_templates[0] if len(q_templates) > 0 else "Tell me about your experience with {topic}"
        elif difficulty == "Advanced":
            return q_templates[-1] if len(q_templates) > 0 else "How would you optimize {system}?"
        else:
            return q_templates[len(q_templates) // 2] if q_templates else "How would you implement {topic}?"
    
    def _extract_topics(self, context_chunks: List[Dict], skills: List[str]) -> Dict:
        """Extract key topics from retrieved context"""
        
        topics = {
            "topic": "your expertise",
            "topic1": "first approach",
            "topic2": "alternative approach",
            "concept": "important concept",
            "system": "system",
            "problem": "challenge",
            "task": "technical task",
            "skill": skills[0] if skills else "technical skills",
            "scenario": "a sudden traffic spike",
            "constraint": "increased load",
            "challenge": "scale",
        }
        
        # Try to extract from context chunks
        if context_chunks:
            # Enhanced with actual context content
            first_chunk = context_chunks[0].get("content", "").split(":")
            if len(first_chunk) > 1:
                topics["concept"] = first_chunk[0].strip()[:30]
        
        return topics
    
    def _fill_template(
        self,
        template: str,
        topics: Dict,
        role: str,
        domain: str,
        skills: List[str]
    ) -> str:
        """Fill template with actual content"""
        
        # Map placeholders
        question = template
        
        for placeholder, value in topics.items():
            question = question.replace("{" + placeholder + "}", str(value))
        
        question = question.replace("{role}", role)
        question = question.replace("{domain}", domain)
        question = question.replace("{scale}", "production")
        
        # Remove any remaining unreplaced placeholders
        import re
        question = re.sub(r'\{[^}]+\}', '', question)
        
        # Clean up question
        question = question.strip()
        if not question.endswith('?'):
            question += '?'
        
        return question
    
    def _categorize_question(self, question: str, role: str) -> str:
        """Categorize question based on content"""
        
        q_lower = question.lower()
        
        if "design" in q_lower or "architecture" in q_lower:
            return "System Design"
        elif "explain" in q_lower or "understand" in q_lower:
            return "Conceptual"
        elif "implement" in q_lower or "code" in q_lower:
            return "Implementation"
        elif "optimize" in q_lower or "improve" in q_lower:
            return "Optimization"
        elif "challenge" in q_lower or "difficult" in q_lower:
            return "Problem Solving"
        else:
            return "General Technical"
    
    def _get_expected_depth(self, difficulty: str, question_type: str) -> str:
        """Get expected answer depth"""
        
        if difficulty == "Basic":
            return "2-3 minutes, covering fundamentals"
        elif difficulty == "Advanced":
            return "5-10 minutes, deep technical insight expected"
        else:
            return "3-5 minutes, solid understanding required"
    
    def _get_fallback_question(self, question_number: int) -> Dict:
        """Return fallback question if generation fails"""
        
        fallback_questions = [
            "Tell us about your background and what interests you in this role.",
            "What are your strongest technical skills and why?",
            "Can you describe a complex technical problem you've solved?",
            "How do you stay updated with new technologies in your field?",
            "What's your approach to writing clean, maintainable code?",
        ]
        
        q = fallback_questions[min(question_number - 1, len(fallback_questions) - 1)]
        
        return {
            "question_id": f"fallback_q{question_number}",
            "question_number": question_number,
            "question_text": q,
            "question_type": "Experience",
            "difficulty": "Intermediate",
            "category": "General",
            "context_used": [],
            "expected_depth": "3-5 minutes"
        }