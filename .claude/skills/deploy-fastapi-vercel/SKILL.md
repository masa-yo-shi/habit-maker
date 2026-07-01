---
name: deploy-fastapi-vercel
description: Set up and deploy the habit-maker FastAPI backend to Vercel as a serverless Python function (vercel.json, requirements.txt, .vercelignore, SQLite-on-readonly-fs fix). Use when the user asks to deploy this app to Vercel, set up a Vercel config, or debug a Vercel build/runtime failure for this backend.
---

# Deploy habit-maker FastAPI backend to Vercel

Base approach adapted from https://zenn.dev/yuri_kurashima/articles/2faf67bbc5c4e4 (generic FastAPI-on-Vercel guide), adjusted for this repo's actual layout — the article's directory structure (root-level `app.py`) does not match this project.

## Repo facts that change the generic recipe

- App object lives at `backend/main.py` (`app = FastAPI(...)`), not a root `app.py`. `vercel.json` must point at `backend/main.py`.
- Dependencies are declared in root `pyproject.toml` ([project] / dependencies), no `requirements.txt` or lock file exists. Vercel's `@vercel/python` runtime installs from `requirements.txt`, so one must be generated.
- `requires-python = ">=3.12"` in pyproject.toml → use `"runtime": "python3.12"` in vercel.json (the article uses 3.9; that's stale for this repo).
- `backend/db.py` opens a SQLite file at `backend/habit_maker.db` via aiosqlite. **Vercel's Lambda filesystem is read-only except `/tmp`.** Without a fix, `init_db()`'s `create_all` will raise `sqlite3.OperationalError: unable to open database file` on first request and the deploy will be unusable. This must be patched (see step 3) — it is not just a "data won't persist" caveat, it's a hard crash.
- `backend/templates/` (Jinja templates + `partials/`) must ship in the bundle — do not exclude it in `.vercelignore`.
- No WebSocket usage in this codebase, so the article's "no WebSocket support" limitation doesn't block anything here.

## Steps

1. **Generate `requirements.txt` at repo root** from pyproject.toml's dependency list (fastapi, uvicorn, sqlalchemy, aiosqlite, pydantic, pydantic-settings, jinja2, pwdlib, pyjwt). Pin versions from the active environment if possible (`pip freeze` inside the project venv), otherwise list unpinned names.

2. **Create `vercel.json` at repo root:**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "backend/main.py",
         "use": "@vercel/python",
         "config": { "runtime": "python3.12" }
       }
     ],
     "routes": [
       { "src": "/(.*)", "dest": "backend/main.py" }
     ]
   }
   ```

3. **Fix `backend/db.py` so the DB path is writable on Vercel.** Vercel sets the `VERCEL` env var at runtime. Change `DB_PATH` to fall back to `/tmp` there:
   ```python
   import os
   BASE_DIR = os.path.dirname(__file__)
   DB_PATH = os.path.join("/tmp", "habit_maker.db") if os.environ.get("VERCEL") else os.path.join(BASE_DIR, "habit_maker.db")
   ```
   Tell the user explicitly: `/tmp` is wiped on cold start, so habit/diary data will NOT persist between deploys or scale-to-zero cycles. This is fine for a demo but not for real usage — if they want persistence, point them at a hosted DB (e.g. Postgres on Neon/Supabase, or Turso for SQLite-compatible) instead of file-based SQLite, and swap `DATABASE_URL` accordingly. Don't make that switch unless asked — just flag it.

   **Status (2026-07-01): this has been done.** `backend/db.py` now reads a Postgres URL from env (`DATABASE_URL`/`POSTGRES_URL`/non-pooling variants), normalizes to `postgresql+asyncpg://`, and only falls back to `/tmp` SQLite when no such env var is set. Prod is on **Neon Postgres** (Marketplace integration `neon-camel-lever`, connected to the project → env vars auto-injected). To (re)provision from the CLI: `vercel integration add neon -e production` (requires one-time browser terms acceptance first; the CLI prints the `accept-terms` URL). See the `vercel-needs-external-db` memory.

4. **Create `.vercelignore` at repo root** — exclude dev/test cruft, keep templates:
   ```
   .git
   .venv
   venv
   __pycache__
   *.db
   .pytest_cache
   backend/test
   ```

