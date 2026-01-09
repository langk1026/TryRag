# RAG Document Assistant

A production-ready Retrieval-Augmented Generation (RAG) application for querying SharePoint documents with transparent, modular architecture.

## Architecture Overview

### Backend Components

- **FastAPI Server**: RESTful API with endpoints for querying and indexing
- **SharePoint Connector**: Integrates with Microsoft SharePoint using Office365-REST-Python-Client
- **Document Processor**: Extracts text from PDF, DOCX, XLSX, TXT, and MD files
- **RAG Engine**: Orchestrates the complete RAG pipeline with full transparency
- **Vector Store**: ChromaDB for persistent vector embeddings
- **Embedding Service**: OpenAI embeddings with batching support
- **Text Chunker**: Smart chunking with overlap and sentence boundary detection
- **Index Scheduler**: Automated cron job for incremental indexing

### Frontend Components

- **React + Vite**: Modern, fast development experience
- **Tailwind CSS**: Utility-first styling
- **Search Interface**: Clean UI for asking questions
- **Index Manager**: Control panel for manual indexing operations

## Project Structure

```
rag-application/
├── backend/
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints
│   ├── core/
│   │   ├── config.py              # Configuration management
│   │   ├── logger.py              # Logging setup
│   │   ├── embeddings.py          # OpenAI embedding service
│   │   ├── text_chunker.py        # Document chunking logic
│   │   └── rag_engine.py          # Main RAG orchestration
│   ├── services/
│   │   ├── sharepoint_connector.py # SharePoint integration
│   │   ├── document_processor.py   # Text extraction
│   │   ├── vector_store.py         # ChromaDB interface
│   │   └── indexing_service.py     # Document indexing
│   ├── models/
│   │   └── index_state.py          # Index state tracking
│   └── main.py                     # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchInterface.jsx
│   │   │   └── IndexManager.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── styles/
│   │   │   └── index.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   └── index_scheduler.py          # Automated indexing cron
├── .env.example
└── requirements.txt
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- SharePoint site with appropriate permissions
- OpenAI API key

### Backend Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Start the FastAPI server:
```bash
python backend/main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

The UI will be available at `http://localhost:3000`

### Automated Indexing

Start the index scheduler for automated incremental updates:

```bash
python scripts/index_scheduler.py
```

This runs every 30 minutes (configurable in `.env`)

## API Endpoints

### Query Endpoint
```
POST /api/v1/query
Body: {
  "question": "Your question here",
  "top_k": 5,
  "temperature": 0.7
}
```

### Indexing Endpoints
```
POST /api/v1/index/full          # Full reindex
POST /api/v1/index/incremental   # Incremental index
GET  /api/v1/index/stats         # Index statistics
```

### Health Check
```
GET /api/v1/health
```

## RAG Pipeline Flow

1. **User Query** → Received by FastAPI endpoint
2. **Query Embedding** → Generate embedding using OpenAI
3. **Vector Search** → Retrieve top-k similar chunks from ChromaDB
4. **Context Building** → Construct context from retrieved documents
5. **LLM Generation** → OpenAI generates answer based on context
6. **Response** → Return answer with source citations

## Indexing Pipeline Flow

1. **Document Fetch** → Retrieve documents from SharePoint
2. **Text Extraction** → Extract text based on file type
3. **Chunking** → Split text into overlapping chunks
4. **Embedding** → Generate embeddings for chunks
5. **Storage** → Store in ChromaDB with metadata
6. **State Update** → Track last indexed time

## Configuration Options

Key environment variables:

- `SHAREPOINT_SITE_URL`: Your SharePoint site URL
- `SHAREPOINT_CLIENT_ID`: Azure AD app client ID
- `SHAREPOINT_CLIENT_SECRET`: Azure AD app client secret
- `OPENAI_API_KEY`: OpenAI API key
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)
- `LLM_MODEL`: LLM model (default: gpt-4-turbo-preview)
- `CHUNK_SIZE`: Text chunk size in characters (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap in characters (default: 200)
- `INDEX_SCHEDULE_MINUTES`: Indexing frequency (default: 30)

## Code Style Guidelines

This project follows strict code style conventions:

- **No Type Hints**: Python code uses no type annotations
- **Self-Documenting**: Variable and function names are descriptive
- **Minimal Comments**: Comments only for complex logic
- **Clean Architecture**: Clear separation of concerns
- **Transparency**: Every step is logged for traceability

## Transparency Features

All pipeline steps are logged with:
- Timestamp
- Operation details
- Success/failure status
- Performance metrics

Logs are written to both console and file for analysis.

## License

MIT License
