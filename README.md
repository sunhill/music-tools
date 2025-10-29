# Spotify Export

A tool to export your Spotify data to various formats.

## Features

- Export your saved tracks, albums, artists, and playlists to Excel, CSV, PostgresSQL and other formats
- Parallel processing for faster data retrieval
- Rate limiting to avoid API throttling
- Deduplication of tracks and albums

## Installation

1. Clone the repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your Spotify API credentials:

```bash
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"
export SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
```

## Usage

### Export to Excel

```bash
python src/spotify/spotify_export.py
```

This will create an Excel file with the following sheets:
- Saved Tracks
- Saved Albums
- Saved Artists
- My Playlists
- Other Playlists
- Playlist Tracks
- Unique Playlist Tracks
- Unique Playlist Artists

### Export to CSV

```bash
python src/spotify/spotify_export.py --format csv
```

This will create CSV files for each sheet in the Excel file.

### Export to JSON

```bash
python src/spotify/spotify_export.py --format json
```

This will create JSON files for each data type.

### Export to PostgreSQL

```bash
python src/spotify/spotify_postgres_saver.py
```

This will save your Spotify data to a PostgreSQL database. By default, it will connect to a local PostgreSQL instance with the following settings:

- Host: localhost
- Port: 5432
- Database: spotify
- User: postgres
- Password: postgres
- Schema: public

You can customize these settings using command-line arguments:

```bash
python src/spotify/spotify_postgres_saver.py --db-host localhost --db-port 5432 --db-name spotify --db-user postgres --db-password postgres --schema public
```

By default, the script will pickle the data before saving it to PostgreSQL. You can disable this behavior with the `--no-pickle` flag:

```bash
python src/spotify/spotify_postgres_saver.py --no-pickle
```

#### PostgreSQL Schema

The PostgreSQL schema is defined in the `src/spotify/schema` directory. The following tables are created:

- `spot_artists`: Stores artist information
- `spot_albums`: Stores album information
- `spot_album_artists`: Junction table for album-artist relationships
- `spot_tracks`: Stores track information
- `spot_track_artists`: Junction table for track-artist relationships
- `spot_playlists`: Stores playlist information
- `spot_playlist_tracks`: Junction table for playlist-track relationships

You can create or drop these tables using the SQL scripts in the `src/spotify/schema` directory:

```bash
# Create tables
psql -U <username> -d <database> -f src/spotify/schema/create_tables.sql

# Drop tables
psql -U <username> -d <database> -f src/spotify/schema/drop_tables.sql
```

## Development

### Project Structure

```
spotify-export/
├── src/
│   ├── spotify/
│   │   ├── spotify_export.py
│   │   ├── spotify_get_data.py
│   │   ├── spotify_get_data_v2.py
│   │   ├── spotify_postgres_saver.py
│   │   ├── spotify_utils.py
│   │   └── schema/
│   │       ├── create_tables.sql
│   │       ├── drop_tables.sql
│   │       └── README.md
│   └── app/
│       ├── dependencies.py
│       ├── main.py
│       └── static/
│           ├── css/
│           │   └── styles.css
│           └── js/
│               └── app.js
├── requirements.txt
└── README.md
```

### Running Tests

```bash
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Pre-requisites

* pip install --upgrade pipenv
* pip install --upgrade setuptools
* pipenv --python 3.8
* pipenv install -dev
* pipenv shell
* setup.py --help-commands
* setup.py sdist

### Redis Setup

This project uses Redis for rate limiting. See [Redis Documentation](docs/redis.md) for setup instructions.

## Using `uv` for Python Dependency Management

This project uses [`uv`](https://github.com/astral-sh/uv) as a fast, modern Python package manager and virtual environment tool.

### Why `uv`?

- Much faster than `pip` and `pip-tools`
- Handles dependency resolution and virtual environments in one tool
- Drop-in replacement for most `pip`/`venv` workflows

### Common Commands

- **Install dependencies:**  
  ```sh
  uv pip install -r requirements.txt

### Keeping `requirements.txt` in Sync with `pyproject.toml` using `uv`

To ensure your `requirements.txt` matches the dependencies specified in `pyproject.toml`, use the following command:

  ```sh
  uv pip compile pyproject.toml --output-file requirements.txt
  ```


### Useful links

* [pipenv](https://pipenv.kennethreitz.org/en/latest/install/#installing-pipenv)
* [Structuring your project](https://docs.python-guide.org/writing/structure/)
* [Repository Structure and Python](https://www.kennethreitz.org/essays/repository-structure-and-python)
* [Setuptools](https://setuptools.readthedocs.io/)
* [more pipenv](https://dev.to/yukinagae/your-first-guide-to-getting-started-with-pipenv-50bn)
