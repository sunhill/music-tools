# Spotify PostgreSQL Schema

This folder contains SQL scripts for creating and managing the PostgreSQL database schema for storing Spotify data.

## Files

- `create_tables.sql`: Creates all necessary tables for storing Spotify data
- `drop_tables.sql`: Drops all tables created for storing Spotify data

## Usage

### Creating Tables

To create the tables, you can run the following command:

```bash
psql -U <username> -d <database> -f src/spotify/schema/create_tables.sql
```

Replace `<username>` with your PostgreSQL username and `<database>` with your database name.

### Dropping Tables

To drop all tables, you can run the following command:

```bash
psql -U <username> -d <database> -f src/spotify/schema/drop_tables.sql
```

## Table Structure

The schema includes the following tables:

- `spot_artists`: Stores artist information
- `spot_albums`: Stores album information
- `spot_tracks`: Stores track information
- `spot_playlists`: Stores playlist information
- `spot_album_artists`: Junction table for album-artist relationships
- `spot_track_artists`: Junction table for track-artist relationships
- `spot_playlist_tracks`: Junction table for playlist-track relationships

## Notes

- The tables use `JSONB` for storing complex data structures like images, external URLs, etc.
- Foreign key constraints are used to maintain referential integrity
- Timestamps are used to track when records are created 