# Dockerised Flask Login App

A small Flask authentication service (register, log in, log out, protected dashboard) backed by MySQL, run as two containers with Docker Compose. A PowerShell script brings the whole stack up with one command for demos.

## Stack

| Part | Choice |
|---|---|
| App | Flask 3, Flask-Login, Flask-SQLAlchemy, Gunicorn |
| Database | MySQL 8.4 with a named volume |
| Container | Multi-stage `python:3.12-slim` image, non-root user, built-in `HEALTHCHECK` |
| Orchestration | Docker Compose; `web` waits for `db` to be healthy |
| CI | GitHub Actions: unit tests, then a full Compose smoke test |

Passwords are hashed with Werkzeug (PBKDF2). `/health` checks DB connectivity and is used by both the container healthcheck and the PowerShell script.

## Run it

**Windows / PowerShell (one command):**

```powershell
./start-demo.ps1          # build, start, wait for health, open browser
./start-demo.ps1 -Down    # stop
./start-demo.ps1 -Reset   # stop and wipe the database
```

On first run the script creates `.env` from `.env.example` with a random `SECRET_KEY`.

**Any OS:**

```bash
cp .env.example .env      # edit values
docker compose up -d --build
open http://localhost:5000
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Tests use in-memory SQLite, so no database container is needed.

## Layout

```
app/
  __init__.py     app factory, DB + login manager setup
  models.py       User model with password hashing
  routes.py       auth + dashboard + /health
  templates/
tests/            pytest suite
Dockerfile        multi-stage build
docker-compose.yml
start-demo.ps1    one-command demo spin-up
```
