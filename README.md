# WDL2Doc

Generate documentation and visual diagrams for WDL (Workflow Description Language) files.

![Python](https://img.shields.io/badge/python-3.12+-green)
![WDL](https://img.shields.io/badge/WDL-1.0+-blue)

## Installation

```bash
pip install -e .
```

Or using `uv`:
```bash
uv sync
```

### Docker

Build the image:
```bash
docker build -t wdl2doc .
```

Run with Docker:
```bash
mkdir output
# Generate documentation
docker run  --user $(id -u):$(id -g) --rm -v /path/to/wdl-project:/data -v $(pwd)/output:/output wdl2doc generate /data -o /output

# Generate graph
docker run  --user $(id -u):$(id -g) --rm -v /path/to/wdl-project:/data -v $(pwd)/output:/output wdl2doc graph /data/workflow.wdl -o /output/graph.md
```

## Usage

WDL2Doc provides two main commands:

### 1. Generate HTML Documentation

Generate complete HTML documentation for your WDL project:

```bash
wdl2doc generate /path/to/wdl-project -o docs/
```

**Options:**
- `-o, --output PATH` - Output directory (default: `docs/wdl`)
- `-e, --exclude PATTERN` - Patterns to exclude (repeatable)
- `--external-dirs NAME` - Directories to treat as external (default: `external`)
- `-v, --verbose` - Enable verbose logging

**Example:**
```bash
wdl2doc generate . -o docs/ --exclude "test_*" --verbose
```

### 2. Generate Workflow Graph

Generate a Mermaid diagram for a specific workflow:

```bash
wdl2doc graph workflow.wdl -o workflow_graph.md
```

**Options:**
- `-o, --output PATH` - Output Markdown file (required)
- `-v, --verbose` - Enable verbose logging

**Example:**
```bash
wdl2doc graph workflows/analysis.wdl -o docs/analysis_graph.md
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
uv run pytest
```

Check types:
```bash
make typecheck
```

## Project Structure

```
src/
├── cli/                 # Command-line interface
├── domain/              # Domain models
├── application/         # Use cases
└── infrastructure/      # Parsers, renderers, repositories
```
