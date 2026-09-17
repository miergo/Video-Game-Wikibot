# Interview study sheet — ARC Raiders WikiBot

Read-later cheat sheet for talking about this project. Match your CV bullets; do not overclaim.

---

## 30-second pitch

> I built a wiki-style chatbot for ARC Raiders that answers with a **local LLM**, **web search**, and a **semantic Q&A cache**. The pipeline is cache lookup → generation (DuckDuckGo if needed) → a validator agent → store the result. **MLflow** traces every step and compares config changes against a golden dataset. The stack — FastAPI, React, Ollama, MLflow — runs on **Docker Compose**.

Then stop. Let them pick a bullet.

---

## Architecture (whiteboard)

```
User question
    │
    ├─ session history (in-memory LRU, 200 sessions)
    │
    ▼
ChromaDB semantic cache  ← embed question with nomic-embed-text
    │  cosine sim ≥ 0.75 → inject past Q&A into prompt
    ▼
Main agent (llama3.1:8b via PydanticAI / Ollama)
    │  tool: websearch (DuckDuckGo) unless cache fully answers
    │  output: { answer, sources[] }  — URLs never in the answer text
    ▼
Validator agent (same model)
    │  checks: on-topic, no leaked URLs, not fabricated, sources sane
    │  can rewrite answer/sources
    ▼
Store Q&A back in Chroma  +  log spans/metrics to MLflow
```

**Critical distinction:** this is **not** classic document RAG. There is no scraped wiki corpus. Chroma stores **past questions and answers**. Similar questions reuse previous work; fresh questions go to the web. Call it a **semantic cache with RAG-style retrieval**, not “we indexed the whole wiki.”

### Ports (easy to mix up)

| Service | Local | Docker host |
|---|---|---|
| Chat API / UI | 8000 / 5173 | 8001 |
| MLflow | 5000 | 5001 |
| Ollama | 11434 | 11435 |

### Numbers to know

- Models: `llama3.1:8b`, `nomic-embed-text`
- Cache: cosine, threshold `0.75`, top 3
- Eval: ~18 golden questions, keyword recall
- Experiment: `arc-raiders-rag`
- Sessions: 200 LRU; agent retries 5 / 3
- Search: DuckDuckGo via `ddgs`, max 6 results
- CI: Ruff + ESLint only (no eval in CI — model too large for runners)

---

## CV bullet 1 — RAG, PydanticAI, Chroma, Ollama

### Why PydanticAI (not for eval)

PydanticAI is the **agent runtime** that talks to the LLM. It is **not** the eval framework.

What it does on each `ask()`:

1. **Structured output** — force `ArcRaidersResponse` / `ValidationVerdict`
2. **Retries** — 5 (main) / 3 (validator) when the 8B model returns invalid JSON
3. **Tool calling** — `websearch` as a tool the model can invoke
4. **Message history** — multi-turn via `run_sync(..., message_history=...)`
5. **Ollama adapter** — OpenAI-compatible `/v1` endpoint

What it does **not** do: score answers, log experiments, own the golden dataset.

| Piece | Library |
|---|---|
| Agents, tools, structured output | PydanticAI |
| DuckDuckGo | `ddgs` |
| Vector cache | ChromaDB |
| Observability / eval | MLflow |
| HTTP | FastAPI |

Interview one-liner:

> PydanticAI is how the bot generates a typed answer with tools. MLflow is how I watch that pipeline and compare configs. I didn’t use PydanticAI’s eval features.

### Other talking points

- **Why local Ollama:** no API keys, full control, demo-able offline
- **Why two agents:** generator vs critic; validator does not invent new facts
- **Why Chroma:** embed the *question*, store answer/sources as metadata
- **Embeddings URL gotcha:** chat is `/v1`; embeddings are `/api/embeddings`
- **Sessions:** in-memory OrderedDict LRU + lock; FastAPI runs sync agent on a thread pool
- **Fallback:** regex parse if structured output still fails after retries — and be honest that fallback answers can pollute the cache

### Likely follow-ups

