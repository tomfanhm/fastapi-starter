# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
make install          # poetry install

# Run dev server (auto-reload)
make run              # uvicorn app.main:create_app --factory --reload

# Tests
make test             # pytest --cov=app --cov-report=term-missing
poetry run pytest tests/test_auth.py -k "test_register" -v  # single test

# Linting & formatting
make lint             # ruff check + ruff format --check + mypy
make format           # ruff format (auto-fix)

# Database migrations
make migrate          # alembic upgrade head
make migration        # alembic revision --autogenerate -m "description"

# Docker
make docker-up        # docker compose up -d --build (runs migrations on start)
make docker-down      # docker compose down (preserves volumes)
make docker-nuke      # docker compose down -v (destroys volumes)
```

## Architecture

Layered async FastAPI app: **Routes → Services → Models → PostgreSQL**

- **`app/main.py`** — App factory (`create_app()`) with lifespan, middleware registration, exception handlers
- **`app/core/config.py`** — Pydantic `BaseSettings` loaded from `.env`, cached via `lru_cache` in `get_settings()`. Rejects default JWT secret in non-dev environments.
- **`app/core/database.py`** — Lazy-initialized async engine via `init_engine()` (called in lifespan). `Base` provides auto `id` (UUID), `created_at`, `updated_at`.
- **`app/core/security.py`** — JWT creation/verification (PyJWT HS256), bcrypt password hashing (direct bcrypt lib)
- **`app/api/v1/`** — Versioned routes under `/api/v1`. Router aggregated in `router.py`
- **`app/services/`** — Business logic layer; services use `flush()` (not `commit()`). Transaction boundary is in `get_db()`.
- **`app/schemas/`** — Pydantic v2 request/response schemas (separate from ORM models)
- **`app/models/`** — SQLAlchemy ORM models inheriting from Base (which adds id, timestamps)
- **`app/exceptions/handlers.py`** — `AppException` hierarchy (`NotFoundException`, `ConflictException`, `UnauthorizedException`, `ForbiddenException`) with global handlers returning `{"error": "CODE", "detail": "message"}`
- **`app/middleware/`** — CORS, request logging with `X-Process-Time` header

## Auth Flow

- `POST /api/v1/auth/register` (JSON body) → creates user → returns JWT. Password must be 8-128 chars.
- `POST /api/v1/auth/login` (OAuth2 form-encoded) → validates credentials → returns JWT
- Protected routes use `Depends(get_current_user)` which extracts user from Bearer token and checks `is_active`

## Database Dependency

`get_db()` async generator yields `AsyncSession` with commit-on-success, rollback-on-failure. Services should use `flush()`, not `commit()`. Override in tests via `app.dependency_overrides[get_db]`.

## Testing

Tests use in-memory SQLite async (aiosqlite) — no PostgreSQL needed. Fixtures in `tests/conftest.py`:
- `db_engine` / `db_session` — ephemeral in-memory SQLite with table create/drop per test
- `async_client` — httpx `AsyncClient` with dependency overrides for DB and settings
- `test_user` / `auth_headers` — pre-created user with valid JWT
- `admin_user` / `admin_headers` — admin role user for admin-only endpoint tests
- `inactive_user` / `inactive_headers` — deactivated user for `is_active` enforcement tests

## Code Style

- **Ruff**: line length 120, target Python 3.12, strict rule set (E/F/W/I/N/UP/ANN/B/A/SIM/TCH/RUF)
- **Mypy**: strict mode with `pydantic.mypy` and `sqlalchemy.ext.mypy.plugin`
- All async — use `AsyncSession`, `await` for DB operations, `async def` for route handlers
