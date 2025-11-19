# Hermes

Backend API for the app built with FastAPI, PostgreSQL, and Docker.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://www.docker.com/) and Docker Compose
- PostgreSQL (via Docker)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Hermes
```

### 2. Setup Environment Variables

Create the `.env` file from the template:

```bash
cp .env.example .env
```

Update the `.env` file with your configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://hermes_user:hermes_password@localhost:5432/hermes

# Security - IMPORTANT: Generate a new SECRET_KEY for production!
SECRET_KEY=$(openssl rand -hex 32)  # Generate a secure key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENV=development
```

### 3. Start PostgreSQL with Docker

```bash
docker-compose up -d
```

This command will:

- Download the PostgreSQL 16 image
- Create the `hermes` database
- Expose PostgreSQL on `localhost:5432`
- Persist data in the `postgres_data` volume

Verify that PostgreSQL is ready:

```bash
docker ps  # You should see hermes_postgres with "healthy" status
```

### 4. Install Python Dependencies

```bash
uv sync
```

This command automatically creates a `.venv` virtual environment and installs all dependencies.

### 5. Run the Application

```bash
uv run uvicorn src.main:app --reload
```

The application will be available at `http://localhost:8000`

On first startup, FastAPI will automatically create all database tables.

### Available Endpoints

- `GET /health` - Health check for API and database
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - Alternative ReDoc documentation
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/token` - Get access token (OAuth2)
- `GET /api/v1/users/me` - Current user information (requires authentication)

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

The project includes a comprehensive test suite with both unit and integration tests.

#### Running Tests Locally

```bash
# Run all tests (automatically starts test database)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_auth.py

# Run specific test class
uv run pytest tests/test_auth.py::TestLogin

# Run only unit tests
uv run pytest tests/unit/
```

The test suite automatically:
1. Starts a PostgreSQL container via `docker-compose.test.yaml` (port 5433)
2. Creates test database and tables
3. Runs all tests with transaction isolation
4. Stops and removes the container

#### Test Structure

```text
tests/
├── conftest.py          # Shared fixtures
├── test_config.py       # Test environment variables
├── test_auth.py         # Authentication endpoint tests
├── test_users.py        # User endpoint tests
└── unit/                # Unit tests
    ├── test_security.py
    ├── test_validators.py
    └── ...
```

#### Manual Test Database Management

```bash
# Start test database manually
docker-compose -f docker-compose.test.yaml up -d

# Stop and remove test database
docker-compose -f docker-compose.test.yaml down -v
```

## CI/CD

The project uses **GitHub Actions** for continuous integration. Tests run automatically on every push to `main` and on pull requests.

### Workflow Features

- **Fast setup** with [uv](https://docs.astral.sh/uv/)
- **PostgreSQL service container** (no docker-compose needed)
- **Parallel test execution**
- **Linting** with ruff

### Build Status

Tests run automatically when you:
- Push to `main` branch
- Open a pull request to `main`

View test results in the **Actions** tab on GitHub.

### Running CI Locally

To simulate CI environment locally:

```bash
CI=true uv run pytest tests/ -v
```

This skips docker-compose (useful if you already have the test database running).

## Docker Commands

```bash
# Start PostgreSQL
docker-compose up -d

# Stop PostgreSQL
docker-compose down

# Complete reset (deletes all data)
docker-compose down -v

# View logs
docker-compose logs -f postgres

# Connect to PostgreSQL
docker exec -it hermes_postgres psql -U hermes_user -d hermes

# Run SQL query
docker exec hermes_postgres psql -U hermes_user -d hermes -c "SELECT * FROM users;"
```

## Quick Start Locally

After cloning the repository on a new machine:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate a new SECRET_KEY (macOS/Linux)
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env

# 3. Start PostgreSQL
docker-compose up -d

# 4. Install dependencies
uv sync

# 5. Run the application
uv run uvicorn src.main:app --reload
```

## Contributing

When contributing, please ensure:

- Never commit `.env` file (use `.env.example` as template)
- Generate strong random secrets: `openssl rand -hex 32`
- Test authentication flows thoroughly
- Document any security-related changes
