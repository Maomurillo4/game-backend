# Game Backend API

A backend service for video games built with FastAPI. Provides user authentication, cloud save management, and real-time leaderboards — the kind of infrastructure that powers real game backends.

## Tech Stack

- **FastAPI** — REST API framework
- **SQLModel** — ORM with SQLite (easily swappable for PostgreSQL)
- **Argon2** — Password hashing
- **JWT** — Token-based authentication via python-jose
- **uv** — Dependency management

## Features

- User registration and login with hashed passwords
- JWT authentication protecting write endpoints
- Cloud save system with automatic timestamps
- Leaderboards per game title, ordered by score

## Getting Started

```bash
# Clone the repo
git clone https://github.com/Maomurillo4/game-backend.git
cd game-backend

# Install dependencies
uv sync

# Create your .env file
echo "SECRET_KEY=your-secret-key-here" > .env

# Run the server
uv run fastapi dev
```

API docs available at `http://127.0.0.1:8000/docs`

## Endpoints

### Auth
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| POST | `/auth/login` | Login and receive JWT | No |

### Users
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| POST | `/users/` | Register a new user | No |
| GET | `/users/` | List all users | No |
| GET | `/users/{user_id}` | Get a user by ID | No |
| PUT | `/users/{user_id}` | Update your account | Yes |
| DELETE | `/users/{user_id}` | Delete your account | Yes |

### Saves
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| POST | `/saves/` | Create a cloud save | Yes |
| GET | `/saves/{user_id}` | Get all saves for a user | No |

### Leaderboards
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| GET | `/leaderboards/{game_title}` | Top scores for a game | No |

## Example Usage

```bash
# Register
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "mario", "email": "mario@nintendo.com", "password": "super123"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "mario", "password": "super123"}'

# Create a save (requires token)
curl -X POST "http://localhost:8000/saves/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"game_title": "Hollow Knight", "state": "{\"area\": \"Forgotten Crossroads\"}", "score": 1200}'

# Get leaderboard
curl "http://localhost:8000/leaderboards/Silksong"
```