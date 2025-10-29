import gzip
import json
import logging
import os
import sys
from configparser import ConfigParser
from logging.handlers import RotatingFileHandler
from typing import Iterator

import psutil
import spotipy
from spotipy import (
    Spotify,
    SpotifyClientCredentials,
    SpotifyOAuth,
    MemoryCacheHandler,
)

UNIQUE_PLAYLIST_ARTISTS = "unique_playlist_artists"
UNIQUE_PLAYLIST_TRACKS = "unique_playlist_tracks"
PLAYLIST_TRACKS = "playlist_trm_tacks"
OTHER_PLAYLIST_TRACKS = "other_playlist_tracks"
PLAYLISTS = "playlists"
OTHER_PLAYLISTS = "other_playlists"
SAVED_TRACKS = "saved_tracks"
SAVED_ARTISTS = "saved_artists"
SAVED_ALBUMS = "saved_albums"
SAVED_ALBUM_TRACKS = "saved_album_tracks"
USER_ID = "user_id"

linebreak = "\r\n"
separator = "\t"

logger = logging.getLogger(__name__)

async def get_data_location():
    config_location = get_config_location()
    logger.info(f"Using config file {config_location}")
    config_parser = ConfigParser()
    config_parser.read(config_location)
    running_in_docker = os.getenv("RUNNING_IN_DOCKER", "False")
    logger.info(f"Running in docker: {running_in_docker}")
    if running_in_docker == "True":
        save_location = "/src/data/"
    else:
        save_location = config_parser["spotify"]["save_location"]
    # list files
    logger.info(f"Using save location {save_location}")
    spotify_user = config_parser["spotify"]["spotify_user"]
    logger.info(f"Using Spotify user {spotify_user}")
    raw_data_folder = config_parser["spotify"]["raw_data_location"]
    raw_data_location = os.path.join(save_location, spotify_user, raw_data_folder)
    files = os.listdir(raw_data_location)
    logger.info(f"Files in save location: {files}")
    logger.info("Getting latest zip file")
    return raw_data_location


def get_latest_zip(dir_location: str, file_name="all_data") -> str:
    logger.debug(f"Getting latest zip file from {dir_location}")
    res = []
    walk: Iterator[tuple[str, list[str], list[str]]] = os.walk(dir_location)
    first_walk: tuple[str, list[str], list[str]] = next(walk)
    sub_dirs: list[str] = first_walk[1]
    sub_dirs = sorted(sub_dirs, reverse=True)

    most_recent_dir = sub_dirs[0]
    logger.debug(f"Most recent directory: {most_recent_dir}")

    for path in os.listdir(os.path.join(dir_location, most_recent_dir)):
        isfile = os.path.isfile(os.path.join(dir_location, most_recent_dir, path))
        endswith = path.endswith(f"{file_name}.gz")
        if isfile and endswith:
            res.append(path)
    res = sorted(res, reverse=True)
    print(res)
    if len(res) == 0:
        return ""

    return os.path.join(dir_location, most_recent_dir, res[0])


def get_latest_zips(dir_location: str) -> list[str]:
    res = []
    most_recent_dir = most_recent_directory(dir_location)

    for path in os.listdir(os.path.join(dir_location, most_recent_dir)):
        if os.path.isfile(
            os.path.join(dir_location, most_recent_dir, path)
        ) and path.endswith(".gz"):
            res.append(os.path.join(dir_location, most_recent_dir, path))

    return res

def most_recent_directory(dir_location):
    walk: Iterator[tuple[str, list[str], list[str]]] = os.walk(dir_location)
    first_walk: tuple[str, list[str], list[str]] = next(walk)
    sub_dirs: list[str] = first_walk[1]
    sub_dirs = sorted(sub_dirs, reverse=True)
    most_recent_dir = sub_dirs[0]
    return most_recent_dir


