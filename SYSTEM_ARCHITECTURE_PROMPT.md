# AIScraperAgent — End-to-End System Architecture Specification

## Overview
**AIScraperAgent** is an automated procurement monitoring, vector search, and AI-driven relevance ranking system for public procurement notices, tenders, and calls for proposals (AMI / AO). 

The system implements a dual-path data ingestion pipeline (Static HTML + Dynamic API interception), unifies heterogeneous structures into standardized JSON schemas, cleans and normalizes data in Pandas, indexes opportunities into a vector database (Qdrant), executes semantic similarity search, and persists the top-ranked opportunities into a local SQLite database (`CERT.db`) exposed via a clean web interface and CLI.

---

## 1. System Architecture Flowchart

```text
                        ┌──────────────┐
                        │     DATA     │
                        └──────┬───────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       ┌───────────────┐               ┌───────────────┐
       │   HTML Path   │               │   API Path    │
       │ (Static Sites)│               │(Dynamic Sites)│
       └───────┬───────┘               └───────┬───────┘
               │                               │
               ▼                               ▼
       ┌───────────────┐               ┌───────────────┐
       │     Text      │               │  LLM Mapper   │
       │  Extraction   │               │ & Normalizer  │
       └───────┬───────┘               └───────┬───────┘
               │                               │
               ▼                               │
       ┌───────────────┐                       │
       │   NLP (LLM)   │                       │
       │ Entity Parser │                       │
       └───────┬───────┘                       │
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
                       ┌───────────────┐
                       │     JSON      │
                       │ Standardized  │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │      DF       │
                       │(Pandas Batch) │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │    Filter     │
                       │ Clean Columns │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │ Normalisation │
                       │ Dates/Hashes  │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │   Embedding   │
                       │ (Sentence-TF) │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │Semantic Search│
                       │ Qdrant Vector │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │    SQLite     │
                       │(Top 5 Saved)  │
                       └───────────────┘
```

---

## 2. Step-by-Step Pipeline Walkthrough

### Step 1: Dual-Source Data Ingestion (`Data`)
The pipeline ingests public tenders and expressions of interest from two distinct web architectures:
1. **Static HTML Portals** (e.g., INTT / Government portals): Server-side rendered HTML listings.
2. **Dynamic API Portals** (e.g., World Bank Procurement): Single Page Applications (SPA) that fetch notices asynchronously via background JSON XHR/fetch requests.

---

### Step 2: Branch Processing

#### Path A: Static HTML Processing (`HTML` $\rightarrow$ `Text` $\rightarrow$ `NLP (LLM)`)
- **Module**: `static_sc.py`, `scraper/html_extractor.py`, `LLM/nlp_extractor.py`
- **Mechanism**:
  1. `BeautifulSoup` crawls and extracts the raw HTML links and tender announcement text blocks.
  2. The raw unstructured text is passed to an LLM-based entity extractor (`meta/llama-3.1-8b-instruct` via NVIDIA API / OpenAI-compatible endpoint).
  3. The LLM extracts key fields: `title`, `description`, `submission_deadline`, `organization`, `budget`, and `sector`.

#### Path B: Dynamic API Interception (`API` $\rightarrow$ `LLM Mapper & Normalisation`)
- **Module**: `sc2.py`, `scraper/json_parser.py`, `LLM/nlp_mapper.py`
- **Mechanism**:
  1. Headless **Playwright Chromium** navigates to the dynamic portal and listens to network responses in real-time (`page.on('response', handle_response)`).
  2. Automatically identifies the best API endpoint delivering tender data by scoring candidate JSON payloads against procurement keywords.
  3. The `LLM Mapper` inspects arbitrary JSON payloads and maps disparate external key names (e.g., `procurement_title`, `tender_desc`, `closing_date`) to our standardized schema.

---

### Step 3: Unified Structured Output (`JSON`)
Both static text extraction and dynamic API payload transformation converge into a single, standardized dictionary format:
```json
{
  "title": "Digital Public Procurement Interoperability & API Gateway",
  "description": "Consulting services to implement interoperability APIs...",
  "organization": "High Authority of Public Procurement",
  "country": "Tunisia",
  "sector": "Information and Communications Technologies",
  "submission_deadline": "2026-09-22",
  "url": "https://example.com/notice/123"
}
```

---

### Step 4: Pandas DataFrame Conversion (`DF`)
- **Module**: `main.py`, `pandas`
- Standardized records from all sources are loaded into a unified Pandas DataFrame (`pd.DataFrame`).
- Allows scalable vectorized batch operations, deduplication, and tabular processing.

---

### Step 5: Column & Quality Filtering (`Filter`)
- **Module**: `scraper/filtering.py`
- Discards irrelevant columns, empty notices, and invalid structures.
- Ensures all records contain non-empty title and description fields before persistence.

---

### Step 6: Normalization & Deduplication (`Normalisation`)
- **Module**: `scraper/hashing.py`, `dateutil.parser`
- **Date Standardization**: Parses varied date formats into ISO standard datetime strings.
- **Deduplication**: Generates deterministic SHA-256 hash IDs based on `(title + deadline + description)` to prevent inserting duplicate notices into the database.

---

### Step 7: Dense Vector Embeddings (`Embedding`)
- **Module**: `scraper/embedding.py`, `qdrant_embedding.py`
- **Model**: `SentenceTransformer('all-MiniLM-L6-v2')` (384-dimensional dense vectors).
- Combines notice title and description, computes normalized vector representations, and upserts points into **Qdrant Vector Database**.

---

### Step 8: AI Semantic Similarity Search (`Semantic Search`)
- **Module**: `qdrant_embedding.py` (`retrive_spesific_data`)
- Executes semantic vector cosine similarity search against a specialized strategic domain query:
  > *"Find procurement opportunities relevant to an IT engineering company involving AI, machine learning, software development, cybersecurity, cloud computing, data science, automation, digital platforms, or technology consulting."*
- Computes cosine similarity scores ($0.0$ to $1.0$) for all indexed notices.

---

### Step 9: SQLite Persistence & Web Exploitation (`SQLite`)
- **Module**: `database/models.py`, `database/storage.py`, `CERT.db`, `app.py`, `main.py`
- The top 5 highest-scoring opportunity matches are persisted directly into the SQLite database (`similarity_results` and `opportunities` tables).
- A clean **FastAPI web server** (`app.py`) serves the minimalist dashboard where users can view the top 5 ranked opportunities and trigger the complete pipeline on demand (`POST /api/run-pipeline` and `GET /api/results/top5`).

---

## 3. Technology Stack Summary

| Layer | Technologies Used | Purpose |
| :--- | :--- | :--- |
| **Ingestion** | Playwright, BeautifulSoup4, Requests | Dynamic XHR interception & static HTML crawling |
| **NLP & LLM** | `meta/llama-3.1-8b-instruct`, NVIDIA API | Text entity extraction & schema field mapping |
| **Data Processing**| Pandas, Python-dateutil, Hashlib | Batch DataFrame filtering, cleaning, deduplication |
| **Vector Engine** | SentenceTransformers (`all-MiniLM-L6-v2`), Qdrant | 384-dim dense embeddings & semantic search |
| **Database** | SQLite (`CERT.db`), SQLAlchemy ORM | Structured relational persistence of top 5 results |
| **Backend / API** | FastAPI, Uvicorn | REST endpoints & pipeline execution bridge |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript | Clean, minimalist data table interface |
