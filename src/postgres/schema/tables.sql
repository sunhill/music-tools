
CREATE TABLE IF NOT EXISTS Artists (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name TEXT NOT NULL,
    external_urls JSONB,
    followers JSONB,
    genres TEXT[],
    href TEXT,
    images JSONB,
    popularity INT,
    type TEXT,
    uri TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Albums (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    album_type TEXT,
    artists JSONB,
    available_markets TEXT[],
    copyrights JSONB,
    external_ids JSONB,
    external_urls JSONB,
    genres TEXT[],
    href TEXT,
    images JSONB,
    label TEXT,
    name TEXT NOT NULL,
    popularity INT,
    release_date TEXT,
    release_date_precision TEXT,
    total_tracks INT,
    tracks JSONB,
    type TEXT,
    uri TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Tracks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    album JSONB,
    artists JSONB,
    available_markets TEXT[],
    disc_number INT,
    duration_ms INT,
    explicit BOOLEAN,
    external_ids JSONB,
    external_urls JSONB,
    href TEXT,
    is_local BOOLEAN,
    name TEXT NOT NULL,
    popularity INT,
    preview_url TEXT,
    track_number INT,
    type TEXT,
    uri TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Playlists (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    collaborative BOOLEAN,
    description TEXT,
    external_urls JSONB,
    href TEXT,
    name TEXT NOT NULL,
    owner JSONB,
    primary_color TEXT,
    public BOOLEAN,
    snapshot_id TEXT,
    tracks JSONB,
    type TEXT,
    uri TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Images (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    height INT,
    width INT,
    url TEXT UNIQUE NOT NULL
);