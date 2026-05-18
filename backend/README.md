# AI-Powered Candidate Screening System - Backend

## Overview

This is a FastAPI-based backend for an intelligent candidate screening system that uses Retrieval-Augmented Generation (RAG) to dynamically generate technical interview questions based on:
- Candidate's resume
- Target job role
- Role-specific knowledge base
- Candidate's previous answers

## System Architecture

### Core Components

1. **Resume Parser Module** (`modules/resume_parser.py`)
   - Extracts structured data from resume files (PDF, TXT, DOCX)
   - Identifies: skills, experience, domain, education
   - Uses regex patterns and domain knowledge for extraction

2. **RAG Pipeline** (`modules/rag_pipeline.py`)
   - Knowledge ingestion and chunking
   - Embedding generation using sentence-transformers
   - Semantic similarity-based retrieval
   - Support for 5 different roles with specialized knowledge bases

3. **Question Generator** (`modules/question_generator.py`)
   - Generates contextual questions using RAG context
   - Adapts difficulty based on candidate experience
   - Varies question types (Conceptual, Applied, Challenge, Experience)
   - Ensures questions are relevant and grounded in knowledge base

4. **Session Manager** (`modules/session_manager.py`)
   - Manages interview session lifecycle
   - Tracks question/answer progress
   - Maintains session state in memory and database

5. **Database Module** (`modules/database.py`)
   - SQLite-based persistence
   - Stores sessions, questions, answers, metadata
   - Query building for analytics

## Setup Instructions

### Prerequisites

- Python 3.9+
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the server**
   ```bash
   python main.py
   # or
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Resume Management
- `POST /api/upload-resume` - Upload and parse resume
- Returns: Extracted resume data with skills, experience, domain

### Role Management
- `POST /api/select-role` - Select target role and load knowledge base
- Supports: Backend Engineer, AI/ML Engineer, Full Stack Engineer, Data Scientist, DevOps Engineer

### Interview Flow
- `POST /api/start-interview` - Initialize interview session
- `POST /api/submit-answer` - Submit answer and get next question
- `GET /api/interview-summary/{session_id}` - Get complete interview summary
- `GET /api/sessions` - List all interview sessions

### Session Management
- Each session has a unique UUID
- Questions and answers are stored with metadata
- Session status tracking (in_progress, completed)

## RAG Pipeline Design

### Knowledge Ingestion

1. **Document Collection**
   - Role-specific curated knowledge (hardcoded in rag_pipeline.py)
   - Can be extended to load from external sources

2. **Chunking Strategy**
   - Semantic sentence-based chunking
   - Chunk size: 500 characters
   - Overlap: 100 characters for context preservation

3. **Embedding Generation**
   - Model: sentence-transformers (all-MiniLM-L6-v2)
   - Efficient, lightweight, good for semantic search
   - ~400-600 embeddings per role

### Retrieval Mechanism

1. **Query Construction**
   - Builds context-aware queries from resume and role
   - Different queries for each question progression
   - Adapts based on previous answer quality

2. **Similarity Search**
   - Cosine similarity matching
   - Top-k retrieval (default: 5)
   - Minimum similarity threshold: 0.3

3. **Context Filtering**
   - Only includes relevant chunks above threshold
   - Ranked by similarity score

### Question Generation

1. **Template Selection**
   - Different templates for: Conceptual, Applied, Challenge, Experience
   - Adapts based on difficulty and question type

2. **Template Filling**
   - Uses extracted topics from context
   - Substitutes placeholders with actual domain knowledge
   - Ensures coherence and relevance

3. **Question Adaptation**
   - Difficulty progression (Basic → Intermediate → Advanced)
   - Based on candidate experience years
   - Adjusts with question progression

## Data Persistence

### Database Schema

```
Sessions
├── id (UUID)
├── candidate_name
├── role
├── email
├── phone
├── resume_data (JSON)
├── created_at
├── updated_at
└── status

Questions
├── id
├── session_id (FK)
├── question_number
├── question_text
├── question_type
├── difficulty
├── category
├── context_used (JSON)
└── created_at

Answers
├── id
├── session_id (FK)
├── question_id (FK)
├── answer_text
├── duration_seconds
├── quality_score
└── created_at

Interview Metadata
├── session_id (FK)
├── total_duration
├── average_answer_length
├── overall_performance
└── notes
```

## Extension Points

### Adding New Roles

To add a new role, extend `RAGPipeline.load_knowledge_base()`:

```python
def _get_new_role_knowledge(self) -> str:
    """Role-specific knowledge content"""
    return """
    Core Concepts:
    1. Topic 1
    2. Topic 2
    ...
    """
```

### Integrating with LLM

Current implementation uses templates. To integrate with an LLM (GPT-4, Claude, etc.):

```python
# In question_generator.py
def _create_question(self, ...):
    # Instead of template filling, call LLM
    response = llm.generate(
        prompt=f"Generate a {difficulty} {question_type} question about {topic}",
        context=retrieved_context
    )
    return response
```

### Custom Scoring

Implement answer evaluation:

```python
# Add to question_generator.py
def score_answer(self, question, answer, context) -> float:
    # Use LLM or similarity matching
    # Return 0-1 score
    pass
```

## Performance Considerations

1. **Embedding Generation**: ~1-2 seconds for 1000 chunks (one-time)
2. **Retrieval**: ~100ms per query (cosine similarity)
3. **Database**: SQLite suitable for <10K sessions, consider PostgreSQL for production

## Troubleshooting

### Common Issues

1. **Embedding model not found**
   ```
   Solution: pip install sentence-transformers
   Models are auto-downloaded on first use
   ```

2. **Resume parsing errors**
   ```
   Solution: Ensure file is valid PDF/TXT/DOCX
   Check file encoding for text files
   ```

3. **CORS errors in frontend**
   ```
   Solution: Update CORS_ORIGINS in .env
   Ensure frontend runs on allowed origin
   ```

## Performance Optimizations

- [ ] Cache embeddings for knowledge bases
- [ ] Implement async question generation
- [ ] Add request caching with Redis
- [ ] Batch process multiple resumes
- [ ] Implement database connection pooling

## Security Considerations

- [ ] Add API authentication/authorization
- [ ] Validate and sanitize all inputs
- [ ] Implement rate limiting
- [ ] Encrypt sensitive data in database
- [ ] Add HTTPS in production

## Future Enhancements

1. **LLM Integration**
   - Use GPT-4/Claude for more natural question generation
   - Real-time answer evaluation

2. **Advanced Analytics**
   - Answer quality scoring
   - Performance trends
   - Skill gap identification

3. **Multi-language Support**
   - Question and answer translation
   - Multilingual resume parsing

4. **Video Interview Support**
   - Record candidate responses
   - Speech-to-text conversion
   - Body language analysis

5. **Collaborative Features**
   - Interviewer notes
   - Shared session summaries
   - Comparison with other candidates

## License

This project is part of the PG-AGI internship program.