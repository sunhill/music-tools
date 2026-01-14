# Project Rules & Context

## Project Overview
Music-tools is a Spotify data management app with a Python FastAPI backend and React TypeScript frontend.

## Tech Stack
- **Backend**: Python 3.13+, FastAPI, Pydantic v2, Asyncio.
- **Frontend**: React, TypeScript, Material-UI (MUI).
- **Package Manager**: `uv` (Python), `npm` (Node).
- **Storage**: PostgreSQL, MongoDB, Redis (for rate limiting).

## Coding Guidelines

### Python (Backend)
- **Formatting**: Follow `black` style and `isort` for imports.
- **Typing**: Enforce strict type hints (checked by `mypy`).
- **Pydantic**: Use Pydantic V2 conventions (e.g., `model_dump()` instead of `.dict()`).
- **Async**: Prefer `async/await` for I/O bound operations.
- **Paths**: Use `pathlib` instead of `os.path` where possible.

### TypeScript (Frontend)
- **Components**: Use functional components with React Hooks.
- **Styling**: Use Material-UI components and styling system.
- **State**: Manage state effectively; avoid excessive prop drilling.

## Architecture & Patterns
- **In-Memory Data**: Spotify data (artists, tracks, etc.) is loaded into memory at startup via `app/utils.py`.
- **Configuration**: Configuration lives in `src/app_config/app_config.ini`. Never hardcode credentials.
- **Rate Limiting**: Respect `RedisRateLimiter` for external API calls to avoid throttling.
- **Dependency Injection**: Use FastAPI's `Depends()` for services like `get_artists` or `get_tracks`.

## Development Workflow
- **Frontend Commands**: Must be run from the `frontend/` subdirectory.
- **Backend Port**: 8001
- **Frontend Port**: 3000
- **Dependency Install**: `uv pip install -r requirements.txt`
