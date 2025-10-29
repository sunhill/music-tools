-- Create tables for storing Spotify data in PostgreSQL

-- Create artists table
CREATE TABLE IF NOT EXISTS spot_artists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    uri TEXT NOT NULL,
    href TEXT NOT NULL,
    external_urls JSONB NOT NULL,
    image TEXT,
    genres JSONB,
    popularity INTEGER,
    followers INTEGER,
    spotify_url TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Create albums table
CREATE TABLE IF NOT EXISTS spot_albums (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    uri TEXT NOT NULL,
    href TEXT NOT NULL,
    external_urls JSONB NOT NULL,
    image TEXT,
    release_date TEXT NOT NULL,
    release_date_precision TEXT,
    total_tracks INTEGER NOT NULL,
    album_type TEXT NOT NULL,
    available_markets JSONB,
    spotify_url TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Create album_artists junction table
CREATE TABLE IF NOT EXISTS spot_album_artists (
    album_id TEXT REFERENCES spot_albums(id) ON DELETE CASCADE,
    artist_id TEXT REFERENCES spot_artists(id) ON DELETE CASCADE,
    PRIMARY KEY (album_id, artist_id)
);

-- Create tracks table
CREATE TABLE IF NOT EXISTS spot_tracks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    uri TEXT,
    href TEXT,
    external_urls JSONB,
    duration_ms INTEGER NOT NULL,
    preview_url TEXT,
    album_id TEXT,
    available_markets JSONB,
    isrc TEXT,
    spotify_url TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Create track_artists junction table
CREATE TABLE IF NOT EXISTS spot_track_artists (
    track_id TEXT REFERENCES spot_tracks(id) ON DELETE CASCADE,
    artist_id TEXT REFERENCES spot_artists(id) ON DELETE CASCADE,
    PRIMARY KEY (track_id, artist_id)
);

-- Create playlists table
CREATE TABLE IF NOT EXISTS spot_playlists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    uri TEXT NOT NULL,
    href TEXT,
    external_urls JSONB,
    description TEXT,
--     image TEXT,
    owner TEXT NOT NULL,
    public BOOLEAN NOT NULL,
    tracks_count INTEGER NOT NULL,
    spotify_url TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Create playlist_tracks table
CREATE TABLE IF NOT EXISTS spot_playlist_tracks (
    playlist_id TEXT REFERENCES spot_playlists(id) ON DELETE CASCADE,
    track_id TEXT REFERENCES spot_tracks(id) ON DELETE CASCADE,
    added_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (playlist_id, track_id)
); 