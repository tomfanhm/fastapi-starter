# Stage 1: Build
FROM python:3.12-slim AS build

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.4

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry: create virtualenv in project directory
RUN poetry config virtualenvs.in-project true \
    && poetry install --only main --no-root --no-interaction

# Copy application source
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

# Copy virtualenv and application from build stage
COPY --from=build /app/.venv .venv
COPY --from=build /app/app app
COPY --from=build /app/alembic alembic
COPY --from=build /app/alembic.ini .

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:create_app", "--factory", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
