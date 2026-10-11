import sqlite3
from pathlib import Path

CACHE_FILENAME = "media_tag_cache.sqlite3"
LEGACY_CACHE_FILENAME = ".media_tag_cache.sqlite3"


class MediaTagSearcher:
    def __init__(self, directory_path):
        self.directory = Path(directory_path).resolve()
        if not self.directory.is_dir():
            raise NotADirectoryError(self.directory)

        self.cache_path = self.directory / CACHE_FILENAME
        legacy_cache_path = self.directory / LEGACY_CACHE_FILENAME
        if not self.cache_path.exists() and legacy_cache_path.exists():
            legacy_cache_path.rename(self.cache_path)
            for suffix in ("-wal", "-shm"):
                legacy_sidecar = Path(f"{legacy_cache_path}{suffix}")
                if legacy_sidecar.exists():
                    legacy_sidecar.rename(Path(f"{self.cache_path}{suffix}"))

        self.connection = sqlite3.connect(self.cache_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self._create_schema()
        self._load_index()

    @staticmethod
    def parse_tags(txt_file):
        """Read a tag file as normalized tag:value pairs and standalone tags."""
        key_values = {}
        single_tags = set()

        with open(txt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key_values[key.strip().lower()] = val.strip().lower()
                else:
                    single_tags.add(line.lower())

        return key_values, single_tags

    def _create_schema(self):
        with self.connection:
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS media_files (
                    txt_path TEXT PRIMARY KEY,
                    media_path TEXT NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    size INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tags (
                    txt_path TEXT NOT NULL REFERENCES media_files(txt_path)
                        ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    value TEXT NOT NULL,
                    is_key_value INTEGER NOT NULL,
                    PRIMARY KEY (txt_path, tag, value, is_key_value)
                );
                CREATE INDEX IF NOT EXISTS tags_lookup
                    ON tags (tag, value, is_key_value);
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """)
            version = self.connection.execute(
                "SELECT value FROM cache_metadata WHERE key = 'version'"
            ).fetchone()
            if version is None or version[0] != "1":
                self.connection.execute("DELETE FROM tags")
                self.connection.execute("DELETE FROM media_files")
                self.connection.execute("""
                    INSERT INTO cache_metadata (key, value) VALUES ('version', '1')
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """)

    def _load_index(self):
        with self.connection:
            self.connection.execute(
                "CREATE TEMP TABLE IF NOT EXISTS seen_files (txt_path TEXT PRIMARY KEY)"
            )
            self.connection.execute("DELETE FROM seen_files")

            for txt_file in self.directory.rglob("*.txt"):
                media_file = txt_file.with_suffix("")
                if not media_file.is_file():
                    continue

                relative_txt = txt_file.relative_to(self.directory).as_posix()
                relative_media = media_file.relative_to(self.directory).as_posix()
                stat = txt_file.stat()
                cached_entry = self.connection.execute(
                    """
                    SELECT media_path, mtime_ns, size
                    FROM media_files WHERE txt_path = ?
                    """,
                    (relative_txt,),
                ).fetchone()
                self.connection.execute(
                    "INSERT INTO seen_files (txt_path) VALUES (?)",
                    (relative_txt,),
                )

                if cached_entry == (relative_media, stat.st_mtime_ns, stat.st_size):
                    continue

                key_values, single_tags = self.parse_tags(txt_file)
                self.connection.execute(
                    """
                    INSERT INTO media_files (txt_path, media_path, mtime_ns, size)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(txt_path) DO UPDATE SET
                        media_path = excluded.media_path,
                        mtime_ns = excluded.mtime_ns,
                        size = excluded.size
                    """,
                    (relative_txt, relative_media, stat.st_mtime_ns, stat.st_size),
                )
                self.connection.execute(
                    "DELETE FROM tags WHERE txt_path = ?", (relative_txt,)
                )
                self.connection.executemany(
                    """
                    INSERT INTO tags (txt_path, tag, value, is_key_value)
                    VALUES (?, ?, ?, ?)
                    """,
                    [(relative_txt, tag, "", 0) for tag in single_tags]
                    + [
                        (relative_txt, tag, value, 1)
                        for tag, value in key_values.items()
                    ],
                )

            self.connection.execute("""
                DELETE FROM media_files
                WHERE NOT EXISTS (
                    SELECT 1 FROM seen_files
                    WHERE seen_files.txt_path = media_files.txt_path
                )
                """)

    def search(self, query_tag, query_value=None):
        """Search tags with optional * (any length) and ? (single character) wildcards."""
        query_tag = query_tag.strip().lower()
        where_clauses = []
        parameters = []
        if "*" in query_tag or "?" in query_tag:
            where_clauses.append("tag LIKE ? ESCAPE '!'")
            parameters.append(self._to_like_pattern(query_tag))
        else:
            where_clauses.append("tag = ?")
            parameters.append(query_tag)

        if query_value is not None:
            query_value = query_value.strip().lower()
            if "*" in query_value or "?" in query_value:
                where_clauses.append("value LIKE ? ESCAPE '!'")
                parameters.append(self._to_like_pattern(query_value))
            else:
                where_clauses.append("value = ?")
                parameters.append(query_value)
            where_clauses.append("is_key_value = 1")

        rows = self.connection.execute(
            f"""
            SELECT DISTINCT media_path FROM tags
            JOIN media_files USING (txt_path)
            WHERE {" AND ".join(where_clauses)}
            ORDER BY media_path
            """,
            parameters,
        )
        return [self.directory / row[0] for row in rows]

    @staticmethod
    def _to_like_pattern(query):
        """Translate * and ? wildcards, escaping SQLite LIKE metacharacters."""
        pattern = []
        for character in query:
            if character == "*":
                pattern.append("%")
            elif character == "?":
                pattern.append("_")
            elif character in "!%_":
                pattern.append("!" + character)
            else:
                pattern.append(character)
        return "".join(pattern)

    def get_tags(self, media_path):
        """Return the tags cached for a media file as display-ready strings."""
        relative_path = (
            Path(media_path).resolve().relative_to(self.directory).as_posix()
        )
        rows = self.connection.execute(
            """
            SELECT tag, value, is_key_value
            FROM tags
            JOIN media_files USING (txt_path)
            WHERE media_path = ?
            ORDER BY tag, is_key_value, value
            """,
            (relative_path,),
        )
        return [
            f"{tag}:{value}" if is_key_value else tag
            for tag, value, is_key_value in rows
        ]

    def format_result(self, media_path):
        """Format a result as a clickable terminal file link followed by its tags."""
        media_path = Path(media_path).resolve()
        link = f"\033]8;;{media_path.as_uri()}\033\\Open file\033]8;;\033\\"
        tags = ", ".join(self.get_tags(media_path))
        return f"{link} [{tags}]"

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception, _traceback):
        self.close()


if __name__ == "__main__":
    # media_dir = "./my_media_collection"
    media_dir = "/Users/simon/Downloads/hydrex"
    with MediaTagSearcher(media_dir) as searcher:
        for match in searcher.search("character", "superman"):
            print(searcher.format_result(match))