def zip_data(data, data_type, data_location):
    logger.debug(f"Zipping data of type {data_type} to {data_location}")
    save_dir = f"{data_location}"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    json_string = json.dumps(data, ensure_ascii=False, indent=4)
    logger.debug(f"Data size before compression: {len(json_string)} bytes")
    get_memory_usage()
    zip_filename = f"{data_location}/{data_type}.gz"
    with gzip.open(zip_filename, "wb", compresslevel=5) as handle:
        handle.write(json_string.encode('utf-8'))
    logger.debug(f"Data compressed to {zip_filename}")


def unzip_data(data_location):
    logger.debug(f"Unzipping data from {data_location}")
    all_data = {}
    zip_filenames = get_latest_zips(data_location)
    for zip_filename in zip_filenames:
        if zip_filename == "all_data.gz":
            continue
        data_type = zip_filename.split("/")[-1].split(".")[0]
        all_data[data_type] = unzip_data_from_zip(zip_filename)
    return all_data


def unzip_data_from_zip(zip_filename):
    logger.debug(f"Unzipping data from {zip_filename}")
    get_memory_usage()
    with open(zip_filename, "rb") as handle:
        get_memory_usage()
        read = gzip.decompress(handle.read()).decode('utf-8')
        data = json.loads(read)
        logger.debug(f"Decompressed data size: {len(data)}")
        get_memory_usage()
        logger.debug(f"Data loaded from {zip_filename}")
    get_memory_usage()

    return data


def get_spotify_wrapper(scope):
    logger.info("Getting Spotify wrapper")
    # TODO central place for config
    config_parser: ConfigParser = ConfigParser()
    config_parser.read(get_config_location())
    os.environ["SPOTIPY_CLIENT_ID"] = config_parser["spotify"]["spotify_consumer_key"]
    os.environ["SPOTIPY_CLIENT_SECRET"] = config_parser["spotify"]["spotify_secret_key"]
    os.environ["SPOTIPY_REDIRECT_URI"] = config_parser["spotify"][
        "spotify_redirect_uri"
    ]
    print(config_parser["spotify"]["spotify_consumer_key"])
    print(config_parser["spotify"]["spotify_secret_key"])
    print(config_parser["spotify"]["spotify_redirect_uri"])
    print(os.getenv("SPOTIPY_CLIENT_ID"))
    print(os.getenv("SPOTIPY_CLIENT_SECRET"))
    print(os.getenv("SPOTIPY_REDIRECT_URI"))
    cache_handler = MemoryCacheHandler()

    #     http://127.0.0.1:43019/redirect
    #     http://localhost:8888/callback/

    # os.environ["SPOTIPY_REDIRECT_URI"] = "http://host.docker.internal:43019/redirect"
    # os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:43019/redirect"
    # os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:43019/redirect"
    # os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:8001/redirect"
    print(os.getenv("SPOTIPY_REDIRECT_URI"))
    spotify: Spotify = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(),
        auth_manager=SpotifyOAuth(
            scope=scope,
            cache_handler=cache_handler,
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        ),
        requests_timeout=30,
    )
    logger.info("Logged in as {display_name} ({id})".format(**(spotify.me())))

    return spotify


def setup_app_logging(a_logger, log_level=logging.DEBUG):
    a_logger.setLevel(log_level)
    simple_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(simple_formatter)
    a_logger.addHandler(stream_handler)
    file_handler = RotatingFileHandler("../spotify.log")
    file_handler.setFormatter(simple_formatter)
    a_logger.addHandler(file_handler)


def get_memory_usage():
    # Get the memory usage in bytes
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss
    # Convert to megabytes
    memory_usage_mb = memory_usage / (1024**2)
    # Log the memory usage
    logger.info(f"memory usage {memory_usage_mb}")
    return memory_usage_mb


def get_config_location():
    config_location = os.getenv(
        "SPOTIFY_CONFIG_LOCATION", "src/app_config/app_config.ini"
    )
    logger.info(f"Using config file {config_location}")
    return config_location
