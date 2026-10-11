# Media Tag Search

`filetag_searcher.py` searches image and video files using tags stored in paired
text files. A media file named `photo.jpg` must have a tag file named
`photo.jpg.txt` beside it. Tag files contain one tag per line:

```text
favorite
category: landscape
description: mountain lake at sunrise
```

Tag names and values are trimmed and matched case-insensitively. Files are
searched recursively under the directory passed to `MediaTagSearcher`.
Unpaired text files are ignored.

## Supported searches

Use `search(tag, value=None)` for one exact or wildcard search. With one
argument, `search()` also accepts a quoted `tag:value` term or a full boolean
expression:

```python
searcher.search("favorite")                  # standalone tag
searcher.search("category", "landscape")     # exact tag:value pair
searcher.search("category", "land*")         # wildcard value
searcher.search("favorit?")                  # wildcard tag
searcher.search('character:"judge dredd"')   # quoted tag value with spaces
```

Use `search_query(expression)` for boolean expressions made from standalone
tags and `tag:value` terms:

```python
searcher.search_query("favorite AND category:landscape")
searcher.search_query("category:landscape OR category:portrait")
searcher.search_query("category:landscape NOT archived")
searcher.search_query("character:superman AND (format:comic OR favorite)")
searcher.search_query('description:"mountain lake at sunrise"')
searcher.search_query("category:land* AND NOT favorite")
```

`AND`, `OR`, and `NOT` are case-insensitive. `NOT` is unary; `AND` has higher
precedence than `OR`. Parentheses group expressions. Adjacent terms imply
`AND`, so `cat NOT fish` means `cat AND NOT fish`. Quote values containing
spaces, as in `description:"mountain lake at sunrise"`.

The `*` wildcard matches zero or more characters; `?` matches exactly one
character. Wildcards work in tag names and values. Without wildcards, a term
must match exactly.

Queries return media paths sorted by path. A `NOT` expression excludes matching
files from the set of indexed, paired media files.

## Python usage

From the repository root, set `PYTHONPATH` so the `src` package is importable:

```bash
export PYTHONPATH=src
```

Then use the searcher as a context manager:

```python
from utils.filetag_searcher import MediaTagSearcher

with MediaTagSearcher("/path/to/media_collection") as searcher:
    matches = searcher.search_query(
        'category:landscape AND (favorite OR rating:high) NOT archived'
    )
    for path in matches:
        print(searcher.format_result(path))
```

`format_result(path)` displays a clickable terminal link followed by that
file's tags. Terminal support for clickable links depends on the terminal
application.

## Cache

The searcher creates `media_tag_cache.sqlite3` in the collection root. On
initialization, it recursively scans paired text files, reuses cached entries
whose modification time and size have not changed, updates changed entries,
and removes entries for deleted or unpaired sidecars. Keep the cache file with
the collection between runs. Use `with` (or call `close()`) to close the
SQLite database cleanly.
