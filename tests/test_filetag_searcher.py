from utils.filetag_searcher import (
    CACHE_FILENAME,
    LEGACY_CACHE_FILENAME,
    MediaTagSearcher,
)


def test_search_indexes_paired_files_recursively(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    image = nested / "picture.jpg"
    image.touch()
    (nested / "picture.jpg.txt").write_text(
        "favorite\ncategory: landscape\n", encoding="utf-8"
    )
    video = tmp_path / "clip.mp4"
    video.touch()
    (tmp_path / "clip.mp4.txt").write_text("category: portrait\n", encoding="utf-8")
    (tmp_path / "orphan.txt").write_text("favorite\n", encoding="utf-8")

    with MediaTagSearcher(tmp_path) as searcher:
        assert searcher.search("favorite") == [image]
        assert searcher.search("category") == [video, image]
        assert searcher.search("category", "landscape") == [image]
        assert searcher.get_tags(image) == ["category:landscape", "favorite"]
        formatted = searcher.format_result(image)
        assert f"\033]8;;{image.as_uri()}\033\\Open file\033]8;;\033\\" in formatted
        assert "\033]8;;\033\\" + str(image) not in formatted
        assert formatted.endswith("[category:landscape, favorite]")
    assert (tmp_path / CACHE_FILENAME).is_file()


def test_search_supports_wildcards_in_tags_and_values(tmp_path):
    filenames_and_tags = {
        "landscape.jpg": "category: landscape\n",
        "landscape-night.jpg": "category: landscape at night\n",
        "portrait.jpg": "category: portrait\n",
        "favorite.jpg": "favorite\n",
    }
    for filename, tags in filenames_and_tags.items():
        (tmp_path / filename).touch()
        (tmp_path / f"{filename}.txt").write_text(tags, encoding="utf-8")

    with MediaTagSearcher(tmp_path) as searcher:
        assert searcher.search("categ*") == [
            tmp_path / "landscape-night.jpg",
            tmp_path / "landscape.jpg",
            tmp_path / "portrait.jpg",
        ]
        assert searcher.search("category", "land*") == [
            tmp_path / "landscape-night.jpg",
            tmp_path / "landscape.jpg",
        ]
        assert searcher.search("category", "p?rtrait") == [tmp_path / "portrait.jpg"]
        assert searcher.search("favorit?") == [tmp_path / "favorite.jpg"]


def test_cache_refreshes_when_tag_file_changes(tmp_path):
    media = tmp_path / "photo.png"
    media.touch()
    tags = tmp_path / "photo.png.txt"
    tags.write_text("old-tag\n", encoding="utf-8")

    with MediaTagSearcher(tmp_path) as first_searcher:
        assert first_searcher.search("old-tag") == [media]

    tags.write_text("new-tag\n", encoding="utf-8")
    with MediaTagSearcher(tmp_path) as second_searcher:
        assert second_searcher.search("old-tag") == []
        assert second_searcher.search("new-tag") == [media]


def test_existing_hidden_cache_is_moved_to_visible_filename(tmp_path):
    media = tmp_path / "photo.png"
    media.touch()
    (tmp_path / "photo.png.txt").write_text("favorite\n", encoding="utf-8")

    with MediaTagSearcher(tmp_path) as searcher:
        assert searcher.search("favorite") == [media]

    visible_cache = tmp_path / CACHE_FILENAME
    visible_cache.rename(tmp_path / LEGACY_CACHE_FILENAME)

    with MediaTagSearcher(tmp_path) as searcher:
        assert searcher.search("favorite") == [media]

    assert visible_cache.is_file()
    assert not (tmp_path / LEGACY_CACHE_FILENAME).exists()
