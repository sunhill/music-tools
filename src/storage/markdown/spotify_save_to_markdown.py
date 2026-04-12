import datetime
import logging
import os
from typing import List, Dict, Optional
import argparse
import frontmatter
from configparser import ConfigParser
import re

from spotify.spotify_save import SpotifySave
from spotify.spotify_utils import (
    get_config_location,
    setup_app_logging,
    most_recent_directory,
    unzip_data_from_zip,
    get_data_location,
)

logger = logging.getLogger(__name__)


def get_safe_filename(name: str) -> str:
    """Return a filename-safe string for macOS (APFS).

    Replaces path separators and null bytes, strips control characters,
    avoids special names, and truncates to 255 characters.
    """
    if not isinstance(name, str):
        name = str(name or "")
    # replace nulls and path separators with underscore
    safe_name = re.sub(r"[\x00/]+", "_", name)
    # remove other non-printable/control characters
    safe_name = re.sub(r"[\x00-\x1f\x7f]+", "", safe_name).strip()
    if not safe_name or safe_name in (".", ".."):
        safe_name = "unnamed"
    return safe_name[:255]


def sanitize_album_name_for_filename(
    name: str, keywords: list[str] | None = None
) -> str:
    """Remove bracketed segments containing 'remaster' (case-insensitive) from album name.

    Keeps the original album name for front matter/content, but returns a cleaned
    version suitable for filenames.
    """
    if not isinstance(name, str):
        name = str(name or "")
    # determine keywords to remove
    if keywords is None:
        keywords = ["remaster", "deluxe", "expanded", "edition", "version", "re-master"]

    # build regex alternation, special-case 'remaster' to match 'remastered' too
    mapped = []
    for kw in keywords:
        kw = str(kw).strip()
        if not kw:
            continue
        if kw.lower() == "remaster":
            # match 'remaster' followed by any letters (covers remaster, remastered, remastering, remasters, etc.)
            mapped.append(r"remaster[a-zA-Z]*")
        else:
            mapped.append(re.escape(kw))

    alt = "|".join(mapped) if mapped else "remaster"
    # remove brackets containing any of the keywords (case-insensitive)
    pattern = rf"[\(\[\{{][^\)\]\}}]*\b(?:{alt})\b[^\)\]\}}]*[\)\]\}}]"
    cleaned = re.sub(pattern, "", name, flags=re.IGNORECASE)
    # collapse whitespace and trim
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # remove trailing separators like '-' or ':' left behind
    cleaned = re.sub(r"[\-:]+$", "", cleaned).strip()
    return cleaned


