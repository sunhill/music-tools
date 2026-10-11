from storage.file.spotify_save_to_file import SpotifyToFile
from storage.markdown.spotify_save_to_markdown import (
    sanitize_album_name_for_filename,
)


def test_playlist_markdown_uses_artist_track_year_duration_format(tmp_path):
    tracks = [
        {
            "name": "Song Name",
            "artists": [{"name": "Artist One"}],
            "album": {
                "name": "Album Name",
                "release_date": "2024-05-15",
                "release_date_precision": "day",
            },
            "duration_ms": 222000,
        }
    ]

    markdown_path = tmp_path / "Sample_Playlist.md"
    SpotifyToFile.write_playlist_markdown(str(markdown_path), "Sample Playlist", tracks)

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Sample Playlist" in markdown
    assert "- Artist One - Song Name (2024) [3:42]" in markdown


def test_playlist_markdown_filename_pattern_is_configurable():
    filename = SpotifyToFile.get_playlist_markdown_filename(
        "Sample Playlist",
        "abc123",
        "2026-10-11",
        "{playlist_name}_{date}{extension}",
    )
    assert filename == "Sample Playlist_2026-10-11.md"


def test_existing_playlist_csv_is_converted_to_markdown(tmp_path):
    csv_path = tmp_path / "Sample_Playlist_abc123_2026-10-11.csv"
    csv_path.write_text(
        "\ufeffArtist,Track,Album,Spotify_URI,ID,Playlist,Release_Year,"
        "Release_Date,Release_Date_Precision,Track_Length_min\n"
        "Artist One,Song Name,Album Name,spotify:track:1,1,Sample Playlist,"
        "2024,2024-05-15,day,3:42\n",
        encoding="utf-8",
    )

    SpotifyToFile.convert_existing_playlist_csvs_to_markdown(str(tmp_path))

    markdown_path = tmp_path / "Sample_Playlist_abc123_2026-10-11.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Sample Playlist" in markdown
    assert "- Artist One - Song Name (2024) [3:42]" in markdown


def test_sanitize_album_name_remaster_variants():
    cases = {
        "The Album (Remastered 2020)": "The Album",
        "Greatest Hits [Deluxe Remaster]": "Greatest Hits",
        "Some Album {Remaster}": "Some Album",
        "Foo (Remastered) - Deluxe": "Foo - Deluxe",
        "Bar [Remastered Edition]": "Bar",
        "Anniversary (Expanded Edition)": "Anniversary",
        "Hits [Deluxe Edition]": "Hits",
        "Special Album (Special Edition)": "Special Album",
        "Remix [Version 2]": "Remix",
    }

    for inp, expected in cases.items():
        assert sanitize_album_name_for_filename(inp) == expected


def test_sanitize_album_name_no_change():
    # Names without remaster keywords should be preserved (except trimming)
    assert sanitize_album_name_for_filename("Original Album") == "Original Album"
    assert sanitize_album_name_for_filename("Live Album (Live)") == "Live Album (Live)"
