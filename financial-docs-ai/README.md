# Financial Docs AI 
**Enterprise-Grade Agentic RAG for SEC Financial Disclosures**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/) [![React + Vite](https://img.shields.io/badge/frontend-React%20%7C%20Vite-61dafb.svg)](https://vitejs.dev/) [![Postgres + pgvector](https://img.shields.io/badge/database-pgvector-336791.svg)](https://github.com/pgvector/pgvector) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`financial-docs-ai` is a high-throughput, retrieval-augmented generation (RAG) system engineered to extract actionable intelligence from dense financial corpora. By fusing semantic vector search with deterministic full-text filtering, the system allows analysts to query complex SEC filings in natural language while strictly enforcing factual grounding through verifiable, document-backed citations.


---

## Generative AI & Retrieval Architecture

The pipeline is built for low-latency inference and high-fidelity retrieval, utilizing a decoupled architecture to separate the ingestion engine from the chat inference layer.

* **Hybrid Search Retrieval:** Combines dense vector similarity (`pgvector` via OpenAI embeddings) with sparse keyword matching (Postgres Full-Text) to ensure both contextual nuance and exact-match accuracy for financial tickers and metrics.
* **Semantic Chunking:** Documents are parsed and chunked using a sliding window algorithm to preserve financial context and tabular data across paragraph boundaries.
* **Hallucination Mitigation:** The LLM prompt heavily utilizes system instructions to restrict generation strictly to the retrieved context. All assertions are appended with deterministic citations linking back to the raw source chunk.
* **Streaming Inference:** Utilizes Server-Sent Events (SSE) to stream LLM tokens to the React client, ensuring perceived latency remains minimal during complex query reasoning.

---

## Technology Stack

| Layer | Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Backend / API** | Python 3.12 + FastAPI | Async event loop optimized for IO-bound LLM and database operations. |
| **Frontend SPA** | React + Vite + TypeScript | Strict type safety, modular component isolation, and rapid HMR. |
| **Database** | Supabase (PostgreSQL) | Unified storage for user state, raw documents, and relational data. |
| **Vector Engine** | `pgvector` + Postgres FTS | Fuses semantic vector embeddings with traditional full-text search. |
| **Generative AI** | OpenAI API | GPT models for chat inference; OpenAI embedding models for vectorization. |
| **Migrations** | SQLAlchemy + Alembic | Version-controlled, deterministic database schema management. |
| **Authentication** | Supabase Auth | Secure, stateless JWT-based session management. |

---

## Repository Layout

```text
financial-docs-ai/
├── AGENTS.md           # LLM agent coding conventions and stack constraints
├── README.md           # System documentation
├── data/               # Local corpus storage + EDGAR ingestion scripts
├── docs/               # Architecture diagrams, design docs, setup guides
├── backend/            # FastAPI service (Inference & Retrieval API)
└── frontend/           # React SPA (Client Interface)

## Local Environment Provisioning

### Prerequisites & Toolchain

| Dependency | Version | Purpose | Installation |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **uv** | Latest | Fast Python dependency resolution | [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| **Node.js** | 20+ | Frontend runtime | [nodejs.org](https://nodejs.org/) |
| **pnpm** | Latest | Deterministic package management | `corepack enable && corepack prepare pnpm@latest --activate` |

*Note: You must provision a Supabase project and obtain an OpenAI API key before initializing the services. Reference [docs/guides/supabase-setup.md](docs/guides/supabase-setup.md) for database bootstrapping.*

### 1. Backend Service Initialization

The backend service handles the API gateway, vector database connections, and LLM orchestration.

```bash
cd backend
cp .env.example .env   # Configure SUPABASE_URL and OPENAI_API_KEY
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

API Gateway: http://localhost:8000

2. Frontend Service Initialization
The client is a standalone React SPA communicating with the backend via REST and SSE.

cd frontend
cp .env.example .env   # Configure VITE_API_BASE_URL
pnpm install
pnpm dev

Client Interface: http://localhost:5173

3. Data Ingestion & Seeding (Optional)
To test the Generative AI capabilities, you must populate the vector database with embedded chunks. The ingestion script connects to the SEC EDGAR database, downloads raw filings, chunks the text, and writes the semantic embeddings to Postgres.

uv run data/download.py
cd backend && uv run python ingest/run.py

Note: Edit the USER_AGENT string in data/download.py prior to execution to comply with SEC rate-limiting and contact requirements.

Testing & Telemetry
Continuous integration checks enforce strict type boundaries and functional test coverage across the backend logic.

cd backend
uv run pytest -m "not integration"
