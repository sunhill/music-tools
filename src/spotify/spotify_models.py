from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class SpotifyImage(BaseModel):
    """Spotify image model."""

    height: int = 0
    url: str
    width: int = 0


class SpotifyFollowers(BaseModel):
    """Spotify followers model."""

    href: Optional[str] = None
    total: int = 0


class SpotifyCopyright(BaseModel):
    """Spotify copyright model."""

    text: str
    type: str


class SpotifyExternalIds(BaseModel):
    """Spotify external IDs model."""

    isrc: Optional[str] = None
    upc: Optional[str] = None


class SpotifyArtist(BaseModel):
    """Spotify artist model."""

    external_urls: Dict[str, str]
    followers: SpotifyFollowers = Field(default_factory=SpotifyFollowers)
    genres: List[str] = []
    href: str
    id: str
    images: List[SpotifyImage] = []
    name: str
    popularity: int = 0
    type: str
    uri: str
    # Additional fields for database
    spotify_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class SpotifyAlbum(BaseModel):
    """Spotify album model."""

    album_type: str
    artists: List[SpotifyArtist]
    available_markets: List[str]
    copyrights: List[SpotifyCopyright] = []
    external_ids: SpotifyExternalIds = Field(default_factory=SpotifyExternalIds)
    external_urls: Dict[str, str]
    genres: List[str] = []
    href: str
    id: str
    images: List[SpotifyImage]
    name: str
    popularity: int = 0
    release_date: str
    release_date_precision: str
    total_tracks: int
    type: str
    uri: str
    # Additional fields for database
    spotify_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class SpotifyTrack(BaseModel):
    """Spotify track model."""

    album: Optional[SpotifyAlbum] = Field(default_factory=SpotifyAlbum)
    artists: List[SpotifyArtist]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: SpotifyExternalIds
    external_urls: Dict[str, str]
    href: str
    id: str
    is_local: bool
    is_playable: bool
    name: str
    popularity: int = 0
    preview_url: Optional[str] = None
    track_number: int
    type: str
    uri: str
    # Additional fields for database
    spotify_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class SpotifyPlaylistOwner(BaseModel):
    """Spotify playlist owner model."""

    display_name: str
    external_urls: Dict[str, str]
    href: str
    id: str
    type: str
    uri: str


class SpotifyPlaylistTracks(BaseModel):
    """Spotify playlist tracks model."""

    href: str
    total: int


class SpotifyPlaylist(BaseModel):
    """Spotify playlist model."""

    collaborative: bool
    description: str
    external_urls: Dict[str, str]
    href: str
    id: str
    # images: List[SpotifyImage] = []
    name: str
    owner: SpotifyPlaylistOwner
    primary_color: Optional[str] = None
    public: bool
    snapshot_id: str
    tracks: SpotifyPlaylistTracks
    type: str
    uri: str
    # Additional fields for database
    spotify_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class SpotifyPlaylistTrack(BaseModel):
    """Spotify playlist track model for database."""

    playlist_id: str
    track_id: str
    added_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)
