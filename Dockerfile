FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev --no-install-project

# Copy source
COPY src/ src/
COPY data/ data/
COPY eval/ eval/

# Install the project
RUN uv sync --no-dev

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "agentflow.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
