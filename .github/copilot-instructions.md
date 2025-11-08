## Repo snapshot (short)

- Backend: Django project under `src/` (settings in `src/config/settings.py`, URLs in `src/config/urls.py`).
- Services: each domain lives as a Django app in `src/services/*` (e.g. `chatbot_service`, `ai_recommendations`, `blockchain_service`).
- Frontend: A simple static prototype exists in `frontend-simple/` and is served by Django templates during dev.
- AI/Vector store: `chroma_db/` (Chroma vector DB used by `src/services/chatbot_service/rag_engine.py` and `src/shared/utils.py`).

## Primary patterns & conventions an agent should follow

- Service layout: every `src/services/<name>/` is a self-contained Django app exposing `urls.py`, `views.py`, `models.py`, `serializers.py`, and `tests.py`. When adding endpoints, wire them through `src/config/urls.py` under `api/v1/<route>/`.
- Auth: JWT via `rest_framework_simplejwt`. Token endpoints live at `api/v1/auth/token/` and `api/v1/auth/token/refresh/`. Default DRF permission is `IsAuthenticated` (see `REST_FRAMEWORK` in `src/config/settings.py`) — remember to expose public endpoints or relax permissions intentionally.
- Background tasks: Celery is configured (see `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` in `src/config/settings.py`). Broker defaults to Redis. Typical dev commands: start Redis, run `celery -A src worker -l info` and `celery -A src beat -l info`.
- AI integrations: RAG and embeddings use Google GenAI through langchain wrappers (`langchain_google_genai`) and Chroma from `langchain_community`. Look at `src/services/chatbot_service/rag_engine.py` and `src/shared/utils.py` for concrete usage patterns (embeddings model names, vectorstore persistence, session history via Redis).
- Data & env: Default DB is SQLite (`db.sqlite3`) in dev. Production/postgres options are commented in `src/config/settings.py`. Environment-driven config is used heavily (e.g., `DJANGO_SECRET_KEY`, `STRIPE_SECRET_KEY`, `WEB3_*`, `GOOGLE_API_KEY`, `CELERY_*`).

## How to run and debug (developer workflows)

- Backend (dev): from repository root run:

  - Ensure Python deps installed (see `requirements.txt`) and virtualenv active.
  - Run migrations and dev server:

    - `python src/manage.py migrate`
    - `python src/manage.py runserver`

  - Run tests:
    - `python src/manage.py test` (Django tests live in each service `tests.py`).

- Frontend (dev):

  - `cd frontend`
  - `npm install`
  - `npm run dev` (Vite dev server)
  - The backend allows CORS for common local ports; see `CORS_ALLOWED_ORIGINS` in `src/config/settings.py`.

- Celery (background jobs): ensure `CELERY_BROKER_URL` points to a running Redis, then:
  - `celery -A src worker -l info`
  - `celery -A src beat -l info` (for scheduled tasks)

## Important project-specific caveats (do not change without care)

- Chroma persistence: `rag_engine.py` rebuilds the `chroma_db` directory when initialized (it deletes then recreates). Avoid deleting or replacing `chroma_db/` unless reindexing is intended.
- LLM / embeddings: concrete model names and usage are hard-coded in `rag_engine.py` (e.g., `models/embedding-001`, `gemini-2.0-flash-exp`). Replacing providers requires corresponding code changes in `src/shared/utils.py` and RAG engine usage.
- JWT & DRF defaults: Many endpoints assume authenticated requests. If you add public APIs, explicitly set permissions in the view or serializer.
- Templates: `frontend-simple/` is referenced in `TEMPLATES['DIRS']` — it's used for quick prototype pages served by Django; changes here affect what `runserver` serves for non-SPA pages.

## Useful file references (examples to open quickly)

- `src/config/settings.py` — environment flags, DB, Celery, Stripe, blockchain RPCs, Google API key.
- `src/config/urls.py` — main route map; services are included under `api/v1/<service>/`.
- `src/services/chatbot_service/rag_engine.py` — RAG, Chroma, embeddings and conversational flow.
- `src/services/ai_recommendations/recommendation_engine.py` — hybrid recommendation logic and caching patterns.
- `src/shared/utils.py` — small helpers (email, formatters) and langchain imports used across services.
- `frontend/` — Vite + React app; entry is `frontend/src/index.jsx` and `frontend/package.json` contains run/build scripts.

## When you (the agent) modify code, prefer these small, safe patterns

- Add endpoints: create `views.py` -> `serializers.py` -> `urls.py` in the service folder and register in `src/config/urls.py` under `api/v1/`.
- Tests: add a small `tests.py` test inside the service to validate new endpoint logic before pushing changes.
- Config changes: always prefer environment variables for secrets and service URLs; update `src/config/settings.py` default fallbacks only when necessary.

## Quick checklist for PRs an agent might author

1. Does the change add/modify an API? Update `src/config/urls.py` and add an entry in the matching `src/services/*/urls.py`.
2. Has authentication or permissions changed? Verify `REST_FRAMEWORK` settings or per-view `permission_classes`.
3. If adding background work, add Celery tasks and document required broker settings.
4. Add a minimal test in the service `tests.py` and ensure `python src/manage.py test` passes.

---

If any of the above sections are unclear or you want more detail (example PR templates, lint/test commands, or a short onboarding script), tell me which part to expand and I'll iterate.