| They ask | You answer |
|---|---|
| Why not a vector store of wiki pages? | Game wikis change; search is live truth. Cache is for repeat questions and latency. |
| Why 0.75? | Configurable. Too low → wrong context. Too high → never hits. I evaluate with the golden set in MLflow. |
| Hallucinations? | Ground in search + cache; forbid invented URLs; validator. Keyword eval does not prove factual accuracy. |
| Multi-turn? | History goes to the main agent. Cache is per-question similarity, not conversation-aware retrieval. |

---

## CV bullet 2 — MLflow

Do **not** say “I used MLflow to train a model.” You did not.

### What MLflow actually does

1. **Online observability** — every `ask()` is a trace:
   - `cache_lookup` (RETRIEVER)
   - `main_agent` (LLM)
   - `websearch` (TOOL)
   - `validator` (LLM)
   - `cache_store`
   - root `ask_pipeline` + metrics: latency, cache hits, max similarity, source count, answer length, validator_corrected, used_fallback

2. **Offline eval** — golden questions → keyword recall → named runs with params (model, threshold, prompt hash) and aggregate metrics + JSON artifact

### Why MLflow

- One tool for **traces + experiment comparison**
- Local UI, no SaaS
- Tracing is **best-effort**: probe `/version` with a 2s timeout so a down server never blocks the bot

### Docker gotcha

MLflow 3.5+ rejects non-localhost `Host` headers. Inside Compose the app talks to `http://mlflow:5000` and needs `--allowed-hosts '*'`. App `depends_on` MLflow with a **healthcheck**.

### Honest limits

- Eval is **keyword recall**, not a judge LLM
- CI does **not** run eval
- Prompt versioning = SHA-256 prefix of the system prompt, not MLflow Prompt Registry
- No model registry / serving — the “model” is Ollama

---

## CV bullet 3 — Docker Compose, FastAPI, React

- Three services: **app** (API + built UI), **MLflow**, **Ollama**
- **Multi-stage Dockerfile:** Node builds React → copy `dist` into slim Python image
- **Dev vs prod:** Vite + CORS in dev; one origin in Docker
- **Volumes:** Chroma, MLflow data, Ollama models
- **GPU:** optional — uncomment `deploy:` under `ollama` in Compose; default is CPU

---

## Safe wording (do not overclaim)

| Avoid | Safer |
|---|---|
| “Full RAG over a knowledge base” | “Semantic cache of past Q&A + live web grounding” |
| “MLflow for model training/registry” | “Tracing and offline experiment comparison” |
| “Production GPU serving” | “Optional Compose GPU for local Ollama” |
| “Automated eval in CI” | “Local eval; CI is lint because of model size” |
| “High accuracy” | “Keyword recall as a cheap relevance proxy” |

Frame dates as a **focused MLOps/RAG demo**, not a 6-month product.

---

## If they only have 2 minutes — three decisions

1. **Semantic cache, not a static corpus** — live game info + reuse of similar questions
2. **Generator + validator + structured outputs** — reliability without a bigger model
3. **MLflow traces + golden-set eval** — measure prompt/threshold/model changes; tracing never blocks the app

---

## How it could get better (if asked)

1. Ingest a real wiki corpus **plus** keep the Q&A cache
2. Do not cache fallback / failed answers (cache poisoning)
3. Stronger eval: groundedness, citation checks, per-category scores, regression gate
4. Skip websearch in **code** on high cache similarity (not only in the prompt)
5. Persist sessions (Redis); stream the UI; show cache hit / latency in the product

## How it could get simpler (if asked)

Keep the product (answer + sources). Optional cuts: drop validator (second LLM call), drop Chroma (history + search only), drop MLflow server (print metrics / local JSON), CLI-only instead of React. This repo optimized for the **interview story**, not the minimum bot.

---

## Request walkthrough (one sentence)

Frontend `POST /api/ask` → thread pool → `ask()` → cache span → maybe websearch → validator → store → MLflow metrics → `{answer, sources, session_id}`.
