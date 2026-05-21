"""
LLM Service Module
Handles generating personalized screening questions using API or local context-synthesis fallback

COMPREHENSIVE QUESTION GENERATION RULES - STRICT RESUME-ONLY MODE
==================================================================

CORE REQUIREMENTS:
- Generate ONE realistic interview question STRICTLY grounded in candidate's actual resume
- ONLY ask about technologies, tools, projects, skills, or concepts explicitly mentioned in resume
- NEVER introduce unrelated technologies, architectures, frameworks, or concepts
- NEVER mix technologies across unrelated projects
- NEVER hallucinate tools, databases, APIs, async systems, microservices, distributed systems, or production infrastructure unless explicitly present

QUESTION QUALITY:
- Do NOT generate senior-level or enterprise-level questions
- Keep difficulty beginner to intermediate level
- Prioritize project-based and practical questions over theoretical ones
- Avoid generic AI-generated wording and boilerplate phrases
- Keep questions concise, conversational, and natural-sounding

FOCUS AREAS:
- Projects and implementation details
- Debugging and troubleshooting
- Deployment basics
- Model training (if applicable)
- APIs actually used
- Databases actually used
- Real problems faced during development

PROJECT-TECH VALIDATION:
- Verify technology is actually connected to the project (e.g., TensorFlow + Crop Detection → VALID)
- Validate against Resume Relational Knowledge Graph

SECTION FILTERING:
- Use ONLY: Technical Skills, Internship, Projects
- IGNORE: Leadership, NSS, Extracurricular activities, Hobbies

SECTION FILTERING RULE:
Use ONLY these resume sections:
- Technical Skills
- Internship
- Projects

Do NOT use:
- Leadership
- NSS
- Extracurricular activities
- Hobbies
"""

import os
import random
import logging
from typing import List

logger = logging.getLogger(__name__)

ROLE_SKILLS_MAPPING = {
    "Backend Engineer": ["python", "java", "node.js", "fastapi", "django", "spring", "docker", "kubernetes", "apis", "databases", "postgresql", "mysql", "redis", "mongodb", "sqlite", "rest api", "system design", "git", "c#", "go", "rust"],
    "AI/ML Engineer": ["python", "tensorflow", "pytorch", "scikit-learn", "nlp", "deep learning", "machine learning", "neural networks", "transformers", "keras", "pandas", "numpy", "opencv", "data science"],
    "Full Stack Engineer": ["react", "node.js", "javascript", "typescript", "html", "css", "vue", "angular", "python", "fastapi", "django", "docker", "databases", "apis", "devops", "sql", "git"],
    "Data Scientist": ["python", "sql", "pandas", "numpy", "statistics", "data visualization", "scikit-learn", "machine learning", "r", "tableau", "power bi", "hadoop", "spark", "big data"],
    "DevOps Engineer": ["docker", "kubernetes", "jenkins", "aws", "gcp", "terraform", "ci/cd", "ansible", "git", "cloud", "linux", "bash", "monitoring", "prometheus", "grafana"]
}

