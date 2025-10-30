# WDL Atlas

Explore and visualize your WDL (Workflow Description Language) workflows

![Python](https://img.shields.io/badge/python-3.13-green)
![WDL](https://img.shields.io/badge/WDL-blue)

## Installation

```bash
pip install -e .
```

Or using `uv`:
```bash
uv sync
```

### Docker

Run with Docker:
```bash
# Create a directory with your user permissions
mkdir output

# Generate documentation
docker run  --user $(id -u):$(id -g) --rm \
            -v /path/to/wdl-project:/data \
            -v $(pwd)/output:/output \
            taniguti/wdlatlas:0.1.0 generate /data -o /output

# Generate graph
docker run  --user $(id -u):$(id -g) --rm \
            -v /path/to/wdl-project:/data \
            -v $(pwd)/output:/output \
            taniguti/wdlatlas:0.1.0 graph /data/workflow.wdl -o /output/graph.md
```

## Usage

WDL Atlas provides two main commands:

### 1. Generate HTML Documentation

Generate complete HTML documentation for your WDL project:

```bash
wdlatlas generate /path/to/wdl-project -o docs/
```

### 2. Generate Workflow Graph

Generate a Mermaid diagram for a specific workflow:

```bash
wdlatlas graph workflow.wdl -o workflow_graph.md
```

## Features

- 📚 Complete HTML documentation with navigation
- 📊 Interactive workflow diagrams (Mermaid)
- 🐳 Docker image inventory
- 🔗 Cross-references between workflows and tasks
- 📦 External dependency tracking

## Viewing Generated Documentation

⚠️ **Important**: The generated HTML documentation uses ES6 modules, which require a web server to work properly due to CORS restrictions.

**You cannot simply open `index.html` directly in your browser** (using `file://` protocol). Instead, use one of these options:

### Option 1: Built-in Server Script (Easiest)

```bash
python serve_docs.py
# or specify a different port
python serve_docs.py 8080
```

This will automatically:
- Start a local HTTP server
- Open your browser at the correct URL
- Serve the documentation from the `docs/` directory

### Option 2: Python HTTP Server

```bash
cd docs
python -m http.server 8000
```

Then open: http://localhost:8000

### Why is this necessary?

Modern browsers enforce strict CORS (Cross-Origin Resource Sharing) policies for ES6 modules. When opening files directly (`file://` protocol), the browser blocks module imports for security reasons. A local HTTP server provides the necessary CORS headers to allow module loading.

## Development

Run tests:
```bash
uv run pytest -v --cov=src tests --cov-report=term
# or 'make test'
```

## Project Structure

```
src/
├── cli/                 # Command-line interface
├── domain/              # Domain models
├── application/         # Use cases
└── infrastructure/      # Parsers, renderers, repositories
```
