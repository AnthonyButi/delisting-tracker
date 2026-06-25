# Project Progress Log

A running, module-by-module record of what's been built and how.

## Module 0 — Foundations & setup ✅
- Created the project folder and an isolated virtual environment (`.venv`) so project packages stay separate from system Python.
- Installed core dependencies (`pandas`, `requests`, `python-dotenv`) and pinned them in `requirements.txt` for reproducibility.
- Initialized git and wrote `.gitignore` excluding `.venv/`, `.env`, `__pycache__/`, `*.sqlite`.
- Got a free FRED API key; stored it privately in `.env` (never committed).
- Verified the key loads via `load_dotenv()` + `os.getenv()` (`check_setup.py` → "Key loaded!").
- First commit, pushed to GitHub via the GitHub CLI. Confirmed `.env` is absent from the remote.

## Module 1 — APIs & data ingestion ✅
- Learned a REST API call is just a URL: endpoint + query params (`series_id`, `api_key`, `file_type`).
- Built `fred_client.py` with `get_series_raw` (calls FRED, raises on errors, returns JSON) and `get_series` (shapes raw observations into a tidy date-indexed DataFrame; converts values with `errors="coerce"` so missing "." markers become NaN).
- Verified it's generic across geographies (Chicago metro `ACTLISCOU16980`, national `ACTLISCOUUS`).

## Module 2 — Merge metrics into one panel ✅
- Added `get_panel(series_ids)` — joins several series on the date index, skipping any that fail to fetch (resilient ingestion).
- Added `build_panel(cbsa_code)` — assembles the full monthly panel (active, new, pending, price-reduced + 30-yr mortgage rate) for any metro; mortgage is weekly/national so it's resampled to monthly before joining.
- Output: 119 aligned months, 5 columns. Confirmed Chicago publishes pending data (central to the delisting calc).

## Module 3 — Storage (SQLite) ✅
- Added `storage.py` with `init_db`, `save_panel`, `load_panel`.
- Long-format schema `(date, series_id, value)` with `PRIMARY KEY (date, series_id)`.
- `INSERT OR REPLACE` upserts make writes idempotent — re-running updates rows instead of duplicating them.

## Tooling
- Editing in Cursor with the Microsoft Python extension and the `.venv` interpreter.
- Git rhythm: `git add .` → `git commit -m "..."` → `git push`.