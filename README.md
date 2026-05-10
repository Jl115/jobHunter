# Job Hunter — Desktop App

A PySide6 + FastAPI desktop application that receives job postings from your browser via a Chrome Extension, extracts structured fields with a local LLM, matches them against your uploaded resume, and drafts personalised outreach emails.

## What it does

| Step | Action |
|------|--------|
| 1 | Chrome Extension sends a job page (LinkedIn, Indeed, Xing) to `http://localhost:8080/api/v1/jobs/capture` |
| 2 | Desktop App stores the raw HTML, then runs a local LLM (`Qwen2.5-3B-Instruct-GGUF`) to extract title, company, location, and description |
| 3 | You upload a PDF resume — the LLM parses it for skills and experience |
| 4 | The app computes a semantic match score between each job and your resume (via `sentence-transformers`) |
| 5 | You click **Draft Email** — a personalised email is pre-filled with the role and your top matching skills, ready to open in your default mail client |

## Tech Stack

- **GUI** — PySide6 (Qt) with `QThread` + `QThreadPool`
- **Server** — FastAPI + Uvicorn, runs inside a background `QThread`
- **Database** — SQLite via standard-library `sqlite3` (thread-safe)
- **LLM** — `llama-cpp-python` with `Qwen2.5-3B-Instruct-GGUF` (~1.8 GB)
- **Resume** — `pdfplumber` for text extraction
- **Matching** — `sentence-transformers` (`all-MiniLM-L6-v2`)

## Quick Start

Requires **Python 3.12+** and **4 GB RAM** (3 GB for the LLM).

```bash
# 1. Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create environment
uv venv

# 3. Install dependencies
uv pip install -e .

# 4. Launch the app
uv run job-hunter
```

On first launch the app downloads the LLM automatically (~1.8 GB, cached in `~/.cache/job_hunter/models/`).

## Extension pairing

The Chrome Extension (`../job_hunter_extension/`) communicates over HTTP. The default endpoint is:

```
http://localhost:8080/api/v1/jobs/capture
```

The server binds to `127.0.0.1:8080` only and accepts `chrome-extension://*` CORS origins.

## Directory Layout

```
src/
├── main.py              # Application entry point (QApplication → event loop)
├── app.py               # ApplicationController: boots DB, server, UI, DI wiring
├── workers.py           # QRunnable tasks: LLM extraction, matching, email drafting
├── features/
│   ├── job_extraction/  # LLM-based field extraction (sliding-window batched)
│   ├── jobs/            # Repository + matcher + store (SQLite + embeddings)
│   ├── resume/          # PDF text extraction + LLM skill parsing + repository
│   └── email/           # EmailComposer + MailtoGenerator
├── widgets/
│   ├── main_window.py   # QMainWindow with QStackedWidget (list → detail → email)
│   ├── job_list_widget.py
│   ├── job_detail_widget.py
│   └── email_preview_widget.py
├── shared/
│   ├── models.py        # Pydantic data classes (Job, Resume, EmailDraft)
│   ├── app_state.py     # Singleton reactive store (Qt signals)
│   └── constants.py     # DEFAULT_PORT, MODELS_CACHE_DIR, DEFAULT_GGUF_MODEL
└── infrastructure/
    ├── api/             # FastAPI app factory + routers (jobs, resumes)
    └── database/        # Thread-safe sqlite3 wrapper + migration
```

## Architecture Highlights

- **Feature-sliced design:** each feature is self-contained under `src/features/<name>/`; internal modules live in `internal/` and are not imported by other features.
- **Dependency injection:** `ApplicationController` creates services (repository, matcher, LLM) and injects them into `MainWindow` and `ExtractionWorker`.
- **Signals not polling:** the UI reacts to `AppState` signals (`jobs_updated`, `extraction_completed`, etc.) — never polls the database.
- **Background tasks:** heavy I/O (LLM inference, sentence-transformers matching) runs on `QThreadPool` so the GUI stays responsive.
- **Batch extraction:** long job postings are split into overlapping 1,500-char sliding windows. The LLM processes each window independently; results are merged. This prevents truncation of long German job postings.

## Configuration

Settings are controlled via environment variables and `src/shared/constants.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_PORT` | `8080` | FastAPI local port (localhost only) |
| `DATABASE_PATH` | `~/.local/share/job_hunter/job_hunter.db` | SQLite file |
| `MODELS_CACHE_DIR` | `~/.cache/job_hunter/models` | GGUF + embedding model cache |
| `DEFAULT_GGUF_MODEL` | `qwen2.5-3b-instruct-q4_k_m.gguf` | Local LLM for extraction |
| `DEFAULT_SENTENCE_MODEL` | `all-MiniLM-L6-v2` | Embedding model for matching |

## License

See `LICENSE` — free for educational / non-profit use; commercial use requires a separate license.

## Troubleshooting

**"App won't start / ModuleNotFoundError"**
- Ensure you installed with `uv pip install -e .` (not just `uv add`). This registers the `src/` package correctly.

**"No jobs appear in the list"**
- The Chrome Extension must post to `http://localhost:8080/api/v1/jobs/capture`.
- Check the app log for `INFO infrastructure.api.routers.jobs: Captured job N`.

**"Extraction returns empty fields"**
- The first run downloads the 1.8 GB Qwen2.5-3B GGUF model — wait for the download to finish.
- The model processes long postings in overlapping chunks; extraction of 2–3 chunk jobs may take 15–30 seconds.

**"Match score is 0.0"**
- Upload a resume first (Job Detail → Upload Resume). The score requires a resume in the database.

**"Email draft shows placeholder text"**
- Ensure a resume has been uploaded and parsed. The EmailComposer extracts skills from the resume to personalise the draft.
