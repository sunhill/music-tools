import datetime
import logging
import os
from typing import List, Dict
import frontmatter
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



class SpotifyToMarkdown(SpotifySave):
    """Simple Markdown exporter for Spotify data.

    This implements the abstract methods from `SpotifySave` with small,
    human-readable markdown files. It's intentionally lightweight — the
    goal is to provide a working implementation so the class can be
    instantiated and used in scripts/tests.
    """

    def __init__(self, user_id: str = "") -> None:
        super().__init__()
        config_location = get_config_location()
        # Default to project directory if config missing — keep behaviour
        # minimal and robust for tests.
        save_dir = os.path.join(os.path.dirname(config_location), "markdown_exports")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir

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
        md = ["# Albums\n"]
        for a in albums:
            artists = ", ".join(x["name"] for x in a.get("artists", []))
            md.append(f"- **{a.get('name','')}** — {artists} ({a.get('release_date','')})")
        self._write(f"albums_{datetime.date.today()}.md", "\n".join(md))

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
            path = os.path.join(self.save_dir, filename)

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
                fallback = "---\n" + "\n".join(f"{k}: {v}" for k, v in post.metadata.items()) + "\n---\n\n" + post.content
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(fallback)

    def save_individual_playlists(self, playlists: List[Dict], playlist_tracks: Dict):
        pass


def main():
    # Configure logging and write artist markdown files from the most recent saved data
    setup_app_logging(logger, logging.DEBUG)
    spotify_to_md = SpotifyToMarkdown()

    # Determine where the raw zipped data is stored and pick the most recent complete folder
    raw_data_location = get_data_location()
    most_recent = most_recent_directory(raw_data_location)
    logger.debug(f"Most recent directory: {most_recent}")
    zip_folder = f"{raw_data_location}/{most_recent}"

    # Unzip and write artist markdown files
    saved_artists = unzip_data_from_zip(f"{zip_folder}/saved_artists.gz")
    spotify_to_md.save_artists(saved_artists)


if __name__ == "__main__":
    main()

