# ARC-RAIDERS WikiBot

A wiki-style chatbot for ARC Raiders powered by a local Ollama LLM, DuckDuckGo web search, and a ChromaDB RAG cache. Python/FastAPI backend + React frontend, with MLflow observability and Docker Compose.

**Interview study sheet:** [docs/INTERVIEW.md](docs/INTERVIEW.md)

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Ollama** running locally with two models pulled:
  ```bash
  ollama pull llama3.1:8b
  ollama pull nomic-embed-text
  ollama serve   # if not already running
  ```

## Quick Start (local development)

### Windows (PowerShell)

```powershell
# 1. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python server.py              # API on http://localhost:8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                   # UI on http://localhost:5173

# 3. MLflow (optional, new terminal — for traces/eval)
cd backend
.\.venv\Scripts\Activate.ps1
python run_mlflow_ui.py       # UI on http://localhost:5000
```

### macOS / Linux

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python server.py

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev

# 3. MLflow (optional)
cd backend && source .venv/bin/activate
python run_mlflow_ui.py
# or: ./run_mlflow_ui.sh
```

Open http://localhost:5173 and start asking about ARC Raiders.

## Quick Start (Docker)

```bash
docker compose up --build

# First time only: pull the Ollama models into the container
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
```

- **Chat UI**: http://localhost:8001
- **MLflow dashboard**: http://localhost:5001

Ollama runs on **CPU by default** so Compose works without an NVIDIA GPU. To enable GPU, uncomment the `deploy:` block under `ollama` in `docker-compose.yml`.

To stop: `docker compose down` (add `-v` to also wipe data volumes).

## Configuration

All config lives in `backend/.env` (copy from `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.1:8b` | Chat model |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model for RAG cache |
| `CHROMA_DATA_DIR` | `data/chroma` | ChromaDB storage path |
| `CACHE_SIMILARITY_THRESHOLD` | `0.75` | Min similarity to use cached answers |
| `VERBOSE_TOOL_CALLS` | `0` | Set to `1` for debug output |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow tracking server URL |
| `MLFLOW_EXPERIMENT_NAME` | `arc-raiders-rag` | MLflow experiment name |

## Project Structure

```
├── Dockerfile                   Multi-stage build (frontend + backend)
├── docker-compose.yml           Full stack: app + MLflow + Ollama
├── docs/INTERVIEW.md            Interview talking points
├── .github/workflows/ci.yml     CI pipeline (lint backend + frontend)
│
├── backend/
│   ├── server.py                FastAPI entry point + static file serving
│   ├── run_demo.py              Single-question smoke test
│   ├── run_eval.py              Evaluation harness (golden dataset → MLflow)
│   ├── run_mlflow_ui.py         Start MLflow (Windows / cross-platform)
│   ├── run_mlflow_ui.sh         Start MLflow (bash)
│   ├── eval_dataset.json        Golden test questions for evaluation
│   ├── requirements.txt         Python dependencies
│   └── arc_raider_bot/
│       ├── config.py            Env var loading
│       ├── prompts.py           System prompts (main + validator)
│       ├── models.py            Pydantic models (agent + API)
│       ├── agent.py             LLM agents + pipeline + MLflow tracing
│       ├── sessions.py          Conversation history store
│       ├── knowledge_cache.py   ChromaDB RAG cache
│       ├── tracing.py           MLflow tracing setup
│       └── cli.py               Interactive terminal client
│
└── frontend/
    └── src/
        ├── api.ts               API client
        ├── App.tsx              Chat UI shell
        └── components/          ChatWindow, ChatInput, BotMessage
```

## MLflow Tracing

Every call to the RAG pipeline is traced with MLflow. Spans are created for cache lookup, LLM generation, web search, validation, and cache storage. Summary metrics (latency, cache hits, source count, etc.) are logged per run.

```bash
cd backend

# Start the MLflow tracking server (new terminal)
python run_mlflow_ui.py         # http://localhost:5000

# Run the bot as usual — traces are sent automatically
python server.py
```

If the MLflow server isn't running, the bot still starts normally — tracing is silently skipped.

## Evaluation

The evaluation script runs a golden dataset of ARC Raiders questions through the pipeline and measures answer quality. Results are logged to MLflow for comparison.

```bash
cd backend

python run_eval.py                         # all questions
python run_eval.py --max-questions 5       # quick test
```

On Windows PowerShell for verbose output:

```powershell
$env:VERBOSE_TOOL_CALLS="1"; python run_eval.py
```

The script measures keyword recall, latency, source count, and answer length. Change a config → re-run eval → compare runs in MLflow.

## CI Pipeline

GitHub Actions runs on every push/PR to `main`: Ruff (backend) + ESLint (frontend).

## Other Ways to Run

```bash
cd backend

# Interactive CLI (no frontend needed)
python -m arc_raider_bot.cli

# Smoke test with verbose output
python run_demo.py
```
