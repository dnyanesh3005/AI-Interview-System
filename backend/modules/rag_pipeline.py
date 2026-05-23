"""
Hybrid Agentic RAG Pipeline
Implements FAISS vector search + BM25 keyword retrieval
with per-session resume indexing and 85%/15% retrieval ratio.
"""

import logging
import pickle
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    raise ImportError("Run: pip install sentence-transformers scikit-learn")

try:
    import faiss
except ImportError:
    raise ImportError("Run: pip install faiss-cpu")

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    raise ImportError("Run: pip install rank-bm25")

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────────────
RESUME_WEIGHT = 0.85   # 85% resume context
ROLE_WEIGHT   = 0.15   # 15% role/domain knowledge
RRF_K         = 60     # Reciprocal Rank Fusion constant


class RAGPipeline:
    """
    Hybrid Agentic RAG Pipeline.

    Two layers:
    1. Role knowledge base — FAISS + BM25 (loaded once per role)
    2. Resume index — FAISS + BM25 (built per interview session from structured resume)

    Retrieval merges both layers: 85% resume context + 15% role knowledge.
    """

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model)

        # Role knowledge: role → {chunks, faiss_index, bm25}
        self._role_kb: Dict[str, Dict] = {}

        # Resume index: session_id → {chunks, faiss_index, bm25}
        self._resume_idx: Dict[str, Dict] = {}

        logger.info(f"RAGPipeline initialised with model: {embedding_model}")

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def initialize(self):
        """Called on startup — no-op, indexes are built lazily."""
        logger.info("RAG Pipeline ready (lazy indexing)")

    def load_knowledge_base(self, role: str) -> bool:
        """Load and index role-specific domain knowledge."""
        if role in self._role_kb:
            return True
        try:
            sources = {
                "Backend Engineer":    self._kb_backend(),
                "AI/ML Engineer":      self._kb_aiml(),
                "Full Stack Engineer": self._kb_fullstack(),
                "Data Scientist":      self._kb_datascience(),
                "DevOps Engineer":     self._kb_devops(),
                "Frontend Developer":  self._kb_frontend(),
                "Data Analyst":        self._kb_data_analyst(),
            }
            if role not in sources:
                logger.warning(f"Unknown role: {role}")
                return False

            chunks = self._chunk_text(sources[role])
            index, embeddings = self._build_faiss(chunks)
            bm25 = self._build_bm25(chunks)

            self._role_kb[role] = {
                "chunks": chunks,
                "faiss": index,
                "embeddings": embeddings,
                "bm25": bm25,
            }
            logger.info(f"Role KB loaded for '{role}': {len(chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error loading KB for {role}: {e}")
            return False

    def build_resume_index(self, session_id: str, resume_data: Dict) -> bool:
        """
        Build a per-session FAISS + BM25 index from the candidate's structured resume.
        Must be called after parsing, before question generation.
        """
        try:
            chunks = self._resume_to_chunks(resume_data)
            if not chunks:
                logger.warning(f"No resume chunks for session {session_id}")
                return False

            index, embeddings = self._build_faiss(chunks)
            bm25 = self._build_bm25(chunks)

            self._resume_idx[session_id] = {
                "chunks": chunks,
                "faiss": index,
                "embeddings": embeddings,
                "bm25": bm25,
            }
            logger.info(f"Resume index built for session {session_id}: {len(chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error building resume index for {session_id}: {e}")
            return False

    def retrieve_hybrid(
        self,
        session_id: str,
        role: str,
        query: str,
        top_k: int = 6,
    ) -> List[Dict]:
        """
        Hybrid retrieval: 85% resume context + 15% role knowledge.

        Returns list of dicts:
          {"content": str, "score": float, "source": "resume"|"role"}
        """
        resume_results = self._retrieve_from_index(
            self._resume_idx.get(session_id),
            query,
            top_k=max(1, round(top_k * RESUME_WEIGHT * 2)),
        )
        role_results = self._retrieve_from_index(
            self._role_kb.get(role),
            query,
            top_k=max(1, round(top_k * ROLE_WEIGHT * 2)),
        )

        # Tag sources
        for r in resume_results:
            r["source"] = "resume"
        for r in role_results:
            r["source"] = "role"

        # Merge with budget enforcement
        n_resume = round(top_k * RESUME_WEIGHT)
        n_role   = top_k - n_resume

        merged = resume_results[:n_resume] + role_results[:n_role]
        merged.sort(key=lambda x: x["score"], reverse=True)

        logger.debug(
            f"Hybrid retrieval: {len(merged)} chunks "
            f"({len(resume_results[:n_resume])} resume + {len(role_results[:n_role])} role)"
        )
        return merged

    # Backward-compat wrapper
    def retrieve_context(self, role: str, query: str, top_k: int = 5) -> List[Dict]:
        """Legacy method — retrieves from role KB only."""
        return self._retrieve_from_index(
            self._role_kb.get(role), query, top_k=top_k
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Internal Retrieval
    # ──────────────────────────────────────────────────────────────────────────

    def _retrieve_from_index(
        self,
        store: Optional[Dict],
        query: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """Retrieve from a single {faiss, bm25, chunks} store using RRF fusion."""
        if not store:
            return []
        try:
            chunks = store["chunks"]
            n = len(chunks)
            if n == 0:
                return []

            # ── FAISS retrieval ──────────────────────────────────────────────
            q_emb = self.embedding_model.encode([query], convert_to_numpy=True)
            q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-10)
            faiss_k = min(top_k * 2, n)
            distances, faiss_ids = store["faiss"].search(q_emb.astype("float32"), faiss_k)
            # faiss inner-product gives cosine scores (index is normalised)
            faiss_ranks = {int(idx): rank for rank, idx in enumerate(faiss_ids[0]) if idx >= 0}

            # ── BM25 retrieval ───────────────────────────────────────────────
            tokens = query.lower().split()
            bm25_scores = store["bm25"].get_scores(tokens)
            bm25_order = np.argsort(bm25_scores)[::-1]
            bm25_ranks = {int(idx): rank for rank, idx in enumerate(bm25_order)}

            # ── Reciprocal Rank Fusion ────────────────────────────────────────
            rrf_scores: Dict[int, float] = {}
            for idx in range(n):
                r_faiss = faiss_ranks.get(idx, n)
                r_bm25  = bm25_ranks.get(idx, n)
                rrf_scores[idx] = (1 / (RRF_K + r_faiss)) + (1 / (RRF_K + r_bm25))

            top_indices = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]

            # ── Map cosine distances back for score ──────────────────────────
            cos_map = {}
            for dist, idx in zip(distances[0], faiss_ids[0]):
                if idx >= 0:
                    cos_map[int(idx)] = float(dist)

            results = []
            for rank, idx in enumerate(top_indices):
                results.append({
                    "content": chunks[idx],
                    "score": rrf_scores[idx],
                    "cosine_score": cos_map.get(idx, 0.0),
                    "rank": rank + 1,
                })
            return results

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────────
    # Index Building
    # ──────────────────────────────────────────────────────────────────────────

    def _build_faiss(self, chunks: List[str]) -> Tuple[faiss.Index, np.ndarray]:
        """Build a normalised inner-product FAISS index (equivalent to cosine sim)."""
        embeddings = self.embedding_model.encode(chunks, convert_to_numpy=True)
        embeddings = embeddings / (
            np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10
        )
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings.astype("float32"))
        return index, embeddings

    def _build_bm25(self, chunks: List[str]) -> BM25Okapi:
        tokenised = [chunk.lower().split() for chunk in chunks]
        return BM25Okapi(tokenised)

    # ──────────────────────────────────────────────────────────────────────────
    # Chunking
    # ──────────────────────────────────────────────────────────────────────────

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Sentence-aware chunking for role knowledge."""
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        chunks, current = [], ""
        for sent in sentences:
            candidate = (current + ". " + sent).lstrip(". ")
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current + ".")
                current = sent
        if current:
            chunks.append(current + ".")
        return chunks

    def _resume_to_chunks(self, resume_data: Dict) -> List[str]:
        """
        Convert structured resume into semantically meaningful chunks.
        Each chunk represents one logical unit (a project, a skill group, an experience).
        """
        chunks = []

        # Skills chunk
        skills = resume_data.get("skills") or []
        tools  = resume_data.get("tools")  or []
        if skills:
            chunks.append("Technical skills: " + ", ".join(skills))
        if tools:
            chunks.append("Tools and libraries: " + ", ".join(tools))

        # Certifications
        certs = resume_data.get("certifications") or []
        if certs:
            chunks.append("Certifications: " + "; ".join(certs))

        # Projects — one chunk per project (rich context)
        projects_raw = resume_data.get("projects") or {}
        if isinstance(projects_raw, dict):
            for name, details in projects_raw.items():
                if not isinstance(details, dict):
                    chunks.append(f"Project: {name}")
                    continue
                proj_skills = ", ".join(details.get("skills") or [])
                proj_tools  = ", ".join(details.get("tools")  or [])
                desc        = details.get("description") or ""
                outcome     = details.get("outcome") or ""
                parts = [f"Project '{name}'"]
                if desc:
                    parts.append(f"Description: {desc}")
                if proj_skills:
                    parts.append(f"Skills used: {proj_skills}")
                if proj_tools:
                    parts.append(f"Tools used: {proj_tools}")
                if outcome:
                    parts.append(f"Outcome: {outcome}")
                chunks.append(". ".join(parts))
        elif isinstance(projects_raw, list):
            for p in projects_raw:
                if isinstance(p, dict):
                    name = p.get("name") or p.get("title") or "Project"
                    proj_skills = ", ".join(p.get("skills") or [])
                    proj_tools  = ", ".join(p.get("tools")  or [])
                    desc        = p.get("description") or ""
                    outcome     = p.get("outcome") or ""
                    parts = [f"Project '{name}'"]
                    if desc:
                        parts.append(f"Description: {desc}")
                    if proj_skills:
                        parts.append(f"Skills used: {proj_skills}")
                    if proj_tools:
                        parts.append(f"Tools used: {proj_tools}")
                    if outcome:
                        parts.append(f"Outcome: {outcome}")
                    chunks.append(". ".join(parts))
                elif p:
                    chunks.append(f"Project: {p}")

        # Work experience — one chunk per role
        for exp in (resume_data.get("experience") or []):
            if not isinstance(exp, dict):
                continue
            exp_skills = ", ".join(exp.get("skills") or [])
            parts = [
                f"Work experience: {exp.get('role', '')} at {exp.get('company', '')}",
                f"Duration: {exp.get('duration', 'N/A')}",
            ]
            if exp_skills:
                parts.append(f"Skills applied: {exp_skills}")
            chunks.append(". ".join(parts))

        # Education
        education = resume_data.get("education") or []
        if education:
            chunks.append("Education: " + "; ".join(education))

        return [c for c in chunks if len(c) > 10]

    # ──────────────────────────────────────────────────────────────────────────
    # Role Knowledge Bases
    # ──────────────────────────────────────────────────────────────────────────

    def _kb_backend(self) -> str:
        return """
        Backend Engineering: server-side development, API design, and system architecture.
        Core concepts: REST API design with HTTP methods, status codes, authentication, versioning.
        Database design: SQL normalization, indexing, ACID transactions, query optimization.
        Authentication: JWT tokens, OAuth2 flows, session management, password hashing.
        Performance: caching strategies with Redis, rate limiting, connection pooling.
        Frameworks: FastAPI, Django, Flask for Python; Spring Boot for Java; Express for Node.js.
        Design patterns: MVC, Repository, Factory, Observer, Singleton.
        Databases: PostgreSQL, MySQL, SQLite, MongoDB, Redis.
        Testing: unit tests with pytest, integration tests, API testing with Postman.
        Deployment basics: environment variables, requirements files, basic Docker containers.
        Version control: Git workflows, branching strategies, pull requests.
        Error handling: try/except, logging, HTTP error responses, retry logic.
        API documentation: Swagger/OpenAPI, writing clear endpoint descriptions.
        """

    def _kb_aiml(self) -> str:
        return """
        AI and Machine Learning: building intelligent systems with data.
        Core ML concepts: supervised learning, unsupervised learning, classification, regression.
        Model training: splitting data into train/validation/test sets, overfitting, underfitting.
        Algorithms: linear regression, logistic regression, decision trees, random forests, gradient boosting.
        Deep learning basics: neural network layers, activation functions, loss functions, optimizers.
        NLP basics: tokenization, text preprocessing, embeddings, sentiment analysis.
        Computer vision basics: image preprocessing, CNNs, classification, object detection.
        Feature engineering: missing values, encoding categorical variables, normalization, scaling.
        Model evaluation: accuracy, precision, recall, F1-score, confusion matrix, ROC-AUC.
        Libraries: scikit-learn, TensorFlow, PyTorch, Keras, Pandas, NumPy, OpenCV.
        APIs: Gemini API, OpenAI API, HuggingFace transformers.
        Deployment basics: saving models with pickle/joblib, loading for inference, REST API wrapping.
        Data handling: loading CSVs, handling imbalanced datasets, data augmentation basics.
        """

    def _kb_fullstack(self) -> str:
        return """
        Full Stack Engineering: combining frontend and backend development.
        Frontend: React component architecture, state management, hooks, routing with React Router.
        CSS: Flexbox, Grid, responsive design, media queries, animations.
        JavaScript: ES6+, async/await, fetch API, DOM manipulation, event handling.
        Backend: REST API design, database integration, authentication with JWT.
        State management: useState, useEffect, Context API, Redux basics.
        Build tools: npm/yarn, Vite, Webpack, environment configuration.
        Database integration: connecting frontend to backend APIs, handling loading/error states.
        Deployment: serving static builds, environment variables, basic CI/CD.
        Testing: Jest for unit tests, React Testing Library for component tests.
        Version control: Git, GitHub, pull request workflows.
        """

    def _kb_datascience(self) -> str:
        return """
        Data Science: extracting insights from data using statistics and machine learning.
        Statistics: mean, median, variance, standard deviation, probability distributions.
        Hypothesis testing: p-values, t-tests, chi-square tests, A/B testing basics.
        Data analysis: exploratory data analysis, data cleaning, handling missing values.
        Visualization: matplotlib, seaborn, plotly, choosing right chart types.
        Python tools: Pandas for data manipulation, NumPy for numerical computing.
        SQL: SELECT, JOIN, GROUP BY, window functions, subqueries.
        Machine learning: model selection, cross-validation, hyperparameter tuning.
        Big data basics: Spark overview, partitioning concepts.
        BI tools: Tableau, Power BI, building dashboards, KPI tracking.
        Data pipelines: ETL processes, data quality checks, scheduling.
        Communication: presenting findings, executive summaries, storytelling with data.
        """

    def _kb_devops(self) -> str:
        return """
        DevOps Engineering: automating software delivery and infrastructure management.
        Docker: writing Dockerfiles, building images, docker-compose for local development.
        CI/CD: GitHub Actions workflows, automated testing pipelines, build triggers.
        Linux basics: shell scripting, file permissions, process management, cron jobs.
        Cloud basics: deploying to Render, Heroku, AWS EC2, GCP, environment configuration.
        Version control: Git branching, tags, releases, code review workflows.
        Infrastructure: environment management, secrets management, .env files.
        Monitoring basics: logging, application health checks, uptime monitoring.
        Deployment strategies: blue-green, rolling updates, rollback procedures.
        Networking basics: DNS, HTTP/HTTPS, ports, load balancers at a conceptual level.
        Security: API key management, HTTPS, basic firewall rules, vulnerability scanning.
        """

    def _kb_frontend(self) -> str:
        return """
        Frontend Development: building user-facing web interfaces.
        HTML5: semantic elements, accessibility, ARIA attributes, SEO meta tags.
        CSS: Flexbox layout, CSS Grid, custom properties, animations, transitions, media queries.
        JavaScript: closures, promises, async/await, event loop, fetch API, DOM manipulation.
        React: functional components, hooks (useState, useEffect, useContext), props, state.
        Routing: React Router, dynamic routes, navigation guards, URL parameters.
        State management: Context API, Redux basics, local vs global state decisions.
        Performance: lazy loading, code splitting, image optimization, memoization.
        Testing: Jest, React Testing Library, snapshot testing.
        Build tools: Vite, Webpack, npm scripts, environment variables.
        Responsive design: mobile-first approach, breakpoints, viewport units.
        Accessibility: keyboard navigation, focus management, screen reader compatibility.
        """

    def _kb_data_analyst(self) -> str:
        return """
        Data Analysis: collecting, cleaning, and interpreting data for business decisions.
        SQL: complex JOINs, CTEs, window functions (ROW_NUMBER, RANK, LAG/LEAD), subqueries.
        Data cleaning: handling nulls, duplicates, data type conversions, outlier detection.
        Statistical analysis: descriptive statistics, correlation analysis, trend identification.
        Visualization: choosing bar vs line vs scatter charts, dashboard design principles.
        Spreadsheets: pivot tables, VLOOKUP, INDEX/MATCH, conditional formatting.
        Python for analysis: Pandas groupby, merge, pivot_table, matplotlib/seaborn plots.
        BI tools: Tableau or Power BI — connecting data sources, building dashboards.
        Business metrics: CAC, LTV, churn rate, conversion funnel, MRR, DAU/MAU.
        A/B testing: defining control/treatment, statistical significance, interpreting results.
        Communication: writing data stories, executive summaries, making recommendations.
        Reporting: automated reports, scheduled queries, alerting on KPI thresholds.
        """