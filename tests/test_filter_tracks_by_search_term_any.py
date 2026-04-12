import os
import sys
import pytest

# Ensure project src is on sys.path so we can import the module under test
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from spotify.spotify_playlist_maker import SpotifyPlaylistMaker


def make_track(name, id_="id"):
    return {"name": name, "id": id_}


def test_single_word_matches_whole_word_only():
    tracks = [make_track("The Storm"), make_track("Stormy Weather")]

    # searching for 'storm' should match only the track with the exact token 'Storm'
    results = SpotifyPlaylistMaker.filter_tracks_by_search_term_any(tracks, ["storm"])
    names = [t["name"] for t in results]
    assert "The Storm" in names
    assert "Stormy Weather" not in names


def test_phrase_match_and_ignore_question_mark():
    tracks = [make_track("Ice Cream? (Vanilla)"), make_track("Vanilla Ice")]

    # phrase should match despite punctuation
    results = SpotifyPlaylistMaker.filter_tracks_by_search_term_any(
        tracks, ["ice cream"]
    )
    names = [t["name"] for t in results]
    assert "Ice Cream? (Vanilla)" in names
    assert "Vanilla Ice" not in names


def test_apostrophe_word_matching_and_case_insensitive():
    tracks = [make_track("Don't Stop Believin'"), make_track("Dont Stop")]

    # searching for don't (case-insensitive, with apostrophe) should match
    results = SpotifyPlaylistMaker.filter_tracks_by_search_term_any(tracks, ["don't"])
    names = [t["name"] for t in results]
    assert "Don't Stop Believin'" in names

    # searching for dont (without apostrophe) should not match the "Don't" track
    results2 = SpotifyPlaylistMaker.filter_tracks_by_search_term_any(tracks, ["dont"])
    names2 = [t["name"] for t in results2]
    assert "Don't Stop Believin'" not in names2


def test_multiple_terms_any_behavior():
    tracks = [
        make_track("Ice Cream"),
        make_track("Chocolate Cake"),
        make_track("Strawberry Tart"),
    ]

    results = SpotifyPlaylistMaker.filter_tracks_by_search_term_any(
        tracks, ["ice cream", "chocolate"]
    )
    names = {t["name"] for t in results}
    assert names == {"Ice Cream", "Chocolate Cake"}


def test_no_substring_false_positive():
    tracks = [make_track("Artist Name"), make_track("The Art of Noise")]

    results = SpotifyPlaylistMaker.filter_tracks_by_search_term_any(tracks, ["art"])
    names = [t["name"] for t in results]

    # should match the standalone word 'Art' but not the substring inside 'Artist'
    assert "The Art of Noise" in names
    assert "Artist Name" not in names
