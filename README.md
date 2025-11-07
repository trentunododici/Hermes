# Hermes

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Hermes
```

2. Install dependencies with uv:
```bash
uv sync
```

This command automatically creates a `.venv` virtual environment and installs all dependencies specified in `pyproject.toml`.

## Running the server

To start the FastAPI development server:

```bash
uv run uvicorn src.main:app --reload
```

The server will be available at `http://localhost:8000`

### Available endpoints

- `GET /` - Test endpoint
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - Alternative ReDoc documentation

## Development

To install development dependencies (pytest, black, ruff):

```bash
uv sync --all-groups
```

### Linting and formatting

```bash
# Format with black
uv run black src/

# Lint with ruff
uv run ruff check src/
```

### Testing

```bash
uv run pytest
```
