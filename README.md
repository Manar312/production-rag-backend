# Production RAG Backend

A document-based Retrieval-Augmented Generation (RAG) backend built with FastAPI. The system allows users to organize documents into projects, process uploaded files, retrieve relevant content, and generate answers grounded in the project's documents.

## Features

- REST API documented with Swagger UI.
- Project creation and document uploads.
- Local file storage.
- MongoDB for project and document metadata.
- Celery and Redis for background document processing.
- Qdrant for vector storage and semantic retrieval.
- FastEmbed for multilingual text embeddings.
- PDF text extraction and OCR support for scanned documents.
- Arabic and English OCR using Tesseract language data.
- Support for PDF, DOCX, TXT, CSV, XLSX, PPTX, and common image formats.
- Chunking, embedding, retrieval, and source-aware answer generation.
- Automated tests for document processing, chunking, query schemas, and query behavior.

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| API | FastAPI | REST endpoints and request validation |
| API documentation | Swagger UI | Interactive API testing |
| Metadata database | MongoDB | Projects, assets, and processing metadata |
| Vector database | Qdrant | Embedding storage and similarity search |
| Background processing | Celery | Asynchronous document-processing tasks |
| Message broker and result backend | Redis | Celery task coordination |
| Embeddings | FastEmbed | Multilingual vector generation |
| OCR | Tesseract and pytesseract | Text extraction from scanned documents and images |
| Testing | pytest and HTTPX | Automated tests |

## Architecture Overview

1. A client creates a project through the API.
2. The client uploads a document to that project.
3. The backend stores the file locally and records its metadata in MongoDB.
4. A background task processes the document and extracts text, using OCR when required.
5. Extracted text is divided into chunks.
6. The chunks are embedded and indexed in Qdrant; chunk metadata is stored in MongoDB.
7. A user submits a question for a project.
8. The system retrieves relevant chunks and uses the configured LLM provider to generate an answer.

The intended response flow uses retrieved document context. Retrieval quality and answer grounding should still be evaluated with representative documents and questions.

## Project Structure

```text
.
├── compose.yaml
├── models/
│   └── tessdata/
│       ├── ara.traineddata
│       └── eng.traineddata
├── requirements.txt
├── pytest.ini
├── test_mongo_connection.py
├── src/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       └── routes/
│   ├── core/
│   │   ├── celery_app.py
│   │   └── config.py
│   ├── db/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   │   ├── document_processors/
│   │   └── ocr/
│   └── tasks/
└── tests/
```

## Requirements

- Python 3.13 or a compatible Python version supported by the dependencies.
- Docker Desktop with Docker Compose.
- Tesseract OCR installed on Windows.
- The Tesseract Arabic and English language files included under `models/tessdata/`.
- An LLM provider compatible with the configured API settings for answer generation.

The default Tesseract executable path in the application configuration is:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

If Tesseract is installed elsewhere, update `TESSERACT_CMD` in your local `.env` file.

## Local Setup (Windows PowerShell)

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the URL and repository directory with your actual GitHub repository details.

### 2. Create and activate a virtual environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks virtual-environment activation, use an approved local PowerShell execution-policy configuration or run the environment's Python executable directly.

### 3. Install Python dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally before starting the services.

Set strong, unique values for:

- `MONGO_ROOT_USERNAME`
- `MONGO_ROOT_PASSWORD`
- `MONGO_APP_USERNAME`
- `MONGO_APP_PASSWORD`

Also configure the LLM provider settings when answer generation is required:

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`

Never commit `.env` or share its secrets publicly.

### 5. Start infrastructure services

```powershell
docker compose up -d
docker compose ps
```

The Compose configuration starts MongoDB, Redis, and Qdrant with persistent named volumes.

The services publish ports on `127.0.0.1` for local development:

| Service | Local address |
|---|---|
| MongoDB | `127.0.0.1:27017` |
| Redis | `127.0.0.1:6379` |
| Qdrant | `http://127.0.0.1:6333` |

