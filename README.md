# Take Home Challenge

[![CircleCI](https://dl.circleci.com/status-badge/img/circleci/XDAqBGGy3hmP1bSiLaNrAs/WziQdkTEG5iipEvmUQMnZa/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/circleci/XDAqBGGy3hmP1bSiLaNrAs/WziQdkTEG5iipEvmUQMnZa/tree/main)
[![Coverage Status](https://coveralls.io/repos/github/luisfernandoc/take_home_challenge/badge.svg?branch=main)](https://coveralls.io/github/luisfernandoc/take_home_challenge?branch=main)

A user management API built with Python 3.13 and FastAPI.

Users can be assigned Pokémon using their IDs. These IDs are stored in
PostgreSQL, while Pokémon names are retrieved from PokéAPI.

Passwords are stored as Argon2 hashes and are never included in API responses.

## Technologies

- FastAPI and Pydantic
- SQLAlchemy and PostgreSQL 17
- Alembic
- HTTPX and cachetools
- pwdlib with Argon2
- pytest and Ruff
- uv, Docker, and Docker Compose

## Requirements

To run the application in containers:

- Docker with Docker Compose
- Bash to use the optional startup script

For local development and testing:

- Python 3.13
- uv
- Docker to run PostgreSQL

## Configuration

Copy the example environment files and adjust their values:

```bash
cp .env.example .env
cp .env.test.example .env.test
```

In PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item .env.test.example .env.test
```

Review existing configuration files before overwriting them.

| Variable | Description |
|---|---|
| POSTGRES_DB | Database name |
| POSTGRES_USER | PostgreSQL username |
| POSTGRES_PASSWORD | PostgreSQL password |
| POSTGRES_HOST | PostgreSQL hostname |
| POSTGRES_PORT | PostgreSQL port |
| POKEAPI_BASE_URL | PokéAPI base URL, including a trailing `/` |

When connecting from the host machine, development uses `localhost:5433`
and testing uses `localhost:5434`. Inside Docker Compose, the application
connects to `db:5432`.

The `.env` and `.env.test` files contain local configuration and are
excluded from version control.

## Running with Docker Compose

```bash
docker compose up --build -d api
```

Compose waits for PostgreSQL to become healthy, applies database migrations,
and then starts the API.

Alternatively, use the startup script:

```bash
bash scripts/start.sh
```

Interactive documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

Check service status and logs:

```bash
docker compose ps -a
docker compose logs --tail=100 migrate api
```

The `migrate` service should exit with code `0`.

Stop the services while preserving database data:

```bash
docker compose down
```

Running `docker compose down -v` also deletes the volumes and their data.

## Local Development

If the Compose API service is already using port 8000, stop it first:

```bash
docker compose stop api
```

Install dependencies, start PostgreSQL, apply migrations, and run the API:

```bash
uv sync --locked
docker compose up -d db
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/users` | Create a user |
| GET | `/users` | List users |
| GET | `/users/by-email?email=...` | Find a user by email |
| GET | `/users/{user_id}` | Find a user by ID |
| PATCH | `/users/{user_id}` | Partially update a user |
| DELETE | `/users/{user_id}` | Delete a user |

Example creation request:

```json
{
  "name": "Luis",
  "email": "luis@example.com",
  "password": "Example-test-password-2026!",
  "pokemon_ids": [1, 25]
}
```

Example response:

```json
{
  "id": "fa4d590d-4107-4ed7-9eee-bdfabfa817a9",
  "name": "Luis",
  "email": "luis@example.com",
  "pokemons": ["bulbasaur", "pikachu"]
}
```

For PATCH requests:

- Omitting `pokemon_ids` preserves existing assignments.
- Sending `[]` removes all assignments.
- Sending another list replaces the existing assignments.

Empty PATCH request bodies and explicitly provided `null` values are rejected.
The general PATCH endpoint does not support password changes.

## Architecture

The code is organized by feature, with separate responsibilities:

- `domain`: user entity, repository contract, and domain exceptions.
- `application`: use cases and contracts for password hashing and Pokémon lookups.
- `infrastructure`: ORM models, repositories, and external adapters.
- `presentation`: endpoints, HTTP schemas, dependencies, and exception handlers.

The service depends on contracts. Dependency providers connect those contracts
to SQLAlchemy, Argon2, and the PokéAPI client.

The repository stores Pokémon IDs and does not call external services.
The PokéAPI client resolves names and maintains a temporary in-memory cache
that is independent for each application process.

## Testing

Start the testing PostgreSQL instance:

```bash
docker compose --profile test up -d db_test
```

Once the database is healthy, run:

```bash
uv run python -m tests.prepare_database
uv run python -m pytest tests -v
```

SQL fixtures also apply pending migrations.

The test suite uses:

- An in-memory repository and mocks for service tests.
- Dependency overrides for HTTP tests.
- A separate PostgreSQL instance for SQL integration tests.
- Outer transactions and savepoints to roll back test writes.
- MockTransport to test the HTTP client without internet access.
- The real Argon2 implementation to verify password hashing.

## Linting and Formatting

Check code quality and formatting:

```bash
uv run ruff check .
uv run ruff format --check .
```

Apply automatic fixes and formatting:

```bash
uv run ruff check . --fix
uv run ruff format .
```

## Migrations

After modifying the ORM models, generate a migration:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
```

Always review the generated migration before applying it:

```bash
uv run alembic upgrade head
```

## Scope and Limitations

- Authentication and authorization are not implemented.
- The user list endpoint does not support pagination.
- User responses containing Pokémon depend on PokéAPI when names are not cached.
- Email comparisons follow the application's current behavior; a comprehensive
  case-insensitive comparison policy is not implemented.
- Password hashing protects stored passwords, but does not restrict access
  to API endpoints.
