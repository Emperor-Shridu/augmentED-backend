# AugmentED Backend

FastAPI backend prototype for an AI-augmented learning library. AugmentED lets a learner upload a PDF, build a local retrieval context, ask questions from that document, summarize text, generate study notes, and run semantic passage search.

This repository is portfolio-ready but still prototype-stage. The hosted API can expose health and route-level behavior, while the full AI workflow requires local model files and vector-store dependencies.

The repo also includes a simple Streamlit frontend for demos and interviews.

For hosted demos, the recommended AI mode is Gemini Flash Lite through `GEMINI_API_KEY`. This avoids the local Milvus/GGUF setup and works better on Render-style hosting.

## What It Does

- Uploads PDF learning material and stores timestamped copies under `data/user_doc`.
- Keeps one active PDF context for chat/search; uploading another PDF replaces the active context.
- Answers questions from the current document context.
- Summarizes raw study text into concise notes.
- Generates short note-style summaries.
- Retrieves semantically similar passages with embedding search.
- Provides lightweight health routes for deployment checks.
- Includes a Streamlit demo UI with upload, chat, summarize, notes, search, and admin stats tabs.

## Tech Stack

- **API:** FastAPI, Uvicorn
- **Frontend:** Streamlit
- **Hosted AI option:** Gemini Flash Lite API
- **Local LLM:** llama.cpp through `llama_cpp_python`
- **Model target:** Zephyr 7B Beta GGUF (`zephyr-7b-beta.Q4_K_M.gguf`)
- **Embeddings:** Hugging Face `thenlper/gte-small`
- **Retrieval:** LlamaIndex, Milvus vector store, BM25 retrieval helpers
- **Document parsing:** LlamaIndex `SimpleDirectoryReader`, PDF support through `pypdf`

## API Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service metadata |
| `GET` | `/health/` | Hosting and uptime health check |
| `GET` | `/ai/status/` | Shows active AI provider and Gemini model configuration |
| `GET` | `/admin/stats/` | Safe demo stats for uploaded PDFs and local AI artifact status |
| `POST` | `/uploadbook/` | Upload a PDF and prepare it for document chat |
| `POST` | `/getbook/` | Download a stored PDF by filename |
| `POST` | `/reindex/` | Rebuild vector indexes with the maintenance password |
| `POST` | `/documentchat/` | Ask a question about the active document |
| `POST` | `/summarizer/` | Summarize supplied text |
| `POST` | `/notemaker/` | Generate study notes from supplied text |
| `POST` | `/similaritysearch/` | Return similar passages for supplied text |

## Current Prototype Scope

The project is intentionally local-first because the AI workflow depends on a quantized model file and local vector index infrastructure. Health routes and non-AI server startup are hostable on standard Python app platforms. AI endpoints return a clear `503` response if the local model stack is not available.

Known gaps to address before production:

- Add authentication and user-level document isolation.
- Replace the hard-coded reindex password with environment-based secrets.
- Add persistent metadata storage for uploaded documents.
- Add automated tests around upload, retrieval errors, and AI unavailable states.
- Benchmark response latency, memory usage, and PDF size limits.
- Complete or replace the unfinished ingestion pipeline class used by the AI module.

## Local Setup

Use Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Dependency files:

- `requirements.txt` is for full local development with the AI stack.
- `requirements-backend.txt` is for lightweight hosted FastAPI demos.
- `requirements-frontend.txt` is for Streamlit-only frontend hosting.

The API will run at:

```text
http://127.0.0.1:5555
```

Check the health route:

```powershell
curl http://127.0.0.1:5555/health/
```

Interactive API docs are available at:

```text
http://127.0.0.1:5555/docs
```

## Gemini Hosted AI Mode

Set a Gemini API key to bypass the local Milvus/GGUF pipeline:

```powershell
$env:GEMINI_API_KEY="your-api-key"
$env:GEMINI_MODEL="gemini-3.1-flash-lite"
python main.py
```

On Render, add these environment variables:

```text
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.1-flash-lite
```

With `GEMINI_API_KEY` present, the backend uses Gemini for:

- PDF upload + active document context
- document chat
- summarization
- note generation
- PDF-based search-style answers

Current document behavior: one PDF is active at a time. Admin stats separate the active document, unique uploaded filenames, and total upload events so duplicate uploads do not look like multiple active contexts.

Official references:

- Gemini models: https://ai.google.dev/gemini-api/docs/models/gemini
- Gemini document/PDF processing: https://ai.google.dev/gemini-api/docs/document-processing

## Run the Demo Frontend

Start the backend first:

```powershell
python main.py
```

In a second terminal, start Streamlit:

```powershell
streamlit run frontend/streamlit_app.py
```

The frontend will open at:

```text
http://localhost:8501
```

If your backend is hosted elsewhere, set the backend URL in the Streamlit sidebar or with:

```powershell
$env:AUGMENTED_API_URL="https://your-backend-url"
streamlit run frontend/streamlit_app.py
```

## Full AI Mode

The original local AI mode is still available when `GEMINI_API_KEY` is not set. To run that path locally, place the GGUF model at:

```text
chatbot/models/zephyr-7b-beta.Q4_K_M.gguf
```

The model and generated indexes are intentionally ignored by Git because they are large local artifacts.

## Resume Bullets

- Built a FastAPI backend for an AI learning library that supports PDF upload, document-grounded question answering, text summarization, note generation, and semantic passage search.
- Integrated a local RAG pipeline using LlamaIndex, Hugging Face embeddings, Milvus vector search, BM25 helpers, and a quantized Zephyr 7B model through llama.cpp.
- Improved deployability of a local-first AI prototype by adding lightweight health routes and graceful unavailable-state handling for heavy model dependencies.

## Documentation

- [STAR project write-up](docs/project_star.md)
- [GitHub and hosting guide](docs/github_hosting_guide.md)
- [Interview portfolio log](docs/interview_portfolio_log.md)
