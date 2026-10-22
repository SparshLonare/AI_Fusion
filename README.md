# AI Code Explainer & Debugging Assistant

A Django app that uses Gemini and a local ChromaDB knowledge base to explain code problems, identify issues, and suggest corrected code. It retrieves relevant passages from the indexed programming references and shows the sources alongside the answer. Submitted code is analyzed as text and is never executed.

The editor supports Python, Java, C, C++, and SQL. The repository includes reference PDFs for each language under `kb_seed/`.

## Features

- Explain a code snippet and a problem description, with issue details and corrected code.
- Retrieve documentation passages from PDF and TXT files and show source, page, and similarity.
- Upload PDF/TXT references (up to 10 MB per file) to the knowledge base.
- Save and revisit recent explanations through the search history.
- Use a responsive interface with dark/light themes.

## Requirements

- Python 3.11 or newer
- A Gemini API key from Google AI Studio

## Run locally (Windows PowerShell)

```powershell
git clone https://github.com/SparshLonare/AI_Fusion.git
cd AI_Fusion
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY = "your-gemini-api-key"
python manage.py migrate
python manage.py seed_kb
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Keep your API key in an environment variable; never commit it to Git.

`seed_kb` reads each PDF and TXT file in `kb_seed/`, embeds its text with Gemini, and stores the chunks in `chroma_db/`. Ingestion and code explanations require `GEMINI_API_KEY` and make requests to the Gemini API.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Web interface |
| `POST` | `/api/explain/` | Explain JSON `{ "code": "...", "problem": "..." }` |
| `POST` | `/api/upload/` | Ingest a multipart PDF/TXT file in the `file` field |
| `GET` | `/api/files/` | List indexed source filenames |
| `GET` | `/api/history/` | List recent explanations |
| `POST` | `/api/history/` | Save an explanation to history |
| `GET` | `/api/history/<id>/` | Load a saved explanation |

## Deploy on Render

The repository includes a `render.yaml` Blueprint configured for Render's Free web-service plan. In Render, choose **New → Blueprint**, connect this repository on the `master` branch, enter `GEMINI_API_KEY` when prompted, and apply the Blueprint. The build seeds the bundled references and collects static files.

Render Free services can sleep when idle and use temporary local storage. Uploaded documents and SQLite search history may be lost after a restart, sleep, or redeploy. The bundled references are re-indexed on each build. Seeding also uses Gemini API quota, which is separate from Render hosting. See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for details.

## Project layout

```text
codehelper/   Django project settings and URLs
core/         Django app, views, history model, and RAG logic
kb_seed/      Bundled programming reference PDFs
templates/    Web interface
render.yaml   Render Blueprint
```
