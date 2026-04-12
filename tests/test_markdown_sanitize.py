from storage.markdown.spotify_save_to_markdown import (
    sanitize_album_name_for_filename,
)


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


