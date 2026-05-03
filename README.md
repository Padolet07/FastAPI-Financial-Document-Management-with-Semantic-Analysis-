# Financial Document Management System with Semantic Search

Production-oriented FastAPI backend for uploading financial documents, enforcing JWT/RBAC access, extracting text, indexing chunks, and searching with a RAG-style retrieval pipeline.

## Features

- JWT authentication: `POST /auth/register`, `POST /auth/login`
- RBAC roles: Admin, Analyst, Auditor, Client
- Document APIs: upload, list, detail, update metadata, delete, metadata search
- RAG APIs: index document, remove embeddings, semantic search, document context
- LangChain text splitting, reranking over top 20 candidates, top 5 default response
- SQLite + SQL vector fallback for local development
- PostgreSQL + Qdrant support through Docker Compose
- Swagger UI at `/docs`

## Setup

1. Create and activate a virtual environment. Python 3.11 or 3.12 is recommended for the ML stack; the base API also supports newer Python versions when compatible wheels are available.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create environment file.

```bash
copy .env.example .env
```

4. Seed roles and an admin user.

```bash
python -m scripts.seed
```

5. Run the API.

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`.

Default admin credentials after seeding:

```text
admin@example.com
Admin@12345
```

## Docker

```bash
copy .env.example .env
docker compose up --build
```

This starts FastAPI, PostgreSQL, and Qdrant. Run the seed command inside the API container:

```bash
docker compose exec api python -m scripts.seed
```

## Sample API Flow

Login:

```bash
curl -X POST http://localhost:8000/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"Admin@12345\"}"
```

Upload sample document:

```bash
curl -X POST http://localhost:8000/documents/upload ^
  -H "Authorization: Bearer <TOKEN>" ^
  -F "title=ACME Q4 Report" ^
  -F "company_name=ACME Capital" ^
  -F "document_type=report" ^
  -F "file=@sample_data/acme_q4_report.txt"
```

Index document:

```bash
curl -X POST http://localhost:8000/rag/index-document ^
  -H "Authorization: Bearer <TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"document_id\":1}"
```

Semantic search:

```bash
curl -X POST http://localhost:8000/rag/search ^
  -H "Authorization: Bearer <TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"financial risk related to high debt ratio\",\"limit\":5}"
```

## Configuration Notes

For local demos, `EMBEDDING_PROVIDER=hash` avoids external downloads and API keys. For better retrieval quality use:

```env
EMBEDDING_PROVIDER=sentence-transformers
VECTOR_BACKEND=qdrant
```

Then install the optional ML dependencies:

```bash
pip install -r requirements-ml.txt
```

For OpenAI embeddings:

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=...
```

Use a long random `JWT_SECRET_KEY` in production.
