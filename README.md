# WDL2Doc

Generate documentation and visual diagrams for WDL (Workflow Description Language) files.

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
            taniguti/wdl2docs:0.1.0 generate /data -o /output

# Generate graph
docker run  --user $(id -u):$(id -g) --rm \
            -v /path/to/wdl-project:/data \
            -v $(pwd)/output:/output \
            taniguti/wdl2docs:0.1.0 graph /data/workflow.wdl -o /output/graph.md
```

## Usage

WDL2Doc provides two main commands:

### 1. Generate HTML Documentation

Generate complete HTML documentation for your WDL project:

```bash
wdl2doc generate /path/to/wdl-project -o docs/
```

### 2. Generate Workflow Graph

Generate a Mermaid diagram for a specific workflow:

```bash
wdl2doc graph workflow.wdl -o workflow_graph.md
```

## Features

- 📚 Complete HTML documentation with navigation
- 📊 Interactive workflow diagrams (Mermaid)
- 🐳 Docker image inventory
- 🔗 Cross-references between workflows and tasks
- 📦 External dependency tracking

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