class SpotifyToMarkdown(SpotifySave):
    """Simple Markdown exporter for Spotify data.

    This implements the abstract methods from `SpotifySave` with small,
    human-readable markdown files. It's intentionally lightweight — the
    goal is to provide a working implementation so the class can be
    instantiated and used in scripts/tests.
    """

    def __init__(
        self, user_id: str = "", markdown_location: Optional[str] = None
    ) -> None:
        super().__init__()
        config_location = get_config_location()
        # Default to project directory next to config if config missing — keep behaviour
        # minimal and robust for tests. Allow caller to override via markdown_location.
        config_parser = ConfigParser()
        try:
            config_parser.read(config_location)
            markdown_folder = config_parser.get(
                "spotify", "markdown_location", fallback="markdown_exports"
            )
        except Exception:
            markdown_folder = "markdown_exports"

        # runtime override wins
        if markdown_location:
            markdown_folder = markdown_location

        # optionally allow sanitize keywords via config (comma separated)
        try:
            sanitize_kw = config_parser.get(
                "spotify", "markdown_sanitize_keywords", fallback=None
            )
            if sanitize_kw:
                # split and strip
                self.sanitize_keywords = [
                    k.strip() for k in sanitize_kw.split(",") if k.strip()
                ]
            else:
                self.sanitize_keywords = None
        except Exception:
            self.sanitize_keywords = None

        if os.path.isabs(markdown_folder):
            save_dir = markdown_folder
        else:
            save_dir = os.path.join(os.path.dirname(config_location), markdown_folder)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir
        # create separate subfolders for artists and albums
        self.artists_dir = os.path.join(self.save_dir, "artists")
        self.albums_dir = os.path.join(self.save_dir, "albums")
        os.makedirs(self.artists_dir, exist_ok=True)
        os.makedirs(self.albums_dir, exist_ok=True)
        logger.info(f"Markdown export root: {self.save_dir}")
        logger.info(f"Artists export folder: {self.artists_dir}")
        logger.info(f"Albums export folder: {self.albums_dir}")

    def _write(self, filename: str, content: str):
        path = os.path.join(self.save_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.debug(f"Wrote markdown file: {path}")

    def save_unique_tracks_in_playlists(self, unique_tracks_in_playlists: Dict):
        pass

    def save_unique_artists_in_playlists(self, unique_artists_in_playlists: Dict):
        pass

    def save_playlist_tracks(self, playlists: List[Dict], playlist_tracks: Dict):
        pass

    def save_playlist_details(self, playlists: List[Dict], playlist_tracks: Dict):
        pass

    def save_albums(self, albums: List[Dict]):
        # Create one markdown file per album using frontmatter, merge metadata if file exists
        for album in albums:
            album_name = album.get("name", "unnamed")
            album_id = album.get("id", "")
            uri = album.get("uri", "")
            release_date = album.get("release_date", "")
            release_date_precision = album.get("release_date_precision", "")
            total_tracks = album.get("total_tracks", "")
            label = album.get("label", "")
            album_type = album.get("album_type", "")

            # artists: list of dicts -> names and ids
            artists = album.get("artists", []) or []
            artist_names = [a.get("name", "") for a in artists]
            artist_ids = [a.get("id", "") for a in artists]

            # pick image if present
            image_url = ""
            imgs = album.get("images", [])
            if imgs and len(imgs) > 0 and isinstance(imgs[0], dict):
                image_url = imgs[0].get("url", "")

            # build a safe filename: put artist name first, then sanitized album name; do NOT include spotify id
            sanitized_album_for_filename = sanitize_album_name_for_filename(
                album_name, self.sanitize_keywords
            )
            base_name = f"{artist_names[0] if artist_names else ''} - {sanitized_album_for_filename}".strip()
            safe_base = get_safe_filename(base_name)
            filename = f"{safe_base}.md"
            path = os.path.join(self.albums_dir, filename)

            # Load existing post if present
            if os.path.exists(path):
                try:
                    post = frontmatter.load(path)
                except Exception:
                    post = frontmatter.Post("")
            else:
                post = frontmatter.Post("")

            meta = post.metadata
            # Add missing metadata fields only
            if "name" not in meta:
                meta["name"] = album_name
            if "id" not in meta:
                meta["id"] = album_id
            if "uri" not in meta:
                meta["uri"] = uri
            if "release_date" not in meta:
                meta["release_date"] = release_date
            if "release_date_precision" not in meta:
                meta["release_date_precision"] = release_date_precision
            if "total_tracks" not in meta:
                meta["total_tracks"] = total_tracks
            if "label" not in meta:
                meta["label"] = label
            if "album_type" not in meta:
                meta["album_type"] = album_type
            if "artists" not in meta:
                meta["artists"] = list(artist_names)
            if "artist_ids" not in meta:
                meta["artist_ids"] = list(artist_ids)

            # Build content: album heading first, then image, then existing body
            existing_body = (post.content or "").lstrip()
            if existing_body.startswith("# "):
                existing_body = "\n".join(existing_body.splitlines()[1:]).lstrip()

            new_body_parts = [f"# {album_name}"]
            if image_url and image_url not in existing_body:
                new_body_parts.append("")
                new_body_parts.append(f"![300]({image_url})")

            if existing_body:
                new_body_parts.append("")
                new_body_parts.append(existing_body)

            post.content = "\n".join(new_body_parts)

            # Write back
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(frontmatter.dumps(post))
            except Exception:
                fallback = (
                    "---\n"
                    + "\n".join(f"{k}: {v}" for k, v in post.metadata.items())
                    + "\n---\n\n"
                    + post.content
                )
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(fallback)

    def save_tracks(self, tracks: List[Dict]):
        pass

    def save_album_tracks(self, tracks: List[Dict]):
        pass

    def save_artists(self, artists: List[Dict]):
        # Create one markdown file per artist with basic metadata using python-frontmatter
        for a in artists:
            name = a.get("name", "unnamed")
            artist_id = a.get("id", "")
            uri = a.get("uri", "")
            followers = a.get("followers", "")
            popularity = a.get("popularity", "")
            genres_list = a.get("genres", []) or []
            image_url = ""
            imgs = a.get("images", [])
            if imgs and len(imgs) > 0 and isinstance(imgs[0], dict):
                image_url = imgs[0].get("url", "")

            # sanitize filename for macOS using helper
            safe_name = get_safe_filename(name)
            filename = f"{safe_name}.md"
            path = os.path.join(self.artists_dir, filename)

            # Load existing post if present
            if os.path.exists(path):
                try:
                    post = frontmatter.load(path)
                except Exception:
                    # on any read/parse error, start fresh
                    post = frontmatter.Post("")
            else:
                post = frontmatter.Post("")

            # Ensure metadata fields exist (do not overwrite existing values)
            meta = post.metadata
            if "name" not in meta:
                meta["name"] = name
            if "id" not in meta:
                meta["id"] = artist_id
            if "uri" not in meta:
                meta["uri"] = uri
            if "followers" not in meta:
                meta["followers"] = followers
            if "popularity" not in meta:
                meta["popularity"] = popularity
            if "genres" not in meta:
                # ensure genres is a list
                meta["genres"] = list(genres_list)

            # Build content: name heading first, then optional image (avoid duplicate), then existing body
            existing_body = (post.content or "").lstrip()
            # remove existing top-level heading if it matches name to avoid duplicate headings
            if existing_body.startswith("# "):
                # drop first line
                existing_body = "\n".join(existing_body.splitlines()[1:]).lstrip()

            new_body_parts = [f"# {name}"]
            if image_url and image_url not in existing_body:
                new_body_parts.append("")
                new_body_parts.append(f"![300]({image_url})")

            if existing_body:
                new_body_parts.append("")
                new_body_parts.append(existing_body)

            post.content = "\n".join(new_body_parts)

            # Write back using frontmatter.dump
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(frontmatter.dumps(post))
            except Exception:
                # fallback: write minimal markdown
                fallback = (
                    "---\n"
                    + "\n".join(f"{k}: {v}" for k, v in post.metadata.items())
                    + "\n---\n\n"
                    + post.content
                )
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(fallback)

    def save_individual_playlists(self, playlists: List[Dict], playlist_tracks: Dict):
        pass


def main():
    # Parse CLI args
    parser = argparse.ArgumentParser(
        description="Export Spotify data to markdown files"
    )
    parser.add_argument(
        "--markdown-location", "-m", help="Markdown output folder (overrides config)"
    )
    args = parser.parse_args()

    # Configure logging and write artist markdown files from the most recent saved data
    setup_app_logging(logger, logging.DEBUG)
    spotify_to_md = SpotifyToMarkdown(markdown_location=args.markdown_location)

    # Determine where the raw zipped data is stored and pick the most recent complete folder
    raw_data_location = get_data_location()
    most_recent = most_recent_directory(raw_data_location)
    logger.debug(f"Most recent directory: {most_recent}")
    zip_folder = f"{raw_data_location}/{most_recent}"

    # Unzip and write artist markdown files
    saved_artists = unzip_data_from_zip(f"{zip_folder}/saved_artists.gz")
    spotify_to_md.save_artists(saved_artists)

    # Unzip and write album markdown files (if present)
    try:
        saved_albums = unzip_data_from_zip(f"{zip_folder}/saved_albums.gz")
        spotify_to_md.save_albums(saved_albums)
    except Exception:
        logger.debug(
            "No saved_albums.gz found or failed to read albums; skipping album export"
        )


if __name__ == "__main__":
    main()
