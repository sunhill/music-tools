from typing import List

from pydantic import BaseModel, computed_field


def sanitize(name):
    # remove special characters including / and \ from image name
    # sanitize the name for windows and linux only replacing what's necessary
    name = name.replace("/", "-")
    name = name.replace("\\", "-")
    name = name.replace(":", "-")
    name = name.replace("?", "")
    name = name.replace("*", "")
    name = name.replace('"', "")
    name = name.replace("<", "")
    name = name.replace(">", "")
    name = name.replace("|", "")

    return name


class Image(BaseModel):
    height: int
    width: int
    url: str


class BasicArtist(BaseModel):
    _external_urls: dict
    _href: str
    id: str
    name: str
    _type: str
    _uri: str


class Artist(BasicArtist):
    _external_urls: dict
    followers: dict
    genres: List[str]
    _href: str
    id: str
    images: List[Image]
    name: str
    _popularity: int
    _type: str
    _uri: str

    @computed_field()
    @property
    def image(self) -> str:
        if len(self.images) == 0:
            return ""
        else:
            return self.images[0].url

    @computed_field()
    @property
    def image_name(self) -> str:
        image_name = f"{self.name}"
        image_name = sanitize(image_name)
        return image_name


class Track(BaseModel):
    album: dict | None = None
    album_id: str | None = None
    artists: List[BasicArtist]
    _available_markets: List[str] | None = None
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: dict | None = None
    external_urls: dict | None = None
    href: str
    id: str
    images: List[Image] | None = None
    _is_local: bool
    name: str
    _popularity: int | None = None
    preview_url: str | None
    track_number: int
    type: str | None = None
    uri: str

    @computed_field()
    @property
    def artists_joined(self) -> str:
        return ", ".join([artist.name for artist in self.artists])


class Album(BaseModel):
    album_type: str
    artists: List[BasicArtist]
    _available_markets: List[str]
    _copyrights: List[dict]
    _external_ids: dict
    external_urls: dict
    _genres: List[str]
    href: str
    id: str
    images: List[Image]
    label: str
    name: str
    _popularity: int
    release_date: str
    release_date_precision: str
    total_tracks: int
    tracks: List[Track] | None = None
    _type: str
    _uri: str

    @computed_field()
    @property
    def image(self) -> str:
        if len(self.images) == 0:
            return ""
        else:
            return self.images[0].url

    @computed_field()
    @property
    def artists_joined(self) -> str:
        return ", ".join([artist.name for artist in self.artists])

    @computed_field()
    @property
    def release_year(self) -> str:
        return self.release_date.split("-")[0]

    @computed_field()
    @property
    def image_name(self) -> str:
        image_name = f"{self.artists_joined} - {self.name}"
        return sanitize(image_name)


class Playlist(BaseModel):
    collaborative: bool
    description: str
    external_urls: dict
    href: str
    id: str
    images: List[Image]
    name: str
    owner: dict
    _primary_color: str
    public: bool
    _snapshot_id: str
    tracks: dict
    type: str
    uri: str


class PlaylistRequest(BaseModel):
    year: str | None = None