5. **Local sanity check before deploying:** confirm `backend/main.py` still imports cleanly and `uvicorn backend.main:app` (or the project's normal run command) still boots after the db.py change — the conditional should be a no-op locally since `VERCEL` won't be set.

6. **Deploy is a visible, hard-to-reverse action against an external service — confirm with the user before running it.** Once confirmed:
   ```bash
   npm i -g vercel   # if not already installed
   vercel login      # interactive; ask the user to run this themselves if not already authenticated
   vercel            # preview deploy
   vercel --prod     # production deploy, only after preview looks right
   ```

7. **Post-deploy verification:** hit `https://<project>.vercel.app/` and `https://<project>.vercel.app/docs` (Swagger UI) to confirm the function boots and routes resolve.

## Troubleshooting post-deploy runtime 500s (`FUNCTION_INVOCATION_FAILED`)

A **successful build** can still 500 on every request because the failure is at *import/startup* time, not build time. `vercel ls` shows the deployment as `● Ready` while the site is fully down. Diagnose it like this:

1. **Find the real production URL.** The alias domain (e.g. `habit-maker-nu.vercel.app`) is what the user hits — a fresh `<hash>-<team>.vercel.app` deployment URL may respond differently. `vercel inspect <url>` lists the aliases.
2. **Get the full traceback.** The human-readable `vercel logs <url>` output **truncates the message** (`could not import "backend…`) and often only shows `Python process exited with exit status: N`. Use JSON to get the whole thing:
   ```bash
   curl -s https://<prod-domain>/ > /dev/null   # trigger a fresh invocation first
   vercel logs https://<prod-domain> --json | python3 -c "import sys,json; [print(json.loads(l)['message'][:2000]) for l in sys.stdin if l.strip()]"
   ```
3. **Reproduce locally against the real prod env** when logs are still opaque (`exit status: 0/1` with no trace). Pull prod env and run `init_db` in a throwaway venv — this surfaces the actual `Traceback`:
   ```bash
   vercel env pull prod.env --environment=production
   # venv + pip install -r requirements.txt, then:
   DATABASE_URL="$(grep ^DATABASE_URL= prod.env|cut -d= -f2-|tr -d '\"')" VERCEL=1 SECRET_KEY=x \
     python -c "import asyncio,db; asyncio.run(db.init_db(seed_sample=True, reset=False))"
   ```

### Concrete causes seen on this repo (2026-07-01)

- **`RuntimeError: SECRET_KEY is not set` → whole app 500s.** `backend/auth.py` raises **at import time** when `VERCEL` is set but no `SECRET_KEY` env var exists (added in commit `bcb72a5`). Since `main.py` imports the routers which import `auth`, the module fails to load and *every* route 500s. **Fix:** set the env var, then redeploy (env changes don't apply to existing deployments):
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(48))" | vercel env add SECRET_KEY production
  vercel redeploy https://<prod-domain>          # re-alias with the new env
  ```
  Verify: `/` → 302/303 to login, `/login-page` → 200, `POST /login` (demo/demopassword) → 200 + `access_token` cookie.

- **`asyncpg ... DataError: can't subtract offset-naive and offset-aware datetimes` on insert/seed.** A model column typed `DateTime` (→ Postgres `TIMESTAMP WITHOUT TIME ZONE`) receives a **tz-aware** value (`datetime.now(timezone.utc)`). SQLite silently accepts this; asyncpg rejects it. **Fix:** the column must be `DateTime(timezone=True)` (see the `postgres-timestamptz-gotcha` memory). After changing the model, the *already-created* Postgres column keeps its old type — recreate it (`DROP TABLE ... CASCADE` + `create_all`, or full reset) since `create_all` never alters existing columns. Keep column tz-ness consistent with what the writers produce (`CalendarMemo.updated_at` uses naive `utcnow()`, so plain `DateTime` is correct there).

- **`relation "users" does not exist` right after `create_all` on a fresh Neon DB.** Neon's **pooled** endpoint (the default `DATABASE_URL`, via pgbouncer) had a DDL-visibility lag: `create_all` then an immediate seed query in the same `init_db` run couldn't see the new tables. Work around by **pre-creating the schema once** (run `init_db`/`create_all` out-of-band, e.g. locally, before relying on cold-start init). Note the non-pooling endpoint (`POSTGRES_URL_NON_POOLING`) timed out from a local WSL run; the pooled `DATABASE_URL` is fast and fine for normal queries and one-off DDL from a standalone script.

### General reminders
- **Env var changes require a redeploy** (`vercel redeploy <url>` re-aliases the existing build with new env; `vercel deploy --prod` ships new *code*). To push a code fix you must `vercel deploy --prod` — `redeploy` reuses the old bundle.
- After any fix, verify against the **alias domain**, not just the new deployment URL.

## Known platform limits (carried over from the article)

- Cold starts after idle periods.
- Hobby plan execution-time limits per invocation.
- No WebSocket support (not currently used by this app, but relevant if added later).
