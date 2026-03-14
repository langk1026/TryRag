# TryRag

RAG system built on top of Microsoft SharePoint documents. Indexes content via the Graph API, stores embeddings in ChromaDB, and serves answers through a FastAPI backend with a React frontend.

The retrieval pipeline runs as a LangGraph state graph: query expansion, hybrid vector + BM25 search, cross-encoder reranking, Gemini generation, and RAGAS faithfulness evaluation with an automatic retry loop.

---

## Architecture

```
SharePoint (Graph API)
        |
        v
  IndexingService (APScheduler, 30-min incremental)
        |
        v
  DocumentProcessor (PDF, DOCX, XLSX)
  TextChunker + RecursiveSplitter
        |
        v
  ChromaDB (embeddings via Google text-embedding-004)
        |
   [query time]
        |
        v
  LangGraph pipeline
        |
    +---+---+---+---+---+---+
    |                       |
  query_node           evaluate_node
  rewrite_node  -----> route_after_evaluation
  retrieve_node           |           |
  rerank_node          "end"       "retry"
  generate_node                      |
                               retry_node ---> rewrite_node
        |
        v
  FastAPI /api/v1/query
        |
        v
  React frontend
```

**Observability:** OpenTelemetry traces exported to Jaeger via an OTEL Collector sidecar. Grafana available for dashboards.

---

## LangGraph Pipeline Nodes

| Node | What it does |
|---|---|
| `query_node` | Sanitises and initialises state |
| `rewrite_node` | Generates multiple query variants (multi-query); optionally appends a HyDE hypothetical answer as an additional query |
| `retrieve_node` | Runs each query variant through hybrid retrieval (vector + BM25), deduplicates by document ID, sorts by hybrid score |
| `rerank_node` | Cross-encoder reranking via `BAAI/bge-reranker-v2-m3`; falls back to hybrid score if model unavailable |
| `generate_node` | Builds context string, calls Gemini for answer generation |
| `evaluate_node` | Faithfulness scoring via RAGAS or heuristic term-overlap fallback |
| `retry_node` | Increments retry counter, widens `top_k` by 3, routes back to `rewrite_node` |

Retry fires when `faithfulness < threshold` and `retry_count < max_retries`. Configurable via `.env`.

---

## Retrieval: Hybrid Search

Vector search and BM25 keyword search run independently against the same candidate pool. Scores are min-max normalised per retriever, then merged with configurable weights:

```
hybrid_score = (vector_weight * vector_norm) + (keyword_weight * keyword_norm)
```

Default: `vector_weight=0.6`, `keyword_weight=0.4`. Adjust via `.env`.

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM | Google Gemini 2.0 Flash |
| Embeddings | Google text-embedding-004 |
| Vector store | ChromaDB |
| Keyword search | BM25 (rank-bm25) |
| Reranker | sentence-transformers CrossEncoder (BAAI/bge-reranker-v2-m3) |
| Evaluation | RAGAS faithfulness + heuristic fallback |
| Document source | Microsoft SharePoint (Graph API) |
| API | FastAPI |
| Frontend | React + Vite + Tailwind CSS |
| Scheduler | APScheduler |
| Tracing | OpenTelemetry → Jaeger |
| Dashboards | Grafana |
| Containers | Docker Compose (6 services) |

---

## Services

| Service | Port | Purpose |
|---|---|---|
| backend | 8000 | FastAPI — query, indexing, health endpoints |
| cron | — | APScheduler — incremental SharePoint indexing every 30 min |
| otel-collector | 4317, 4318 | OTLP receiver, forwards traces to Jaeger |
| jaeger | 16686 | Trace visualisation |
| grafana | 3001 | Dashboards |
| frontend | 3000 | React UI |

---

## API Routes

| Route | Purpose |
|---|---|
| `POST /api/v1/query` | Run a RAG query — returns answer, sources, evaluation, retry count |
| `POST /api/v1/index` | Trigger a full re-index from SharePoint |
| `GET /api/v1/index/status` | Current index state (doc count, last indexed time) |
| `GET /api/v1/health` | Service health |

---

## Quickstart

```bash
git clone https://github.com/langk1026/TryRag.git
cd TryRag

cp .env.example .env
# Required: GOOGLE_API_KEY, SHAREPOINT_* credentials
# Optional: HYDE_ENABLED, MULTI_QUERY_ENABLED, RERANKER_ENABLED, RAGAS_ENABLED

docker compose up -d --build
```

Frontend: `http://localhost:3000`
API docs: `http://localhost:8000/docs`
Jaeger UI: `http://localhost:16686`
Grafana: `http://localhost:3001`

---

## Configuration

All options are set via environment variables. Copy `.env.example` to `.env`.

**Core**

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Required. Google AI Studio API key |
| `LLM_MODEL` | `gemini-2.0-flash-exp` | Gemini model name |
| `EMBEDDING_MODEL` | `models/text-embedding-004` | Embedding model |
| `SHAREPOINT_SITE_URL` | — | Required. SharePoint site URL |
| `SHAREPOINT_CLIENT_ID` | — | Required. Azure app client ID |
| `SHAREPOINT_CLIENT_SECRET` | — | Required. Azure app client secret |
| `SHAREPOINT_TENANT_ID` | — | Required. Azure tenant ID |

**Retrieval**

| Variable | Default | Description |
|---|---|---|
| `HYBRID_SEARCH_ENABLED` | `true` | Enable vector + BM25 hybrid search |
| `HYBRID_VECTOR_WEIGHT` | `0.6` | Weight for vector scores |
| `HYBRID_KEYWORD_WEIGHT` | `0.4` | Weight for BM25 scores |
| `HYDE_ENABLED` | `false` | Generate hypothetical answer before retrieval |
| `MULTI_QUERY_ENABLED` | `false` | Generate multiple query variants |

**Reranking**

| Variable | Default | Description |
|---|---|---|
| `RERANKER_ENABLED` | `false` | Enable cross-encoder reranking |
| `RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` | HuggingFace reranker model |
| `RERANKER_TOP_N` | `5` | Documents to keep after reranking |

**Evaluation**

| Variable | Default | Description |
|---|---|---|
| `RAGAS_ENABLED` | `false` | Enable RAGAS faithfulness scoring |
| `FAITHFULNESS_THRESHOLD` | `0.75` | Minimum score to pass without retry |
| `MAX_RETRIES` | `2` | Max retry attempts per query |

---

## Document Support

- PDF (PyPDF2)
- DOCX (python-docx)
- XLSX (openpyxl)

Files are split with a recursive character splitter. Default chunk size: 1000 tokens, overlap: 200.

---

## Observability

OpenTelemetry spans cover every LangGraph node. Set `TELEMETRY_ENABLED=true` and ensure the `otel-collector` service is running. Traces appear in Jaeger at `http://localhost:16686`.

---

## Known Limitations

- ChromaDB is file-based and stored in a Docker volume — not suitable for multi-replica deployments without a remote ChromaDB server
- SharePoint authentication uses client credentials (app-only). Delegated auth not supported.
- RAGAS evaluation adds latency per query; disable with `RAGAS_ENABLED=false` for lower-latency use cases
- Reranker model downloads on first startup (~500MB); ensure network access from the container

---

## Roadmap

- [ ] GitLab Enterprise connector (document source)
- [ ] Freshdesk connector (document source)
- [ ] Remote ChromaDB support for horizontal scaling
- [ ] Streaming response via Server-Sent Events
- [ ] User feedback loop for continuous retrieval improvement
