export interface SpotifyImage {
  url: string;
  height: number;
  width: number;
}

export interface Artist {
  id: string;
  name: string;
  images: SpotifyImage[];
  genres: string[];
  followers: {
    total: number;
  };
}

export interface Album {
  id: string;
  name: string;
  artists: Artist[];
  images: SpotifyImage[];
  release_date: string;
  artists_joined: string;
  album_type: string;
  label: string;
  total_tracks: number;
  release_date_precision: string;
}

export interface Track {
  id: string;
  name: string;
  artists: Artist[];
  _album: {
    name: string;
    images: SpotifyImage[];
    release_date: string;
    album_type: string;
    total_tracks: number;
  };
  duration_ms: number;
  artists_joined: string;
  preview_url: string;
  track_number: number;
  disc_number: number;
}

export interface Playlist {
  id: string;
  name: string;
  description: string;
  images: SpotifyImage[];
  tracks: {
    total: number;
  };
  owner: {
    display_name: string;
  };
} 