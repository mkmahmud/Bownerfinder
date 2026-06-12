# Local Business Decision Maker Finder

Self-hosted lead enrichment application. Phase 1 implements project setup,
upload validation, durable jobs, database schema, API routes, frontend upload
flow, Docker Compose, migrations, and tests.

## Phase 1 Features

- CSV and XLSX upload endpoint.
- Required `business_name` validation.
- Optional `website`, `phone`, `email`, `linkedin`, `facebook`, `instagram`
  columns.
- Company-name normalization for common legal suffixes.
- SQLite local default with PostgreSQL support through `DATABASE_URL`.
- SQLAlchemy models for `companies`, `contacts`, `jobs`, `evidence`, and
  `exports`.
- Alembic migration for the Phase 1 schema.
- Next.js 15 upload page, dashboard, jobs list, job detail, results, and
  settings pages.
- Docker Compose with frontend, backend, PostgreSQL, and Redis.

## Backend

```bash
cd backend
if not exist .venv (python -m venv .venv)
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

If `.venv` already exists, do not recreate it. If Windows reports a permission error for `.venv\Scripts\python.exe`, create a fresh environment with a different name, for example `python -m venv .venv-local`, then activate `.venv-local\Scripts\activate` instead.

API documentation is available at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000/upload`.

Ollama is optional for local development. If it is not running, the app falls back to deterministic ranking for enrichment and still works.

If you want LLM ranking, install Ollama, start the Ollama server, and pull a model such as `qwen3` or `llama3` before clicking re-enrich.

Example:

```bash
ollama serve
ollama pull qwen3
```

## Docker

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Tests

```bash
cd backend
pytest
```

## Upload Format

Required column:

- `business_name`

Optional columns:

- `website`
- `phone`
- `email`
- `linkedin`
- `facebook`
- `instagram`

Rows missing `business_name` are rejected and reported in the upload response.
Valid rows are saved to the `companies` table under the created job.

