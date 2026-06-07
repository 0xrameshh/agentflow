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
COPY scripts/docker_entrypoint.sh /app/docker_entrypoint.sh

# Install the project
RUN uv sync --no-dev
RUN chmod +x /app/docker_entrypoint.sh

EXPOSE 8081

CMD ["/app/docker_entrypoint.sh"]
