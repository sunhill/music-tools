-- Drop tables for Spotify data in PostgreSQL

-- Drop tables in the correct order to handle foreign key constraints
DROP TABLE IF EXISTS spot_playlist_tracks;
DROP TABLE IF EXISTS spot_track_artists;
DROP TABLE IF EXISTS spot_album_artists;
DROP TABLE IF EXISTS spot_tracks;
DROP TABLE IF EXISTS spot_playlists;
DROP TABLE IF EXISTS spot_albums;
DROP TABLE IF EXISTS spot_artists; 