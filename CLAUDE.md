# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

3D-Lab is a Spanish-language marketing/commercial platform for an additive-manufacturing (3D printing) shop: a service catalog, a material selection guide (explore/compare/detail), an anonymous quote-request flow with STL uploads, and a single-admin back office. Full product spec lives in [AGENTS.MD](AGENTS.MD) — read it before implementing any feature; it defines scope, statuses, retention rules, roles, and what is explicitly out of scope for the MVP (no payments, no AI, no CRM/WhatsApp integration, no client accounts). [docs/constitution.md](docs/constitution.md) has the six non-negotiable project principles.

## Commands

Run everything from `backend/` (that's where `pyproject.toml` and `pytest.ini` live):

```powershell
cd backend
python -m venv ../.venv          # once
../.venv/Scripts/pip install -e ".[dev]"

uvicorn src.main:app --reload    # dev server, http://127.0.0.1:8000
python -m src.seed               # seed services/materials/admin user (idempotent)
python -m src.worker             # runs the notification + STL-retention jobs once (cron target)

pytest                           # full suite
pytest -m unit                   # single marker: unit | integration | e2e | security | performance
pytest tests/unit/quotes/test_confirm_quote.py::test_name   # single test

ruff check .
ruff format --check .
```

There is no `requirements-dev.txt` and no root `package.json` — ignore any instructions referencing them. `alembic upgrade head` (from `backend/`) applies migrations; the Docker image runs it automatically on container start. Tests need a reachable PostgreSQL for anything beyond `unit` (`DATABASE_URL`, see `.env.example`).

## Architecture

Clean Architecture, but organized **per bounded context**, not as one top-level `domain/application/infrastructure/presentation` split (that diagram in AGENTS.md's "Estructura esperada" is aspirational — the real layout below is authoritative). Each context under `backend/src/` (`catalog`, `materials`, `quotes`, `customers`, `administration`, `notifications`, `retention`, `reporting`, `audit`, `shared`) has its own:

```
<context>/
├── domain/          # entities, value objects — no framework/infra imports
├── application/      # use cases as frozen dataclasses with an .execute(); ports as Protocols
├── infrastructure/    # SQLAlchemy repositories, gateways, storage
└── presentation/      # FastAPI routers, Jinja2 template wiring
```

Two rules are enforced by `backend/tests/architecture/test_dependencies.py` and will fail CI if violated:
- nothing under `*/domain/*.py` may import `fastapi`, `sqlalchemy`, `starlette`, or any `*.infrastructure` module.
- nothing under `*/presentation/*.py` may reference `SessionFactory`, `.commit(`, or `.rollback(` — transaction boundaries belong to the unit of work in `infrastructure` (see `quotes/infrastructure/unit_of_work.py`), not to routes.

Routers are composed in `backend/src/main.py::create_app`. A typical use case (e.g. `quotes/application/confirm_quote.py::ConfirmQuote`) takes a `QuoteSubmissionUnitOfWork` Protocol plus injected `Clock`/`TokenFactory`/etc. (see `shared/domain/types.py`) so tests can supply fakes without touching a database.

**Templates & static assets**: server-rendered Jinja2 views live in `frontend/src/views/` (mapped via `shared/presentation/templates.py`, resolved relative to the repo root, not `backend/`) and are served alongside `frontend/src/{scripts,styles,Resources}` mounted at `/static` (`main.py`). There is no JS build step — `frontend/src/scripts/*.js` is loaded directly.

**Async work**: emails and STL expiry are not handled inline in the request — a use case appends to an outbox/notification table, and `src/worker.py` (invoked periodically, e.g. every 5 min via cron in Dokploy — see [docs/deployment-dokploy.md](docs/deployment-dokploy.md)) delivers/reaps them. Don't wire SMTP or file deletion into a request handler.

**Config**: `shared/config.py::get_settings()` reads env vars once (`lru_cache`); it hard-fails if `APP_SECRET_KEY` is short in `APP_ENV=production`. See `.env.example` for the full variable list.

## Conventions

- Identifiers and code comments in English; anything user-facing (UI copy, validation/error messages, email templates) in Spanish — see `shared/presentation/messages.py` and `notifications/presentation/templates/`.
- Every async UI operation should represent `loading`/`success`/`empty`/`error` states explicitly (see `MESSAGES` dict usage in `catalog/presentation/routes.py` for the pattern of falling back to a message + non-200 status rather than raising).
- Quote statuses are fixed to `abierta`, `en_proceso`, `entregada`, `cerrada` (`quotes/domain/status.py`) — don't add states without updating [AGENTS.MD](AGENTS.MD) first.
- `UI_STYLE_GUIDE.md` at the repo root describes a Tailwind-based palette/button system that does **not** match this project's actual stack (plain CSS custom properties in `frontend/src/styles/base.css`, no Tailwind anywhere in `frontend/`). Treat only its color values (navy `#0B192C`, slate, blue `#0284C7`) as current; ignore the Tailwind class examples.
- `specs/001-3D-Lab/` holds the spec-kit artifacts (`spec.md`, `plan.md`, `tasks.md`, evidence/checklists) generated by the `speckit-*` skills under `.agents/skills/`.
