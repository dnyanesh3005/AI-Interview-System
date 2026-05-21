"""
RAG (Retrieval-Augmented Generation) Pipeline
Implements knowledge ingestion, embedding, and retrieval
"""

import os
import logging
from typing import List, Dict, Tuple
import pickle
import json

# Vector database and embedding imports
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
except ImportError:
    raise ImportError("Required packages not installed. Run: pip install sentence-transformers scikit-learn numpy")

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline
    Handles knowledge ingestion, chunking, embedding, and retrieval
    """
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG pipeline
        
        Args:
            embedding_model: HuggingFace model for embeddings
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.knowledge_bases = {}  # Store loaded KBs
        self.embeddings_store = {}  # Store embeddings
        self.chunks_store = {}  # Store text chunks
        self.kb_status = {}
        
        logger.info(f"RAG Pipeline initialized with model: {embedding_model}")
    
    def load_knowledge_base(self, role: str) -> bool:
        """
        Load and process role-specific knowledge base
        
        Args:
            role: Job role (e.g., 'Backend Engineer', 'AI/ML Engineer')
            
        Returns:
            bool: Success status
        """
        try:
            # Role-specific knowledge sources
            knowledge_sources = {
                "Backend Engineer": self._get_backend_knowledge(),
                "AI/ML Engineer": self._get_aiml_knowledge(),
                "Full Stack Engineer": self._get_fullstack_knowledge(),
                "Data Scientist": self._get_datascience_knowledge(),
                "DevOps Engineer": self._get_devops_knowledge(),
                "Frontend Developer": self._get_frontend_knowledge(),
                "Data Analyst": self._get_data_analyst_knowledge(),
            }
            
            if role not in knowledge_sources:
                logger.warning(f"Unknown role: {role}")
                return False
            
            # Get knowledge content
            knowledge_content = knowledge_sources[role]
            
            # Process knowledge base
            chunks = self._chunk_knowledge(knowledge_content, role)
            embeddings = self._generate_embeddings(chunks)
            
            # Store processed knowledge
            self.knowledge_bases[role] = knowledge_content
            self.chunks_store[role] = chunks
            self.embeddings_store[role] = embeddings
            self.kb_status[role] = True
            
            logger.info(f"Knowledge base loaded for {role}: {len(chunks)} chunks created")
            return True
            
        except Exception as e:
            logger.error(f"Error loading knowledge base for {role}: {str(e)}")
            return False
    
    def retrieve_context(self, role: str, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant context from knowledge base
        
        Args:
            role: Job role
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant context chunks with similarity scores
        """
        try:
            if role not in self.embeddings_store:
                logger.warning(f"Knowledge base not loaded for role: {role}")
                return []
            
            # Embed query
            query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)
            
            # Compute similarities
            embeddings = self.embeddings_store[role]
            chunks = self.chunks_store[role]
            
            similarities = cosine_similarity([query_embedding], embeddings)[0]
            
            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = [
                {
                    "content": chunks[idx],
                    "similarity_score": float(similarities[idx]),
                    "rank": i + 1
                }
                for i, idx in enumerate(top_indices)
                if similarities[idx] > 0.3  # Minimum similarity threshold
            ]
            
            logger.info(f"Retrieved {len(results)} relevant chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}")
            return []
    
    def _chunk_knowledge(self, content: str, role: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Split knowledge content into chunks
        
        Args:
            content: Full knowledge content
            role: Job role
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
            
        Returns:
            List of content chunks
        """
        chunks = []
        sentences = content.split('.')
        
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            test_chunk = current_chunk + ". " + sentence if current_chunk else sentence
            
            if len(test_chunk) <= chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk + ".")
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk + ".")
        
        logger.info(f"Created {len(chunks)} chunks for {role}")
        return chunks
    
    def _generate_embeddings(self, chunks: List[str]) -> np.ndarray:
        """
        Generate embeddings for knowledge chunks
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Numpy array of embeddings
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_model.encode(chunks, convert_to_numpy=True)
        return embeddings
    
    # ============ Knowledge Base Sources ============
    # These contain curated domain knowledge for each role
    
    def _get_backend_knowledge(self) -> str:
        """Backend Engineering domain knowledge"""
        return """
        Backend Engineering encompasses server-side application development, API design, and system architecture.
        
        Core Concepts:
        1. REST API Design: Design principles, HTTP methods, status codes, request/response handling.
        2. Database Design: SQL, NoSQL, indexing, normalization, ACID properties, transactions.
        3. System Design: Scalability, load balancing, caching, microservices, message queues.
        4. Authentication & Security: JWT, OAuth, encryption, SQL injection prevention, CORS.
        5. Performance Optimization: Query optimization, caching strategies, rate limiting, async programming.
        6. Deployment: Docker, Kubernetes, CI/CD pipelines, monitoring, logging.
        
        Languages & Frameworks: Python (Django, FastAPI, Flask), Java (Spring), Node.js (Express), Go, Rust.
        
        Design Patterns: MVC, Repository Pattern, Factory Pattern, Observer Pattern, Singleton, Strategy.
        
        Database Technologies: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, DynamoDB.
        
        Key Skills: 
        - Building scalable REST APIs
        - Database optimization and design
        - Implementing authentication and authorization
        - Understanding distributed systems
        - Performance profiling and optimization
        - Writing testable, maintainable code
        
        Interview Focus Areas:
        - System design problems (designing a URL shortener, social media feed, etc.)
        - API design decisions and trade-offs
        - Database schema design and optimization
        - Handling concurrent requests and race conditions
        - Caching strategies and when to use them
        - Error handling and retry logic
        """
    
    def _get_aiml_knowledge(self) -> str:
        """AI/ML Engineering domain knowledge"""
        return """
        Artificial Intelligence and Machine Learning involves building intelligent systems using data.
        
        Core Concepts:
        1. Machine Learning Fundamentals: Supervised learning, unsupervised learning, reinforcement learning.
        2. Deep Learning: Neural networks, CNNs, RNNs, Transformers, attention mechanisms.
        3. Natural Language Processing: Text preprocessing, embeddings, language models, fine-tuning.
        4. Computer Vision: Image classification, object detection, segmentation, GANs.
        5. Feature Engineering: Selection, transformation, encoding, dimensionality reduction.
        6. Model Evaluation: Metrics (accuracy, precision, recall, F1), cross-validation, hyperparameter tuning.
        7. Deployment: Model serving, inference optimization, A/B testing, monitoring model drift.
        
        Languages & Frameworks: Python (TensorFlow, PyTorch, Scikit-learn), Java (Deeplearning4j), Scala (Spark MLlib).
        
        Key Algorithms:
        - Regression: Linear, Ridge, Lasso, Elastic Net
        - Classification: Logistic Regression, SVM, Decision Trees, Random Forest, Gradient Boosting
        - Clustering: K-means, Hierarchical, DBSCAN
        - Deep Learning: CNN, RNN, LSTM, GRU, Transformers
        
        Interview Focus Areas:
        - Understanding when to use which algorithm
        - Feature engineering and selection
        - Handling imbalanced datasets
        - Model interpretation and explainability
        - Handling overfitting and underfitting
        - End-to-end ML pipeline design
        - Optimization techniques and regularization
        """
    
    def _get_fullstack_knowledge(self) -> str:
        """Full Stack Engineering domain knowledge"""
        return """
        Full Stack Engineering combines frontend and backend development skills.
        
        Frontend Stack:
        - React, Vue.js, Angular for UI development
        - State management: Redux, Vuex, Context API
        - Styling: CSS, SASS, Tailwind, Material UI
        - Build tools: Webpack, Vite, Parcel
        - Testing: Jest, React Testing Library, Cypress
        
        Backend Stack:
        - Server frameworks: Node.js, Python, Java, Go
        - RESTful API design and GraphQL
        - Database design and optimization
        - Authentication and authorization
        - Caching and performance optimization
        
        DevOps & Deployment:
        - Docker containerization
        - CI/CD pipelines
        - Cloud platforms: AWS, GCP, Azure
        - Monitoring and logging
        - Infrastructure as Code
        
        Key Skills:
        - Understanding full application lifecycle
        - Cross-stack debugging
        - Performance optimization across layers
        - Security throughout the stack
        - Testing both frontend and backend
        """
    
    def _get_datascience_knowledge(self) -> str:
        """Data Science domain knowledge"""
        return """
        Data Science combines statistics, programming, and domain expertise to extract insights from data.
        
        Core Concepts:
        1. Statistics: Probability, distributions, hypothesis testing, A/B testing, confidence intervals.
        2. Data Analysis: Exploratory data analysis, data visualization, statistical inference.
        3. Machine Learning: Supervised and unsupervised learning, model selection, validation.
        4. Big Data: Distributed computing, Apache Spark, Hadoop, data warehousing.
        5. Data Pipeline: ETL processes, data quality, data governance, data versioning.
        
        Tools & Technologies:
        - Programming: Python, R, SQL
        - Libraries: Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn
        - Big Data: Spark, Hadoop, Hive
        - Databases: PostgreSQL, MongoDB, Hive, Redshift
        - Visualization: Tableau, Power BI, D3.js
        
        Key Skills:
        - Data cleaning and preprocessing
        - Exploratory data analysis
        - Feature engineering
        - Statistical testing
        - Building predictive models
        - Communicating insights to stakeholders
        - SQL and database querying
        """
    
    def _get_devops_knowledge(self) -> str:
        """DevOps Engineering domain knowledge"""
        return """
        DevOps Engineering focuses on automating, deploying, and maintaining applications.
        
        Core Concepts:
        1. Infrastructure as Code: Terraform, CloudFormation, Ansible
        2. Containerization: Docker, containerd, image optimization
        3. Orchestration: Kubernetes, Docker Swarm, ECS
        4. CI/CD: GitHub Actions, GitLab CI, Jenkins, CircleCI
        5. Monitoring & Logging: Prometheus, Grafana, ELK Stack, DataDog
        6. Cloud Platforms: AWS, GCP, Azure services and best practices
        
        Key Technologies:
        - Docker and container best practices
        - Kubernetes architecture and operations
        - Terraform for infrastructure provisioning
        - Monitoring and alerting systems
        - Log aggregation and analysis
        - Secrets management
        
        Key Skills:
        - Automating deployment processes
        - Managing cloud infrastructure
        - Implementing monitoring and alerting
        - Troubleshooting infrastructure issues
        - Security and compliance
        - Disaster recovery and backup strategies
        """
    
    def _get_frontend_knowledge(self) -> str:
        """Frontend Developer domain knowledge"""
        return """
        Frontend Development focuses on the user-facing part of web applications, emphasizing user interface (UI), user experience (UX), and web performance.
        
        Core Concepts:
        1. HTML5 & Semantic Web: Proper DOM structure, accessibility (WCAG, ARIA attributes), SEO practices.
        2. Modern CSS: Flexbox, Grid, CSS Variables, responsive web design, CSS-in-JS, CSS modules, animations, and transitions.
        3. JavaScript ES6+: Closures, prototype inheritance, asynchronous programming (Promises, async/await), event loop, DOM manipulation.
        4. Modern SPA Frameworks (e.g., React, Vue, Angular): Component-based architecture, state management (Redux, Zustand, Context API), hooks, virtual DOM, lifecycle methods, routing.
        5. Build Tools & Bundlers: Vite, Webpack, Babel, Turbopack, npm/yarn/pnpm.
        6. Performance Optimization: Lazy loading, code splitting, image optimization, caching strategies, Core Web Vitals (LCP, FID, CLS).
        7. Testing: Unit testing (Jest, Vitest), component testing (React Testing Library), end-to-end testing (Cypress, Playwright).
        8. Security: Cross-Site Scripting (XSS) prevention, Content Security Policy (CSP), secure storage (cookies vs localStorage).
        
        Interview Focus Areas:
        - Component state management and render optimizations.
        - Performance profiling and fixing slow renders/re-renders.
        - Developing highly responsive and interactive layouts.
        - Asynchronous data fetching, status overlays, and error boundaries.
        - Accessibility guidelines and testing frameworks.
        """

    def _get_data_analyst_knowledge(self) -> str:
        """Data Analyst domain knowledge"""
        return """
        Data Analysis involves collecting, cleaning, processing, and analyzing data to discover insights and inform business decisions.
        
        Core Concepts:
        1. Data Querying & Wrangling: SQL (joins, subqueries, CTEs, window functions), data cleaning, handling missing values, filtering.
        2. Statistical Analysis: Mean, median, mode, standard deviation, correlation vs causation, probability distributions, hypothesis testing.
        3. Data Visualization: Best practices for charting, dashboard design, choosing correct chart types (bar, line, scatter, cohort analysis).
        4. Reporting & Dashboards: Designing business-intelligence reports using BI tools, automating reporting.
        5. Spreadsheet Proficiency: Excel or Google Sheets (pivot tables, VLOOKUP, INDEX/MATCH, complex formulas).
        6. Key Business Metrics: Customer Acquisition Cost (CAC), Lifetime Value (LTV), Monthly Recurring Revenue (MRR), Churn Rate, ROI, conversion funnels.
        
        Languages & Tools:
        - SQL (PostgreSQL, MySQL, BigQuery, Snowflake)
        - Python (Pandas, NumPy, Matplotlib, Seaborn) or R
        - BI Tools (Tableau, Power BI, Looker Studio)
        - Spreadsheets (Excel, Google Sheets)
        
        Key Skills:
        - Translating complex data queries into actionable business recommendations.
        - Generating concise reports and automated pipelines.
        - Conducting root-cause analyses for business trends (e.g., sudden drop in active users).
        - Defining and tracking KPIs for different organizational departments.
        
        Interview Focus Areas:
        - Writing efficient SQL queries to aggregate and transform transactional data.
        - Analyzing and presenting findings from A/B tests or user cohort datasets.
        - Designing key dashboards to track product engagement metrics.
        - Explaining data limitations and statistical significance in layman's terms.
        """
    
    def initialize(self):
        """Initialize RAG system"""
        logger.info("RAG Pipeline initialized")