class LLMService:
    """Service to interface with LLM API or fallback to local context synthesizer"""
    
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.huggingface_key = os.getenv("HUGGINGFACE_API_KEY")
        if self.gemini_key:
            logger.info("LLMService initialized with Gemini integration")
        elif self.openai_key:
            logger.info("LLMService initialized with OpenAI integration")
        elif self.huggingface_key:
            logger.info("LLMService initialized with HuggingFace integration")
        else:
            logger.info("LLMService initialized with Local Fallback Synthesizer")

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
        resume_data: dict = None
    ) -> str:
        """
        Generate a personalized interview question
        
        STRICT REQUIREMENT: Questions are constrained to:
        - Technologies explicitly mentioned in resume
        - Projects explicitly mentioned in resume  
        - Tools actually used in those projects
        
        DISABLED: Local fallback completely disabled.
        Uses ONLY external LLM APIs (Gemini → OpenAI) to prevent hallucinations.
        Does NOT introduce:
        - Advanced backend architecture (microservices, distributed systems, message queues)
        - Production infrastructure (Kubernetes, Terraform, Ansible, monitoring)
        - Async/concurrency patterns (unless in resume)
        - Production scaling strategies (unless in resume)
        - Advanced MLOps (unless in resume)
        """
        # 1. Try Gemini API if configured
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = self._build_prompt(role, resume_context, rag_context, difficulty, question_type, skills, domain, previous_questions, resume_data)
                response = model.generate_content(prompt)
                question = response.text.strip()
                logger.info("Question generated successfully using Gemini API")
                return question
            except Exception as e:
                logger.error(f"Gemini question generation failed: {str(e)}. Trying OpenAI.")

        # 2. Try OpenAI API if configured
        if self.openai_key:
            try:
                import openai
                prompt = self._build_prompt(role, resume_context, rag_context, difficulty, question_type, skills, domain, previous_questions, resume_data)
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert technical interviewer assessing candidates."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                question = response.choices[0].message['content'].strip()
                logger.info("Question generated successfully using OpenAI API")
                return question
            except Exception as e:
                logger.error(f"OpenAI question generation failed: {str(e)}. No fallback available.")

        # 3. NO LOCAL FALLBACK - Return error if both APIs fail
        logger.error("CRITICAL: Both Gemini and OpenAI APIs failed or are not configured. Local fallback is DISABLED to prevent hallucinations.")
        return "ERROR: Unable to generate question. Please ensure Gemini or OpenAI API keys are configured."

    def _is_allowed_topic(self, category: str, resume_data: dict, resume_context: List[str]) -> bool:
        """
        Check if a senior-level topic category is explicitly mentioned in candidate's resume/experience.
        Categories: "infrastructure", "distributed", "migration", "memory_leak", "mlops", "async_concurrency"
        
        This enforces the strict requirement: ONLY ask about topics actually mentioned in the resume.
        Do NOT introduce new concepts unless explicitly documented in candidate experience.
        """
        # Collect all resume text to search
        resume_texts = []
        if resume_data:
            if resume_data.get("raw_text"):
                resume_texts.append(resume_data.get("raw_text"))
            if resume_data.get("skills"):
                resume_texts.append(" ".join(resume_data.get("skills", [])))
            if resume_data.get("projects"):
                if isinstance(resume_data["projects"], dict):
                    proj_texts = []
                    for name, details in resume_data["projects"].items():
                        proj_texts.append(name)
                        if isinstance(details, dict) and details.get("skills"):
                            proj_texts.extend(details["skills"])
                    resume_texts.append(" ".join(proj_texts))
                else:
                    resume_texts.append(" ".join(resume_data.get("projects", [])))
        if resume_context:
            resume_texts.extend(resume_context)
            
        full_resume_text = " ".join(resume_texts).lower()
        
        # Define keywords for each category
        keywords_map = {
            "infrastructure": [
                "kubernetes", "k8s", "terraform", "ansible", "cloudformation", "infrastructure as code", 
                "iac", "prometheus", "grafana", "monitoring", "alerting", "production infrastructure", 
                "load balancer", "load-balancer", "autoscaling", "high availability", "failover", "multi-region"
            ],
            "distributed": [
                "distributed system", "distributed systems", "microservices", "microservice", "kafka", 
                "rabbitmq", "event-driven", "message queue", "message broker", "system design", 
                "scalability", "horizontal scaling", "zookeeper", "consul", "raft", "paxos", 
                "consistency model", "cap theorem", "saga pattern", "cqrs"
            ],
            "migration": [
                "migration", "migrate", "legacy", "enterprise", "monolith to microservices", "data migration"
            ],
            "memory_leak": [
                "memory leak", "memory leaks", "valgrind", "leak tracer", "heap dump", "heap profiling", 
                "memory profiling", "memory optimization", "garbage collection tuning"
            ],
            "mlops": [
                "mlops", "kubeflow", "mlflow", "sagemaker", "model deployment", "feature store", 
                "model monitoring", "model tracking", "dvc", "wandb", "weights & biases", 
                "model pipeline", "ci/cd for ml", "triton"
            ],
            "async_concurrency": [
                "async", "asyncio", "async/await", "concurrency", "concurrent", "threading", "multiprocessing",
                "parallel", "promise", "future", "callback", "event loop", "coroutine", "greenlet",
                "tokio", "gevent", "celery", "rq", "task queue", "job queue"
            ]
        }
        
        keywords = keywords_map.get(category, [])
        for kw in keywords:
            if kw in full_resume_text:
                return True
        return False

    def _sanitize_rag_context(self, rag_context: List[str], full_resume_words: set) -> List[str]:
        """
        Sanitize RAG context to remove any lines or sentences that mention technologies,
        tools, architectures, or concepts that are not present in the candidate's resume/skills.
        
        STRICT REQUIREMENT: Only allow concepts explicitly mentioned in the resume.
        Removes all references to:
        - Advanced backend architecture (microservices, distributed systems, message queues)
        - Infrastructure management (Kubernetes, Terraform, Ansible, monitoring tools)
        - Async/concurrency patterns (unless in resume)
        - Production scaling/failover patterns (unless in resume)
        - Advanced ML/MLOps tooling (unless in resume)
        """
        import re
        
        # A list of external tools/architectures/concepts to watch out for
        # These represent advanced concepts that should only appear if explicitly in resume
        known_keywords = {
            # Infrastructure
            "kubernetes", "k8s", "terraform", "ansible", "cloudformation", "prometheus", "grafana",
            "load balancer", "load-balancer", "autoscaling", "failover", "high availability",
            # Distributed/Microservices
            "microservices", "microservice", "kafka", "rabbitmq", "zookeeper", "consul", 
            "distributed system", "event-driven", "message queue", "message broker",
            # Advanced databases
            "elasticsearch", "dynamodb",
            # Cloud platforms
            "aws", "gcp", "azure",
            # ML/MLOps
            "mlflow", "kubeflow", "sagemaker", "triton",
            # Web servers
            "nginx", "apache",
            # Debugging/profiling (advanced)
            "valgrind", "profiler", "profiling", "memory leak", "heap dump",
            # Auth/API patterns
            "oauth", "jwt", "cors", "saga", "cqrs", "graphql", "grpc",
            # Caching
            "caching", "cache", "redis",
            # Databases
            "mongodb",
            # Async/Concurrency
            "async", "asyncio", "async/await", "concurrency", "concurrent", 
            "threading", "multiprocessing", "parallel execution", "coroutine", "event loop",
            # CI/CD
            "jenkins", "ci/cd",
            # Serverless
            "serverless", "lambda",
            # General advanced concepts
            "distributed", "migration", "legacy"
        }
        
        sanitized_chunks = []
        for chunk in rag_context:
            sanitized_lines = []
            for line in chunk.split('\n'):
                line_lower = line.lower()
                # Check if this line mentions any known technology/concept
                contains_external = False
                for kw in known_keywords:
                    # If the keyword is in the line, but NOT in the candidate's resume, we reject the line!
                    if kw in line_lower and kw not in full_resume_words:
                        contains_external = True
                        break
                if not contains_external:
                    sanitized_lines.append(line)
            if sanitized_lines:
                sanitized_chunks.append("\n".join(sanitized_lines))
        return sanitized_chunks

    def _build_prompt(
        self,
        role: str,
        resume_context: List[str],
        rag_context: List[str],
        difficulty: str,
        question_type: str,
        skills: List[str],
        domain: str,
        previous_questions: List[str] = None,
        resume_data: dict = None
    ) -> str:
        """Helper to format prompt for external LLM API based on strict student-friendly, direct guidelines
        
        STRICT REQUIREMENT: Questions must be grounded 85% in resume and only 15% in general role knowledge.
        No advanced concepts introduced unless explicitly in resume.
        """
        prev_qs_str = "\n".join([f"- {q}" for q in previous_questions]) if previous_questions else "None"
        
        # Structured details from resume_data
        resume_skills_str = "None"
        resume_projects_str = "None"
        experience_years = 0
        if resume_data:
            role_to_use = role or "Backend Engineer"
            role_keywords = ROLE_SKILLS_MAPPING.get(role_to_use, [])
            role_keywords_lower = {k.lower() for k in role_keywords}
            
            resume_skills = resume_data.get("skills") or []
            relevant_candidate_skills = []
            for skill in resume_skills:
                skill_lower = skill.lower()
                if skill_lower in role_keywords_lower or any(kw in skill_lower for kw in role_keywords_lower):
                    relevant_candidate_skills.append(skill)
            
            if not relevant_candidate_skills:
                relevant_candidate_skills = [k.title() for k in role_keywords[:4]] if role_keywords else ["Software Engineering"]
                
            resume_skills_str = ", ".join(relevant_candidate_skills) if relevant_candidate_skills else "None"
            resume_projects = resume_data.get("projects") or []
            if isinstance(resume_projects, dict):
                resume_projects_str = "\n".join([f"- {name}: {', '.join(details.get('skills', []))}" for name, details in resume_projects.items()])
            else:
                resume_projects_str = "\n".join([f"- {p}" for p in resume_projects]) if resume_projects else "None"
            experience_years = resume_data.get("experience_years", 0) or 0
            
            # Build relational knowledge graph representation
            kg_str = "None"
            if resume_data.get("knowledge_graph"):
                kg = resume_data["knowledge_graph"]
                lines = []
                if kg.get("projects"):
                    lines.append("Projects to Skills:")
                    for proj_name, details in kg["projects"].items():
                        skills_used = ", ".join(details.get("skills", []))
                        lines.append(f"  - Project '{proj_name}' uses: {skills_used if skills_used else 'None'}")
                if kg.get("experience"):
                    lines.append("Work Experience to Skills:")
                    for exp in kg["experience"]:
                        job_key = f"{exp.get('role')} at {exp.get('company')}"
                        skills_used = ", ".join(exp.get("skills", []))
                        lines.append(f"  - Job '{job_key}' applied: {skills_used if skills_used else 'None'}")
                kg_str = "\n".join(lines)
            else:
                kg_str = "None"
        
        # Build an explicit technology whitelist from the knowledge graph
        # This is the ONLY set of technologies the LLM is allowed to mention
        allowed_tech_set = set()
        allowed_tech_list = []
        if resume_data:
            # From structured skills
            for s in (resume_data.get("skills") or []):
                allowed_tech_set.add(s.lower())
                allowed_tech_list.append(s)
            # From KG projects
            kg = resume_data.get("knowledge_graph") or {}
            if kg.get("projects"):
                for proj_name, details in kg["projects"].items():
                    allowed_tech_set.add(proj_name.lower())
                    for s in details.get("skills", []):
                        allowed_tech_set.add(s.lower())
                        if s not in allowed_tech_list:
                            allowed_tech_list.append(s)
            # From KG experience
            if kg.get("experience"):
                for exp in kg["experience"]:
                    for s in exp.get("skills", []):
                        allowed_tech_set.add(s.lower())
                        if s not in allowed_tech_list:
                            allowed_tech_list.append(s)
        
        # Fallback: collect from raw resume text if no KG
        if not allowed_tech_set and resume_context:
            import re
            raw = " ".join(resume_context).lower()
            allowed_tech_set = set(re.findall(r'\b[a-zA-Z0-9_-]{2,30}\b', raw))
        
        # Augment with raw resume words for RAG sanitization
        resume_texts = []
        if resume_data:
            if resume_data.get("raw_text"):
                resume_texts.append(resume_data.get("raw_text"))
        if resume_context:
            resume_texts.extend(resume_context)
        import re
        full_resume_text_lower = " ".join(resume_texts).lower()
        full_resume_words = allowed_tech_set | set(re.findall(r'\b[a-zA-Z0-9_-]{2,30}\b', full_resume_text_lower))
        
        # Filter and sanitize RAG context using the strict whitelist
        sanitized_rag = self._sanitize_rag_context(rag_context, full_resume_words)
        
        # Format whitelist for prompt
        allowed_tech_str = ", ".join(sorted(set(allowed_tech_list))) if allowed_tech_list else "Only technologies mentioned in the resume"
        
        # Determine disallowed senior categories based on resume content
        # STRICT REQUIREMENT: Only allow topics explicitly mentioned in resume
        disallowed_topics = []
        if not self._is_allowed_topic("infrastructure", resume_data, resume_context):
            disallowed_topics.append("production infrastructure (e.g., Kubernetes, Terraform, Ansible, Prometheus/Grafana, cloud autoscaling/failover)")
        if not self._is_allowed_topic("distributed", resume_data, resume_context):
            disallowed_topics.append("distributed systems and microservices (e.g., microservices, Kafka/RabbitMQ, system design/scalability, CAP theorem, consensus protocols)")
        if not self._is_allowed_topic("migration", resume_data, resume_context):
            disallowed_topics.append("legacy system migration (e.g., monolith to microservices, enterprise data migration)")
        if not self._is_allowed_topic("memory_leak", resume_data, resume_context):
            disallowed_topics.append("memory leak debugging and profiling (e.g., Valgrind, heap dumps, memory optimization)")
        if not self._is_allowed_topic("mlops", resume_data, resume_context):
            disallowed_topics.append("advanced MLOps and model deployment (e.g., Kubeflow, MLflow, SageMaker, model deployment pipelines, feature stores)")
        if not self._is_allowed_topic("async_concurrency", resume_data, resume_context):
            disallowed_topics.append("async/concurrency patterns (e.g., asyncio, async/await, threading, multiprocessing, event loops, coroutines)")
            
        disallowed_instructions = ""
        if disallowed_topics:
            disallowed_instructions = "CRITICAL LIMITATION: The candidate's resume does NOT show experience with the following senior/advanced topics, so you MUST NOT ask questions about them:\n"
            for topic in disallowed_topics:
                disallowed_instructions += f"        - Do NOT ask about: {topic}\n"
            disallowed_instructions += "        Instead, focus on student-level project implementation, practical understanding, debugging basics, model usage, and real-world project experience appropriate for their profile.\n"
        else:
            disallowed_instructions = "Focus on practical understanding, debugging basics, model usage, and project experience appropriate for their profile.\n"

        return f"""
        Generate a single unique technical screening question for a candidate.
        
        ===== STRICT RESUME-ONLY REQUIREMENT =====
        Questions MUST ONLY discuss:
        - Technologies explicitly listed in the candidate's skills
        - Projects explicitly listed in the candidate's portfolio
        - Tools actually used in those specific projects
        - Experiences explicitly documented in work history
        
        Questions MUST NOT introduce:
        - Advanced backend architecture (microservices, distributed systems, message queues, event-driven patterns)
        - Production infrastructure management (Kubernetes, Terraform, Ansible, monitoring solutions)
        - Async/concurrency patterns (unless explicitly in resume: asyncio, threading, multiprocessing, etc.)
        - Production scaling/failover strategies (unless explicitly in resume)
        - Advanced MLOps tooling (Kubeflow, MLflow, SageMaker, feature stores - unless in resume)
        
        ===== CRITICAL RULES FOR QUESTION GENERATION =====
        
        CORE REQUIREMENTS:
        1. Generate ONE realistic interview question STRICTLY grounded in the candidate's actual resume.
        2. Compose the question with exactly an 85% focus on the candidate's actual resume (projects, experience, tools, skills, code implementation, and specific candidate details listed below) and a 15% focus on role knowledge (using the Job/Domain Knowledge Context only to frame, contextualize, or add industry flavor to the resume elements).
        3. ONLY ask about technologies, tools, projects, skills, or concepts explicitly mentioned in the resume.
        4. NEVER introduce unrelated technologies, architectures, frameworks, or concepts.
        5. NEVER mix technologies across unrelated projects.
        6. NEVER hallucinate tools, databases, APIs, async systems, microservices, distributed systems, or production infrastructure unless explicitly present in the resume.
        
        QUESTION TYPE & DIFFICULTY:
        7. Do NOT generate senior-level or enterprise-level questions.
        8. Questions must sound natural, practical, and human-like.
        9. Keep the difficulty beginner to intermediate level.
        10. Prioritize project-based and practical questions over theoretical ones.
        
        FOCUS AREAS (in priority order):
        11. Focus mainly on:
            - Projects and their implementation
            - Debugging and troubleshooting
            - Deployment basics
            - Model training (if applicable)
            - APIs actually used
            - Databases actually used
            - Real problems faced during development
        
        PROJECT-TECH VALIDATION RULE:
        12. Before generating the question, verify the technology is actually connected to the project in the resume.
            Example: TensorFlow + Crop Detection → VALID | TensorFlow + TalentScout → INVALID
            Example: SQLite + TalentScout → VALID | Microservices + NSS → INVALID
        
        SECTION FILTERING RULE:
        13. Use ONLY these resume sections:
            - Technical Skills
            - Internship
            - Projects
        14. IGNORE these sections:
            - Leadership
            - NSS
            - Extracurricular activities
            - Hobbies
        
        QUESTION QUALITY RULES:
        15. Avoid generic AI-generated wording
        16. Avoid phrases like:
            - "Based on your resume..."
            - "I notice from your background..."
            - "Looking at your project..."
            - "I see that you..."
        17. Keep questions concise and conversational
        18. Return ONLY the question text without explanations, labels, or preamble
        19. Do not treat extracurricular activities, volunteering, or leadership sections as technical software projects.
        20. {disallowed_instructions}
        
        Role:
        {role}

        Candidate Years of Experience:
        {experience_years} years

        Candidate's Actual Skills/Tools:
        {resume_skills_str}

        Candidate's Actual Projects:
        {resume_projects_str}

        Candidate Resume Relational Knowledge Graph (Connections between projects/jobs and technical skills):
        {kg_str}

        Candidate Skill Level:
        {difficulty}

        Resume Context:
        {chr(10).join(resume_context)[:1000]}

        Job/Domain Knowledge Context (RAG):
        {chr(10).join(sanitized_rag)[:1000]}

        Previously Asked Questions:
        {prev_qs_str}

        Question Type to Focus On:
        {question_type}
        """

    def _clean_project_name(self, proj: str) -> str:
        """Helper to extract clean project titles from resume project strings"""
        import re
        if not proj:
            return "your project"
        # Take the first line (the title line)
        title = proj.split('\n')[0].strip()
        # Split by '|' to remove GitHub links/tech stacks
        title = title.split('|')[0].strip()
        # Split by ' - ' or ' – ' (en-dash) to remove subtitles/dates
        title = re.split(r'\s+[\-\–\—]\s+', title)[0].strip()
        # Split by ' (' or ' [' to remove dates/tech stacks in parentheses
        title = re.split(r'\s+[\(\[]', title)[0].strip()
        # Remove trailing/leading punctuation
        title = title.rstrip(' :,-–—')
        if len(title) < 3:
            return "your project"
        return title[:60].strip()

    def _local_generate(
        self,
        role: str,
        resume_context: List[str],
        rag_context: List[str],
        difficulty: str,
        question_type: str,
        skills: List[str],
        domain: str,
        resume_data: dict = None
    ) -> str:
        """Local generation using heuristics to create a highly personalized, conversational, and direct question.
        
        STRICT REQUIREMENT: Questions are constrained to resume-mentioned technologies, projects, and tools only.
        All template selections are filtered based on whether topics are explicitly in the resume.
        """
        import re
        import random
        
        # 1. Parse/extract tools & concepts from resume context & resume_data
        resume_skills = []
        resume_projects = []
        
        if resume_data:
            resume_skills = resume_data.get("skills") or []
            resume_projects = resume_data.get("projects") or []
            
        # Collect full resume text to search for database/API exposure
        resume_texts = []
        if resume_data:
            if resume_data.get("raw_text"):
                resume_texts.append(resume_data.get("raw_text"))
            if resume_data.get("skills"):
                resume_texts.append(" ".join(resume_data.get("skills", [])))
            if resume_data.get("projects"):
                if isinstance(resume_data["projects"], dict):
                    proj_texts = []
                    for name, details in resume_data["projects"].items():
                        proj_texts.append(name)
                        if isinstance(details, dict) and details.get("skills"):
                            proj_texts.extend(details["skills"])
                    resume_texts.append(" ".join(proj_texts))
                else:
                    resume_texts.append(" ".join(resume_data.get("projects", [])))
        if resume_context:
            resume_texts.extend(resume_context)
            
        full_resume_text = " ".join(resume_texts).lower()
        
        has_database = any(kw in full_resume_text for kw in ["db", "database", "sql", "postgres", "mongo", "query", "sqlite", "mysql", "redis", "model"])
        has_api = any(kw in full_resume_text for kw in ["api", "endpoint", "route", "http", "rest", "request", "response", "controller", "view"])
        
        # Comprehensive list of standard tools
        common_tools = [
            "docker", "kubernetes", "postgres", "mysql", "redis", "mongodb", "sqlite",
            "react", "fastapi", "django", "flask", "pytorch", "tensorflow", "aws", "gcp",
            "git", "jenkins", "ansible", "terraform", "kafka", "rabbitmq"
        ]
        
        role_to_use = role or "Backend Engineer"
        role_keywords = ROLE_SKILLS_MAPPING.get(role_to_use, [])
        role_keywords_lower = {k.lower() for k in role_keywords}
        
        matched_tools = []
        # First include role-relevant skills from resume_skills if available
        for skill in resume_skills:
            skill_lower = skill.lower()
            if (skill_lower in role_keywords_lower or any(kw in skill_lower for kw in role_keywords_lower)) and skill not in matched_tools:
                matched_tools.append(skill)
                
        for tool in common_tools:
            tool_lower = tool.lower()
            if tool_lower in role_keywords_lower or any(kw in tool_lower for kw in role_keywords_lower):
                if re.search(r'\b' + re.escape(tool) + r'\b', full_resume_text):
                    tool_cap = tool.capitalize()
                    if tool_cap not in matched_tools:
                        matched_tools.append(tool_cap)
                
        # Fallback to role's core competency skills if the candidate has no role-relevant skills/tools matched
        if not matched_tools:
            matched_tools = [k.title() for k in role_keywords[:4]] if role_keywords else ["Software Engineering"]
            
        # Primary tool
        if skills and skills[0] != "relevant technologies":
            primary_tool = skills[0]
        else:
            primary_tool = matched_tools[0] if matched_tools else "relevant technologies"
        
        # Determine project name and allowed concepts using the relational knowledge graph if available
        project_name = "your project"
        allowed_concepts = []
        kg = resume_data.get("knowledge_graph") if resume_data else None
        
        if kg:
            # 1. Select a project that uses primary_tool
            candidate_projects = []
            if kg.get("projects"):
                for name, details in kg["projects"].items():
                    if any(primary_tool.lower() in s.lower() for s in details.get("skills", [])):
                        candidate_projects.append(name)
            if candidate_projects:
                project_name = self._clean_project_name(random.choice(candidate_projects))
            elif kg.get("projects"):
                project_name = self._clean_project_name(random.choice(list(kg["projects"].keys())))
                
            # 2. Collect skills that share a project or work experience with primary_tool
            shared_skills = []
            if kg.get("projects"):
                for name, details in kg["projects"].items():
                    proj_skills = details.get("skills", [])
                    if any(primary_tool.lower() in s.lower() for s in proj_skills):
                        shared_skills.extend(proj_skills)
            if kg.get("experience"):
                for exp in kg["experience"]:
                    exp_skills = exp.get("skills", [])
                    if any(primary_tool.lower() in s.lower() for s in exp_skills):
                        shared_skills.extend(exp_skills)
            
            # Deduplicate and filter concepts
            for s in shared_skills:
                if s.lower() != primary_tool.lower() and s not in allowed_concepts:
                    allowed_concepts.append(s)
        else:
            # Fallback if no knowledge graph exists (compatibility layer)
            if resume_projects:
                if isinstance(resume_projects, dict):
                    proj = random.choice(list(resume_projects.keys()))
                else:
                    proj = random.choice(resume_projects)
                project_name = self._clean_project_name(proj)
                
            resume_terms = []
            if resume_data:
                if resume_data.get("skills"):
                    resume_terms.extend(resume_data.get("skills"))
                if resume_data.get("projects"):
                    if isinstance(resume_data["projects"], dict):
                        for p in resume_data["projects"].keys():
                            clean_p = self._clean_project_name(p)
                            if clean_p and clean_p != "your project":
                                resume_terms.append(clean_p)
                    else:
                        for p in resume_data.get("projects"):
                            clean_p = self._clean_project_name(p)
                            if clean_p and clean_p != "your project":
                                resume_terms.append(clean_p)
            allowed_concepts = [t for t in resume_terms if t.lower() != primary_tool.lower()]
            
        if allowed_concepts:
            concept = random.choice(allowed_concepts)
        else:
            concept = "application logic"
                
        # 3. Check allowed topics based on resume data/context
        # STRICT: Only use topics if explicitly mentioned in resume
        allow_infra = self._is_allowed_topic("infrastructure", resume_data, resume_context)
        allow_distributed = self._is_allowed_topic("distributed", resume_data, resume_context)
        allow_migration = self._is_allowed_topic("migration", resume_data, resume_context)
        allow_memory_leak = self._is_allowed_topic("memory_leak", resume_data, resume_context)
        allow_mlops = self._is_allowed_topic("mlops", resume_data, resume_context)
        allow_async_concurrency = self._is_allowed_topic("async_concurrency", resume_data, resume_context)
        
        # 4. Focused Template Pools - BEGINNER/INTERMEDIATE ONLY
        
        project_templates = [
            (f"Walk me through how you set up and ran your project '{project_name}'. What were the main features you implemented using {primary_tool}?", None),
            (f"What were the most challenging parts of building '{project_name}' with {primary_tool}, and how did you resolve them?", None),
            (f"What tools or libraries did you use alongside {primary_tool} in '{project_name}' to help build the project?", None),
            (f"How did you test the functionality of '{project_name}' during development to make sure it worked as expected?", None),
            (f"If you needed to add a new feature to '{project_name}' (like user authentication or a new database model), how would you plan and implement it step-by-step?", None),
        ]
        
        debugging_templates = [
            (f"How do you use print statements, logging, or debugger tools to find and fix errors in a {primary_tool} application?", None),
            (f"If your application fails to compile or start due to a syntax error or a missing import/dependency, how do you locate and resolve it?", None),
        ]
        
        if has_api:
            debugging_templates.append((f"If a route or endpoint in your '{project_name}' project starts returning a 404 (Not Found) or 500 (Internal Server Error), what steps would you take to debug it?", None))
            debugging_templates.append((f"Imagine a user reports that a form submission in '{project_name}' isn't saving data. How would you verify where the failure occurs?", None))
            
        if has_database:
            debugging_templates.append((f"Suppose you get a database connection error when trying to start '{project_name}' locally. How would you troubleshoot this?", None))
        
        # Database Basics Templates
        database_templates = []
        if has_database:
            database_templates = [
                (f"How did you structure the database tables or data storage for your project '{project_name}'?", None),
                (f"Walk me through how you designed the database schema for '{project_name}'. What tables or collections did you create and why?", None),
                (f"If you notice that a specific database query in '{project_name}' is returning more data than needed, how would you modify it to only fetch relevant fields?", None),
                (f"How do you handle relationships or connections between different data entities in '{project_name}'?", None),
            ]
        
        # API Usage Templates
        api_templates = []
        if has_api:
            api_templates = [
                (f"Can you explain how data flows through a typical API endpoint built with {primary_tool}?", None),
                (f"Imagine you need to integrate a third-party API (like a weather service or payment gateway) into '{project_name}'. How would you design the integration?", None),
                (f"How do you ensure your API endpoints or views in '{project_name}' return clean, structured JSON responses to the frontend?", None),
                (f"Walk me through how you structured the API routes or endpoints in '{project_name}'. How did you organize them?", None),
            ]
        
        # Deployment & Docker Basics Templates
        deployment_templates = [
            (f"What has been your hands-on experience with managing secrets, configurations, and environment variables securely in your project '{project_name}'?", None),
            (f"Suppose you want to deploy your project '{project_name}' to a hosting service (like Render, Vercel, or Heroku) so others can use it. What steps would you follow?", None),
            (f"How do you manage external packages or requirements (like requirements.txt or package.json) for '{project_name}'?", None),
            (f"If you need to store and protect sensitive information like API keys or database passwords in '{project_name}', how would you handle that securely?", None),
        ]
        
        # Docker Basics Templates
        docker_templates = []
        if "docker" in full_resume_text.lower():
            docker_templates = [
                (f"Walk me through how you containerized your project '{project_name}' using Docker. What was in your Dockerfile?", None),
                (f"How do you handle environment variables and configuration in a Docker container for '{project_name}'?", None),
                (f"Describe the steps you took to build and run your Docker image for '{project_name}'. What challenges did you face?", None),
            ]
        
        # Streamlit Templates
        streamlit_templates = []
        if "streamlit" in full_resume_text.lower():
            streamlit_templates = [
                (f"How did you structure your Streamlit app in '{project_name}'? What components or pages did you create?", None),
                (f"Walk me through how you used Streamlit widgets in '{project_name}' to collect user input and display results?", None),
                (f"How do you manage session state or caching in your Streamlit application for '{project_name}'?", None),
            ]
        
        # Gemini API Templates
        gemini_templates = []
        if "gemini" in full_resume_text.lower():
            gemini_templates = [
                (f"How did you integrate the Gemini API into '{project_name}'? Walk me through your implementation?", None),
                (f"What parameters or prompts did you use when calling the Gemini API in '{project_name}'?", None),
                (f"How do you handle errors or rate limits when using the Gemini API in '{project_name}'?", None),
            ]
        
        # Firebase Templates
        firebase_templates = []
        if "firebase" in full_resume_text.lower():
            firebase_templates = [
                (f"How did you use Firebase in '{project_name}'? Which Firebase services did you integrate?", None),
                (f"Walk me through how you set up Firebase Authentication in '{project_name}'. How does the login flow work?", None),
                (f"How do you structure and query data in Firestore for '{project_name}'?", None),
                (f"Describe how you used Firebase to store and retrieve user data in '{project_name}'?", None),
            ]
        
        # GitHub Actions Templates
        github_actions_templates = []
        if "github actions" in full_resume_text.lower() or "github action" in full_resume_text.lower():
            github_actions_templates = [
                (f"How did you set up GitHub Actions for '{project_name}'? What workflows did you create?", None),
                (f"Walk me through a GitHub Actions workflow you created for '{project_name}'. What does it do?", None),
                (f"How do you use GitHub Actions to automate testing or deployment for '{project_name}'?", None),
            ]
        
        # Model Training & Feature Engineering Templates
        model_templates = []
        if "tensorflow" in full_resume_text.lower() or "pytorch" in full_resume_text.lower() or "scikit" in full_resume_text.lower():
            model_templates = [
                (f"Walk me through how you prepared and processed the data for your model in '{project_name}'?", None),
                (f"What features did you engineer or extract from the raw data in '{project_name}'? How did you select them?", None),
                (f"How did you split your data (training, validation, test) for '{project_name}' and why did you choose that split?", None),
                (f"Describe the model architecture you chose for '{project_name}'. Why did you pick that approach?", None),
                (f"How did you evaluate your model's performance in '{project_name}'? What metrics did you use?", None),
                (f"Walk me through how you trained your machine learning model in '{project_name}'. How long did it take and how did you monitor progress?", None),
            ]
        
        # Combine all templates
        all_templates = project_templates + debugging_templates + deployment_templates + database_templates + api_templates + docker_templates + streamlit_templates + gemini_templates + firebase_templates + github_actions_templates + model_templates
        
        # Only use beginner-to-intermediate templates (those marked as None)
        # All advanced templates have been removed
        allowed_categories = {None}
            
        # Select from combined pool based on question type
        raw_pool = []
        q_type_lower = question_type.lower()
        if q_type_lower == "project-based":
            raw_pool = project_templates
        elif q_type_lower == "debugging":
            raw_pool = debugging_templates
        elif q_type_lower == "deployment":
            raw_pool = deployment_templates
        elif q_type_lower == "database":
            raw_pool = database_templates if database_templates else project_templates
        elif q_type_lower == "api":
            raw_pool = api_templates if api_templates else project_templates
        else:
            # Default: use all combined templates
            raw_pool = all_templates
            
        # Filter pool
        pool = [t[0] for t in raw_pool if t[1] in allowed_categories]
        
        # Fallback if filtered pool is empty, use all available templates
        if not pool:
            pool = [t[0] for t in all_templates if t[1] in allowed_categories]
        
        # Final fallback if still empty
        if not pool:
            pool = [t[0] for t in all_templates]
            
        q = random.choice(pool)
        
        # Ensure question ends cleanly with a single question mark
        q = q.strip()
        if not q.endswith('?'):
            q += '?'
            
        return q
