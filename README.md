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

```bash
uv run pytest
```

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
