# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Music-tools is a comprehensive application for exporting and managing Spotify music data. It consists of a Python backend (FastAPI) that fetches and serves Spotify data, and a React TypeScript frontend (Material-UI) for browsing and creating playlists.

## Development Commands

### Backend Setup & Running

```bash
# Set required environment variables
export SPOTIFY_CONFIG_LOCATION=$(pwd)/src/app_config/app_config.ini
export PYTHONPATH=src

# Activate virtual environment (Python 3.13+ required)
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Start backend only (port 8001)
./start_api.sh

# Start both backend and frontend
./start_dev.sh
```

### Frontend Setup & Running

**IMPORTANT:** All frontend commands MUST be run from the `frontend/` directory:

```bash
cd frontend

# Install dependencies
npm install

# Start development server (port 3000)
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Testing

```bash
# Run all Python tests
python -m pytest tests/

# Run tests with output
python -m pytest tests/ -v
```

### Dependency Management

The project uses `uv` for Python dependency management:

```bash
# Sync requirements.txt with pyproject.toml
uv pip compile pyproject.toml --output-file requirements.txt

# Install from requirements.txt
uv pip install -r requirements.txt
```

### Fetching Spotify Data

To fetch your latest data from the Spotify API:

```bash
# Option 1: Use the wrapper script (recommended)
./spotify-export.sh

# Option 2: Use the original script
./get_spotify_data.sh

# Option 3: Use the console script directly
export SPOTIFY_CONFIG_LOCATION=$(pwd)/src/app_config/app_config.ini
export PYTHONPATH=src
spotify-export
```

**Note**: Redis must be running for rate limiting. Start Redis with: `brew services start redis`

### Data Export Commands

The project defines console scripts in `pyproject.toml`:

```bash
spotify-export              # Fetch latest data from Spotify API
spotify-save-to-file        # Export to Excel/CSV/JSON
spotify-save-to-mongo       # Export to MongoDB
spotify-save-to-postgres    # Export to PostgreSQL
```

## Architecture Overview

### Data Flow Architecture

1. **Data Retrieval**: `spotify/spotify_get_data.py` fetches data from Spotify API using async operations with rate limiting (Redis-based)
2. **Data Storage**: Raw data is pickled and zipped, saved to `raw_data_location` configured per user
3. **Data Loading**: On FastAPI startup (`app/utils.py:lifespan`), data is unzipped from pickle files and loaded into memory
4. **Data Serving**: FastAPI routes serve the in-memory data to the frontend

### Backend Structure

```
src/
├── app/                          # FastAPI application
│   ├── main.py                   # App entry point, route registration, CORS
│   ├── config.py                 # Custom FastAPI app class with data attributes
│   ├── dependencies.py           # Dependency injection functions (get_artists, get_tracks, etc.)
│   ├── utils.py                  # Lifespan manager for data loading on startup
│   ├── api/routes/               # API endpoints
│   │   ├── artists.py            # /artists endpoints
│   │   ├── albums.py             # /albums endpoints
│   │   ├── tracks.py             # /tracks endpoints
│   │   ├── playlists.py          # /playlists endpoints
│   │   ├── genres.py             # /genres endpoints
│   │   ├── playlist_creation.py  # Playlist creation endpoints
│   │   └── save_data.py          # Data export endpoints
│   ├── model/                    # Pydantic models
│   └── templates/                # Jinja2 templates for HTML views
├── spotify/                      # Spotify data retrieval
│   ├── spotify_get_data.py       # Async Spotify API client with rate limiting
│   ├── spotify_get_data_non_async.py  # Non-async fallback client
│   ├── spotify_playlist_maker.py # Playlist creation logic (random, by year, by decade)
│   ├── spotify_utils.py          # Utility functions (zipping, config, memory)
│   └── schema/                   # PostgreSQL schema definitions
├── storage/                      # Data storage backends
│   ├── file/                     # Export to Excel/CSV/JSON
│   ├── mongo/                    # MongoDB storage
│   ├── postgres/                 # PostgreSQL storage
│   └── markdown/                 # Markdown export (WIP on 'markdown' branch)
├── utils/                        # Shared utilities
│   └── rate_limiter/             # Rate limiting implementations (Redis, in-memory)
└── app_config/                   # Configuration files (.ini)
```

### Frontend Structure

```
frontend/
├── src/
│   ├── App.tsx                   # Main app component with routing
│   ├── index.tsx                 # Entry point
│   └── components/               # Reusable components (ArtistCard, etc.)
├── public/                       # Static assets
└── package.json                  # Dependencies and scripts
```

### Key Design Patterns

**Custom FastAPI App Class**: `app/config.py` defines `MyFastAPI` class extending FastAPI, adding attributes to store loaded data (artists, albums, tracks, playlists) in memory.

**Lifespan Events**: `app/utils.py` implements FastAPI lifespan context manager that loads all Spotify data from zipped pickle files on startup, making data available throughout the app lifecycle.

**Dependency Injection**: `app/dependencies.py` provides async dependency functions for filtering/sorting/paginating data, used in route handlers via FastAPI's `Depends()`.

**Rate Limiting**: Spotify API calls use `RedisRateLimiter` (or `InMemoryRateLimiter` fallback) with configurable burst size and retry logic to avoid API throttling.

**Data Persistence**: Spotify data is saved as pickled Python objects, then zipped. Each data type (artists, albums, tracks, playlists) has separate zip files with timestamps.

## Configuration

### Environment Variables

Create `.env` file (use `.env_template` as reference):

```bash
SPOTIFY_CONFIG_LOCATION=/path/to/app_config.ini
DATA_DIR=/path/to/pickle/files
PYTHONPATH=src
```

### App Config File

Copy `src/app_config/app_config_template.cfg` to `src/app_config/app_config.ini` and configure:

- `[spotify]`: Spotify API credentials, save location, username
- `[lastfm]`: Last.fm API credentials (optional)
- `[mongodb]`: MongoDB connection string
- `[discogs]`: Discogs API credentials (optional)

**User-specific configs**: The codebase supports per-user configs (e.g., `app_config_simon.cfg`, `app_config_marcus.cfg`). Data is saved to subdirectories based on `spotify_user` in config.

## API Routes

### Data Endpoints

- `GET /artists` - List all artists (supports pagination, sorting, search, genre filter)
- `GET /albums` - List all albums (supports pagination, sorting by name/artist, search, type filter)
- `GET /tracks` - List all tracks (supports pagination, sorting by name/artists/duration, search)
- `GET /playlists` - List all playlists (supports pagination, sorting, search)
- `GET /genres` - List all unique genres

### Playlist Creation Endpoints

- `GET /make_random_playlist` - Create random playlist from liked content
- `GET /make_playlists_between_years?start_year=X&end_year=Y` - Create playlists for year range
- `POST /make_playlist_for_year/{year}` - Create playlist for specific year
- `POST /make_playlist_for_decade/{decade}` - Create playlist for decade (e.g., 201 for 2010s)

### Utility Endpoints

- `GET /` - HTML page listing all available routes
- `GET /callback` - OAuth callback for Spotify authentication
- `GET /test` - Health check endpoint

## Data Model

Pydantic models in `src/app/model/model.py` define the structure for:

- `Artist`: id, name, images, followers, genres, popularity
- `Album`: id, name, artists, images, release_date, album_type, total_tracks, label
- `Track`: id, name, artists, album, duration_ms, explicit, popularity
- `Playlist`: id, name, description, images, tracks, owner

**Model Serialization**: Models use `model_dump()` for serialization. Private fields (prefixed with `_`) are excluded from dumps.

## Redis Setup

Redis is used for rate limiting Spotify API calls. See `docs/redis.md` for setup instructions.

Default rate limits:
- 200 requests per period
- Burst size: 20
- Retry after: 10 seconds

## Docker Usage

```bash
# Build and start services
docker-compose up

