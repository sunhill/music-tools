# Spotify Data Export to PostgreSQL

This guide explains how to export your Spotify data to a PostgreSQL database using the `spotify_postgres_saver.py` script.

## Quick Start with Setup Script

The easiest way to run the export is using the provided setup script:

1. Make the script executable:
   ```bash
   chmod +x run_postgres_export.sh
   ```

2. Run the script:
   ```bash
   ./run_postgres_export.sh
   ```

The script will:
- Create and activate a virtual environment
- Install required packages
- Set up the Python path
- Check for Spotify credentials (from environment variables or app_config.ini)
- Run the PostgreSQL export

### Storing Spotify Credentials

You can store your Spotify credentials in an `app_config.ini` file. The script will look for this file in the following locations (in order):

1. Project root directory: `app_config.ini`
2. `src` directory: `src/app_config.ini`
3. `src/spotify` directory: `src/spotify/app_config.ini`
4. `src/spotify/config` directory: `src/spotify/config/app_config.ini`

Example `app_config.ini` file:
```ini
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

The script will automatically detect and use these credentials if the file exists. If you don't have this file, the script will prompt you to enter your credentials and offer to save them to `app_config.ini` in the project root directory for future use.

### Customizing the Script

You can modify the database configuration variables at the top of the script:
```bash
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="spotify"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_SCHEMA="public"
```

Or you can pass them as environment variables when running the script:
```bash
DB_HOST=myhost DB_PASSWORD=mypassword ./run_postgres_export.sh
```

## Manual Setup

If you prefer to run the export manually, follow these steps:

### Prerequisites

1. **PostgreSQL Database**: You need a PostgreSQL database server running. If you don't have one, you can:
   - Install PostgreSQL locally: [PostgreSQL Downloads](https://www.postgresql.org/download/)
   - Use a cloud service like [Supabase](https://supabase.com/), [Railway](https://railway.app/), or [Neon](https://neon.tech/)

2. **Python Dependencies**: Make sure you have the required Python packages installed:
   ```bash
   pip install asyncpg pydantic
   ```

3. **Spotify API Credentials**: Ensure your Spotify API credentials are set up:
   ```bash
   export SPOTIFY_CLIENT_ID="your_client_id"
   export SPOTIFY_CLIENT_SECRET="your_client_secret"
   export SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
   ```

   Alternatively, you can create an `app_config.ini` file in one of the following locations:
   - Project root directory: `app_config.ini`
   - `src` directory: `src/app_config.ini`
   - `src/spotify` directory: `src/spotify/app_config.ini`
   - `src/spotify/config` directory: `src/spotify/config/app_config.ini`

   Example `app_config.ini` file:
   ```ini
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

### Environment Setup

Before running the script, you need to add the `src` directory to your Python path:

```bash
# On Linux/Mac
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# On Windows (PowerShell)
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)\src"
```

### Database Setup

#### Option 1: Automatic Setup

The script will automatically create the necessary tables if they don't exist. No manual setup is required.

#### Option 2: Manual Setup

If you prefer to set up the database manually:

1. Create a database:
   ```bash
   createdb spotify
   ```

2. Create the tables using the SQL script:
   ```bash
   psql -U <username> -d spotify -f src/spotify/schema/create_tables.sql
   ```

3. To drop all tables (if needed):
   ```bash
   psql -U <username> -d spotify -f src/spotify/schema/drop_tables.sql
   ```

### Running the Export

#### Basic Usage

To export your Spotify data to PostgreSQL with default settings:

```bash
python src/spotify/spotify_postgres_saver.py
```

This will:
1. Connect to a local PostgreSQL instance
2. Create the necessary tables if they don't exist
3. Retrieve your Spotify data using parallel processing
4. zip the data (for backup)
5. Save the data to PostgreSQL

#### Customizing Database Connection

You can customize the database connection using command-line arguments:

```bash
python src/spotify/spotify_postgres_saver.py --db-host localhost --db-port 5432 --db-name spotify --db-user postgres --db-password postgres --schema public
```

#### Skipping Zipping

By default, the script zips the data before saving it to PostgreSQL. To skip zipping:

```bash
python src/spotify/spotify_postgres_saver.py --no-zip
```

## Database Schema

The PostgreSQL schema includes the following tables:

### Main Tables

- `spot_artists`: Stores artist information
  - Primary key: `id`
  - Fields: name, uri, href, external_urls, images, genres, popularity, followers, spotify_url, created_at

- `spot_albums`: Stores album information
  - Primary key: `id`
  - Fields: name, uri, href, external_urls, images, release_date, release_date_precision, total_tracks, album_type, available_markets, spotify_url, created_at

- `spot_tracks`: Stores track information
  - Primary key: `id`
  - Fields: name, uri, href, external_urls, duration_ms, preview_url, album_id, available_markets, isrc, spotify_url, created_at
  - Foreign key: `album_id` references `spot_albums(id)`

- `spot_playlists`: Stores playlist information
  - Primary key: `id`
  - Fields: name, uri, href, external_urls, description, images, owner, public, tracks_count, spotify_url, created_at

### Junction Tables

- `spot_album_artists`: Links albums to artists
  - Primary key: (album_id, artist_id)
  - Foreign keys: album_id references spot_albums(id), artist_id references spot_artists(id)

- `spot_track_artists`: Links tracks to artists
  - Primary key: (track_id, artist_id)
  - Foreign keys: track_id references spot_tracks(id), artist_id references spot_artists(id)

- `spot_playlist_tracks`: Links playlists to tracks
  - Primary key: (playlist_id, track_id)
  - Foreign keys: playlist_id references spot_playlists(id), track_id references spot_tracks(id)
  - Additional fields: added_at, created_at

## Querying the Data

Once your data is in PostgreSQL, you can run SQL queries to analyze it. Here are some example queries:

### Count of saved tracks by artist

```sql
SELECT a.name, COUNT(t.id) as track_count
FROM spot_artists a
JOIN spot_track_artists ta ON a.id = ta.artist_id
JOIN spot_tracks t ON ta.track_id = t.id
GROUP BY a.id, a.name
ORDER BY track_count DESC;
```

### Albums released in a specific year

```sql
SELECT a.name, a.release_date, ar.name as artist_name
FROM spot_albums a
JOIN spot_album_artists aa ON a.id = aa.album_id
JOIN spot_artists ar ON aa.artist_id = ar.id
WHERE a.release_date LIKE '2022%'
ORDER BY a.release_date;
```

### Tracks in a specific playlist

```sql
SELECT t.name, a.name as artist_name, al.name as album_name
FROM spot_tracks t
JOIN spot_playlist_tracks pt ON t.id = pt.track_id
JOIN spot_playlists p ON pt.playlist_id = p.id
JOIN spot_track_artists ta ON t.id = ta.track_id
JOIN spot_artists a ON ta.artist_id = a.id
JOIN spot_albums al ON t.album_id = al.id
WHERE p.name = 'Your Playlist Name'
ORDER BY pt.added_at;
```

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Verify your PostgreSQL server is running
2. Check your connection parameters (host, port, username, password)
3. Ensure your PostgreSQL user has the necessary permissions

### Data Import Issues

If data import fails:

1. Check the logs for specific error messages
2. Verify your Spotify API credentials are correct
3. Try running with the `--no-zip` flag to skip the zipping step

### Script Issues

If the setup script fails:

1. Make sure the script has execute permissions (`chmod +x run_postgres_export.sh`)
2. Check that Python 3 is installed and accessible
3. Verify that you're running the script from the project root directory
4. Look for error messages in the colored output

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [Pydantic Documentation](https://docs.pydantic.dev/) 