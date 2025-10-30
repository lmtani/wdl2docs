FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install --system --no-cache -e .

# Set the entrypoint to the wdlatlas command
ENTRYPOINT ["wdlatlas"]

# Default command shows help
CMD ["--help"]