### 6. Create the MongoDB application user on a fresh installation

The Compose configuration creates the MongoDB root user. It does not automatically create the separate application user.

For a fresh database volume, connect to MongoDB:

```powershell
docker exec -it rag-mongodb mongosh -u rag_admin -p --authenticationDatabase admin
```

Enter the root password when prompted, then execute these commands in the MongoDB shell:

```javascript
use rag_db

db.createUser({
  user: "rag_app",
  pwd: "REPLACE_WITH_YOUR_APP_PASSWORD",
  roles: [{ role: "readWrite", db: "rag_db" }]
})
```

Use the same application username and password in `.env`, with `MONGO_APP_AUTH_DATABASE=rag_db`.

Replace the example username and password if you chose different values. Do not put real passwords in source files or commit them.

If your MongoDB volume already exists, do not recreate it just to follow this step. Existing volumes preserve database state, and changing Compose's root-user environment variables does not automatically change users in an already-initialized database.

### 7. Start the API

In the first PowerShell terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Open Swagger UI:

http://127.0.0.1:8000/docs

### 8. Start the Celery worker

Open a second PowerShell terminal in the project directory:

```powershell
.\.venv\Scripts\Activate.ps1
python -m celery -A src.core.celery_app:celery_app worker --loglevel=info --pool=solo
```

The worker command is intended for local development on Windows. The application API and worker are not currently packaged as Docker services.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API health check |
| GET | `/health/database` | MongoDB connectivity check |
| POST | `/api/v1/projects` | Create a project |
| POST | `/api/v1/projects/{project_id}/assets` | Upload a document to a project |
| POST | `/api/v1/projects/{project_id}/query` | Ask a question about a project |

Use Swagger UI to inspect request schemas, submit requests, and review response models.

## Configuration

Application settings are loaded from `.env` through Pydantic Settings.

Important settings include:

| Variable | Purpose |
|---|---|
| `MONGO_DATABASE` | MongoDB application database |
| `MONGO_APP_USERNAME` | MongoDB application user |
| `MONGO_APP_PASSWORD` | MongoDB application password |
| `MONGO_APP_AUTH_DATABASE` | Database used to authenticate the application user |
| `REDIS_URL` | Redis connection URL |
| `CELERY_BROKER_URL` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Celery result backend URL |
| `QDRANT_URL` | Qdrant connection URL |
| `QDRANT_COLLECTION` | Vector collection name |
| `EMBEDDING_MODEL` | Embedding model identifier |
| `EMBEDDING_DIMENSION` | Expected embedding vector dimension |
| `MAX_UPLOAD_SIZE_MB` | Maximum upload size in MB |
| `TESSERACT_CMD` | Local Tesseract executable path |
| `LLM_API_KEY` | LLM provider API key |
| `LLM_BASE_URL` | LLM provider API base URL |
| `LLM_MODEL` | LLM model identifier |

Check `.env.example` and `src/core/config.py` for the current configuration defaults.

## Running Tests

Run the test suite:

```powershell
python -m pytest -q
```

Compile-check the application and tests:

```powershell
python -m compileall -q src tests
```

Check installed dependency consistency:

```powershell
python -m pip check
```

## Development Notes and Limitations

- Uploaded documents are stored locally; external object storage is not configured.
- The API and Celery worker are run from the local Python environment.
- Tesseract must be installed separately; the trained-data files alone are not the OCR executable.
- MongoDB, Redis, and Qdrant are configured for local development, not as a complete production security deployment.
- Redis is not configured with authentication in the current Compose setup. Do not expose these development services to untrusted networks.
- The Qdrant image currently uses the `latest` tag. Pin a tested version before building a reproducible deployment.
- Authentication, authorization, multi-user access controls, production secrets management, and deployment hardening require additional work.
- Retrieval and generated answers should be evaluated for relevance, source correctness, and hallucination resistance before production use.

## License

No license has been specified yet.