# Backend available at: http://localhost:8001
# Frontend available at: http://localhost:3000
```

Environment variable `RUNNING_IN_DOCKER=True` switches save location to `/src/data/`.

## Testing Notes

- Test data is located in `tests/data/`
- Current tests focus on Pydantic model serialization
- API routes use dependency injection, making them easy to test with `pytest` and `pytest-mock`

## Storage Backends

The project supports multiple storage backends for Spotify data:

- **File** (`storage/file/`): Excel, CSV, JSON exports
- **PostgreSQL** (`storage/postgres/`): Relational database storage with defined schema
- **MongoDB** (`storage/mongo/`): Document-based NoSQL storage
- **Markdown** (`storage/markdown/`): Markdown export (work in progress on `markdown` branch)

Each backend has `spotify_save_to_*` and `spotify_read_from_*` modules.

## Important Implementation Details

### Parallel Processing

`spotify_get_data.py` uses `ThreadPoolExecutor` for parallel API requests with configurable `MAX_CONCURRENT_REQUESTS`.

### Data Deduplication

Tracks and albums are deduplicated during retrieval to avoid duplicate entries from multiple sources (saved tracks, playlist tracks, album tracks).

### Memory Management

`spotify_utils.py` provides `get_memory_usage()` for monitoring memory consumption when loading large datasets.

### Logging

All modules use Python's `logging` module. Configure logging in `src/app_config/logging.conf`. Spotipy client logging is set to CRITICAL to reduce noise.

## Common Patterns

### Adding a New API Route

1. Create route file in `src/app/api/routes/`
2. Define router: `router = APIRouter()`
3. Add dependency functions to `src/app/dependencies.py` if needed
4. Register router in `src/app/main.py`: `app.include_router(router, tags=[...])`

### Adding a New Storage Backend

1. Create module in `src/storage/<backend_name>/`
2. Implement `spotify_save_to_<backend>` and `spotify_read_from_<backend>`
3. Add console script entry point in `pyproject.toml`

### Frontend API Integration

Frontend uses Axios for API calls. Backend must be running on port 8001. CORS is configured in `src/app/main.py` to allow requests from `http://localhost:3000`.
