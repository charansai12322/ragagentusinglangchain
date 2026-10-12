# Backend — PDF Intelligence RAG Engine & API

Production-ready, session-isolated FastAPI backend powering document parsing, FastEmbed CPU embeddings, in-memory retrieval, and Groq-powered question-answering with page citations.

---

## Technical Specifications

- **Python Version:** 3.12 (Verified: Python 3.12.10)
- **Framework:** FastAPI 0.143+ / Uvicorn
- **LLM Provider:** Groq (`langchain-groq`, `ChatGroq`)
- **Default LLM Model:** `openai/gpt-oss-120b` (Configurable via `GROQ_MODEL_NAME`)
- **Embeddings:** FastEmbed (`BAAI/bge-small-en-v1.5`, 384 dimensions, CPU ONNX runtime ~67MB)
- **Vector Index:** Session-isolated in-memory cosine similarity matrix (zero disk leakage, sub-millisecond retrieval)
- **PDF Parser:** `pypdf` with strict signature validation, page-count bounding, and scanned-document detection

---

## Installation & Environment Setup

1. **Install production dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install development/test dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Configure Environment:**
   A local `.env` has already been initialized from `.env.example`.
   Edit `backend/.env` and replace the placeholder with your Groq API key:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   GROQ_MODEL_NAME=openai/gpt-oss-120b
   ```

---

## Running the Server

Start the Uvicorn ASGI server with hot-reload:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The interactive OpenAPI documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Running Tests & Linting

1. **Execute full automated test suite (22 unit & integration tests):**
   ```bash
   python -m pytest -v
   ```

2. **Run Ruff linter and formatter checks:**
   ```bash
   python -m ruff check backend
   python -m ruff format backend --check
   ```

---

## Live Smoke Test (Groq Integration)

Once a valid `GROQ_API_KEY` is added to `backend/.env`, run a live smoke test script:

```bash
python -c "
import asyncio
from backend.app.services.chat_service import ChatService

async def main():
    svc = ChatService()
    ans = await svc.generate([{'role': 'user', 'content': 'Explain the attention mechanism in one sentence.'}])
    print('Groq Answer:', ans)

asyncio.run(main())
"
```

---

## API Endpoint Contracts

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health, model info, active sessions | `200` |
| `POST` | `/api/documents/upload` | Multipart PDF upload with size/page validation | `201`, `400`, `413`, `422` |
| `POST` | `/api/documents/url` | Secure remote PDF download with SSRF guard | `201`, `400`, `422`, `504` |
| `GET` | `/api/documents/{id}/status` | Check session state, page count, and history | `200`, `404` |
| `DELETE` | `/api/documents/{id}` | Evict session and free in-memory vector index | `200`, `404` |
| `POST` | `/api/documents/{id}/chat` | Grounded QA with page-number citations | `200`, `404`, `429`, `502` |

---

## Architectural & Memory Controls

- **Single Process In-Memory Architecture:** Designed for single-worker Render instances (`--workers 1`). Vectors are held in process memory and automatically garbage-collected upon session deletion or TTL expiration.
- **TTL Eviction:** Sessions idle for $>60$ minutes are automatically purged by the background janitor loop.
- **Capacity Bounds:** Capped at 20 concurrent active sessions (`MAX_SESSIONS=20`) to prevent memory exhaustion on 512MB RAM cloud tiers.
- **Rate-Limit Resilience:** Groq 429 errors are trapped and mapped to HTTP 429 with clean retry guidance, preventing unhandled server crashes.
