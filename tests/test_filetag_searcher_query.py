import pytest

from utils.filetag_searcher import MediaTagSearcher


@pytest.fixture
def boolean_searcher(tmp_path):
    media_tags = {
        "cat-dog.jpg": "cat\ndog\n",
        "cat-bird.jpg": "cat\nbird\n",
        "cat-fish.jpg": "cat\nfish\n",
        "dog-bird.jpg": "dog\nbird\n",
    }
    for filename, tags in media_tags.items():
        (tmp_path / filename).touch()
        (tmp_path / f"{filename}.txt").write_text(tags, encoding="utf-8")

    with MediaTagSearcher(tmp_path) as searcher:
        yield searcher


def test_search_query_handles_and_or_not_and_parentheses(boolean_searcher, tmp_path):
    assert boolean_searcher.search_query("cat AND (dog OR bird) NOT fish") == [
        tmp_path / "cat-bird.jpg",
        tmp_path / "cat-dog.jpg",
    ]
    assert boolean_searcher.search_query("NOT cat") == [tmp_path / "dog-bird.jpg"]


def test_search_query_gives_and_precedence_over_or(boolean_searcher, tmp_path):
    assert boolean_searcher.search_query("cat OR dog AND bird") == [
        tmp_path / "cat-bird.jpg",
        tmp_path / "cat-dog.jpg",
        tmp_path / "cat-fish.jpg",
        tmp_path / "dog-bird.jpg",
    ]


def test_search_query_handles_tag_values_quotes_and_wildcards(tmp_path):
    entries = {
        "landscape.jpg": "category: landscape\nfavorite\n",
        "portrait.jpg": "category: portrait\n",
        "night.jpg": "category: landscape at night\n",
    }
    for filename, tags in entries.items():
        (tmp_path / filename).touch()
        (tmp_path / f"{filename}.txt").write_text(tags, encoding="utf-8")

    with MediaTagSearcher(tmp_path) as searcher:
        assert searcher.search_query('category:"landscape at night" OR favorit?') == [
            tmp_path / "landscape.jpg",
            tmp_path / "night.jpg",
        ]
        assert searcher.search_query("category:land* AND NOT favorite") == [
            tmp_path / "night.jpg"
        ]
        assert searcher.search('category:"landscape at night"') == [
            tmp_path / "night.jpg"
        ]


@pytest.mark.parametrize("expression", ["", "cat AND", "(cat OR dog", "cat OR )"])
def test_search_query_rejects_malformed_expressions(tmp_path, expression):
    with MediaTagSearcher(tmp_path) as searcher:
        with pytest.raises(ValueError):
            searcher.search_query(expression)
