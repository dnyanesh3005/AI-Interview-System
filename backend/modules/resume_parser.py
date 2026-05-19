"""
Resume Parser Module
Extracts structured information from resume files
"""

import PyPDF2
import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ResumeParser:
    """Parse and extract information from resumes"""
    
    def __init__(self):
        self.skill_keywords = {
            "Backend": ["python", "java", "node.js", "fastapi", "django", "spring", "docker", "kubernetes"],
            "AI/ML": ["python", "tensorflow", "pytorch", "scikit-learn", "nlp", "deep learning", "machine learning"],
            "Frontend": ["react", "vue", "angular", "javascript", "typescript", "html", "css"],
            "DevOps": ["docker", "kubernetes", "jenkins", "aws", "gcp", "terraform", "ci/cd"],
            "Data Science": ["python", "pandas", "numpy", "sql", "hadoop", "spark", "data visualization"]
        }
        
        self.domain_keywords = {
            "Finance": ["fintech", "trading", "banking", "payment", "risk management"],
            "Healthcare": ["healthcare", "medical", "hospital", "pharma", "telemedicine"],
            "E-Commerce": ["ecommerce", "retail", "marketplace", "shopping", "logistics"],
            "SaaS": ["saas", "subscription", "cloud", "api", "microservices"],
            "Data": ["analytics", "big data", "data engineering", "data warehouse", "bi"]
        }
    
    def parse(self, file_content: bytes, filename: str) -> Dict:
        """
        Parse resume file and extract structured data
        
        Args:
            file_content: Binary content of resume file
            filename: Name of the file
            
        Returns:
            Dictionary with extracted resume information
        """
        try:
            if filename.endswith('.pdf'):
                text = self._extract_pdf_text(file_content)
            elif filename.endswith('.txt'):
                text = file_content.decode('utf-8')
            else:
                text = file_content.decode('utf-8')
            
            # Extract information
            resume_data = {
                "candidate_name": self._extract_name(text),
                "email": self._extract_email(text),
                "phone": self._extract_phone(text),
                "skills": self._extract_skills(text),
                "experience_years": self._extract_experience_years(text),
                "domain": self._extract_domain(text),
                "education": self._extract_education(text),
                "projects": self._extract_projects(text),
                "raw_text": text
            }
            
            logger.info(f"Resume parsed successfully for {resume_data['candidate_name']}")
            return resume_data
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise Exception(f"Resume parsing failed: {str(e)}")
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            import io
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise
    
    def _extract_name(self, text: str) -> str:
        """Extract candidate name from resume text"""
        lines = text.split('\n')
        # Typically name is in first few lines
        for line in lines[:5]:
            if line.strip() and len(line.split()) <= 4:
                return line.strip()
        return "Unknown"
    
    def _extract_email(self, text: str) -> str:
        """Extract email from resume"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else "N/A"
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume"""
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else "N/A"
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume"""
        text_lower = text.lower()
        found_skills = set()
        
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.add(skill.capitalize())
        
        return list(found_skills)
    
    def _extract_experience_years(self, text: str) -> int:
        """Extract years of experience"""
        # Look for patterns like "X years", "X+ years"
        pattern = r'(\d+)\s*\+?\s*years'
        matches = re.findall(pattern, text.lower())
        
        if matches:
            return max(int(m) for m in matches)
        return 0
    
    def _extract_domain(self, text: str) -> str:
        """Extract primary domain/industry from resume"""
        text_lower = text.lower()
        scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[domain] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "General"
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education information"""
        education = []
        
        # Look for common degree patterns
        degree_pattern = r'(B\.?S\.?|B\.?Tech\.?|M\.?S\.?|M\.?Tech\.?|Ph\.?D\.?|MBA)\s+in\s+([^,\n]+)'
        matches = re.findall(degree_pattern, text, re.IGNORECASE)
        
        for degree, field in matches:
            education.append(f"{degree} in {field}")
        
        return education if education else ["Not specified"]
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract project descriptions"""
        # Look for project section
        project_section = re.search(
            r'(?:projects?|portfolio|personal\s+projects?)(.*?)(?:skills|education|experience|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if project_section:
            projects_text = project_section.group(1)
            # Split by common delimiters
            projects = [p.strip() for p in re.split(r'[-•*]\s*', projects_text) if p.strip()]
            return projects[:3]  # Return top 3 projects
        
        return []