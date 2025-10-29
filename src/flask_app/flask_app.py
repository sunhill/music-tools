import asyncio
import logging
import zlib
from configparser import ConfigParser
from typing import List

from flask import Flask, jsonify, render_template, url_for, redirect
from json2html import json2html

from spotify.spotify_get_data_non_async import SpotifyDataGetter
from spotify.spotify_playlist_maker import SpotifyPlaylistMaker
from spotify.spotify_utils import (
    get_latest_zip,
    setup_app_logging,
    get_config_location,
)
from storage.file.spotify_save_to_file import SpotifyToFile
from storage.mongo.spotify_read_from_mongo import SpotifyFromMongo
from storage.mongo.spotify_save_to_mongo import SpotifyToMongo

app = Flask(__name__, template_folder="templates", static_folder="static")
app.app_context()
app.debug = True

config_parser = ConfigParser()
config_parser.read(get_config_location())

save_location = config_parser["spotify"]["save_location"]
raw_data_location = save_location + config_parser["spotify"]["raw_data_location"]

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
setup_app_logging(logger, logging.DEBUG)


async def load_data():
    logger.info("getting zip")
    all_data_zip_filename = get_latest_zip(raw_data_location)
    with open(all_data_zip_filename, "rb") as handle:
        logger.info("unzipping data from zip")
        all_data = zlib.decompress(handle.read())
        logger.info("zip data loaded")
    return all_data


@app.route("/test", methods=["GET"])
def check_app():
    logger.debug("test")
    return jsonify({"message": "It works!"})


@app.route("/")
def index():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != "static":
            route = {"url": url_for(rule.endpoint), "endpoint": rule.endpoint}
            routes.append(route)
    return render_template("index.html", routes=routes)


@app.route("/liked_albums", methods=["GET"], endpoint="liked_albums")
def get_albums():
    items: List[dict] = app.spotify_from_mongo.get_liked_albums()

    return convert_json_to_html(items)


@app.route("/liked_artists", methods=["GET"], endpoint="liked_artists")
def get_artists():
    items: List[dict] = app.spotify_from_mongo.get_liked_artists()

    return convert_json_to_html(items)


@app.route("/liked_tracks", methods=["GET"], endpoint="liked_tracks")
def get_tracks():
    items: List[dict] = app.spotify_from_mongo.get_liked_tracks()

    return convert_json_to_html(items)


@app.route("/playlists", methods=["GET"], endpoint="playlists")
def get_playlists():
    items: List[dict] = app.spotify_from_mongo.get_playlists()

    return convert_json_to_html(items)


@app.route(
    "/unique_playlist_tracks", methods=["GET"], endpoint="unique_playlist_tracks"
)
def get_unique_playlist_tracks():
    items: List[dict] = app.spotify_from_mongo.get_unique_playlist_tracks()

    return convert_json_to_html(items)


@app.route("/playlist_tracks", methods=["GET"], endpoint="playlist_tracks")
def get_playlist_tracks():
    items: List[dict] = app.spotify_from_mongo.get_playlist_tracks()

    return convert_json_to_html(items)


@app.route(
    "/unique_playlist_artists", methods=["GET"], endpoint="unique_playlist_artists"
)
def get_playlist_unique_artists():
    items: List[dict] = app.spotify_from_mongo.get_playlist_unique_artists()

    return convert_json_to_html(items)


@app.route("/liked_album_tracks", methods=["GET"], endpoint="liked_album_tracks")
def get_album_tracks():
    items: List[dict] = app.spotify_from_mongo.get_liked_album_tracks()

    return convert_json_to_html(items)


def convert_json_to_html(json_data):
    table_style = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }

        th, td {
            border: 1px solid black;
            padding: 8px;
        }

        th {
            background-color: #f2f2f2;
        }
    </style>
    """
    html_table = json2html.convert(json=json_data)
    formatted_table = f"{table_style}<table>{html_table}</table>"
    return formatted_table


@app.route("/spotify_get_all_data", methods=["GET"], endpoint="spotify_get_all_data")
def spotify_get_data():
    logger.debug("getting data")
    spotify_data_getter: SpotifyDataGetter = SpotifyDataGetter()
    all_data = spotify_data_getter.get_all_data()
    logger.debug("pickling data")
    spotify_data_getter.zip_data(all_data)
    logger.debug("zipd data")


@app.route("/save_data_to_mongodb", methods=["GET"], endpoint="save_data_to_mongodb")
def save_to_mongo():
    logger.debug("saving to mongo")
    spotify_to_mongodb: SpotifyToMongo = SpotifyToMongo()
    spotify_to_mongodb.save_all_data(app.all_data)
    logger.debug("saved to mongo")
    return redirect(url_for("index"))


@app.route(
    "/save_data_to_spreadsheets", methods=["GET"], endpoint="save_data_to_spreadsheets"
)
def save_to_file():
    logger.debug("saving to file")
    spotify_to_file: SpotifyToFile = SpotifyToFile()

    spotify_to_file.save_all_data(app.all_data)
    logger.debug("saved to file")
    return redirect(url_for("index"))


@app.route(
    "/fetch_and_save_data_to_spreadsheets",
    methods=["GET"],
    endpoint="fetch_and_save_data_to_spreadsheets",
)
def fetch_and_save_data_to_spreadsheets():
    logger.debug("getting data")

    spotify_data_getter: SpotifyDataGetter = SpotifyDataGetter()
    all_data = spotify_data_getter.get_all_data()
    logger.debug("zipping data")
    spotify_data_getter.zip_data(all_data)
    logger.debug("zipd data")

    logger.debug("saving to file")

    spotify_to_file: SpotifyToFile = SpotifyToFile()
    all_data_zip_filename = get_latest_zip(spotify_to_file.raw_data_location)

    with open(all_data_zip_filename, "rb") as handle:
        all_data = zip.load(handle)

    spotify_to_file.save_all_data(all_data)
    return redirect(url_for("index"))


@app.route("/make_playlist_2023", methods=["GET"], endpoint="make_playlist_2023")
def make_playlist_2023():
    logger.debug("making playlist 2023")
    app.playlist_maker.create_playlists_by_year(
        tracks=app.playlist_maker.saved_tracks,
        start_year=2023,
        end_year=2023,
        playlist_prefix="Liked",
    )
    # return jsonify({"message": "Saved OK"})
    logger.debug("made playlist 2023")
    return redirect(url_for("index"))


@app.route("/make_playlist_2024", methods=["GET"], endpoint="make_playlist_2024")
def make_playlist_2024():
    logger.debug("making playlist 2024")
    app.playlist_maker.create_playlists_by_year(
        tracks=app.playlist_maker.saved_tracks,
        start_year=2024,
        end_year=2024,
        playlist_prefix="Liked",
    )
    logger.debug("made playlist 2024")
    return redirect(url_for("index"))


@app.route(
    "/make_playlists_by_year",
    methods=["GET"],
    endpoint="make_playlists_by_year",
)
def make_playlists_by_year():
    logger.debug("making playlists by year")
    app.playlist_maker.create_playlists_by_year(
        tracks=app.playlist_maker.saved_tracks,
        start_year=1955,
        end_year=2024,
        playlist_prefix="Liked",
    )
    logger.debug("made playlists by year")
    return redirect(url_for("index"))


@app.route(
    "/make_playlists_by_decade",
    methods=["GET"],
    endpoint="make_playlists_by_decade",
)
def make_playlists_by_decade():
    logger.debug("making playlists by decade")
    app.playlist_maker.create_playlists_by_decade(
        tracks=app.playlist_maker.saved_tracks,
        start_year=193,
        end_year=202,
        playlist_prefix="Liked",
    )
    logger.debug("made playlists by decade")
    return redirect(url_for("index"))


@app.route(
    "/make_random_playlist",
    methods=["GET"],
    endpoint="make_random_playlist",
)
def make_random_playlist():
    logger.debug("making random playlist")
    playlist_name = "Random Playlist from Liked Stuff"
    number_of_songs = 1000
    from_albums = 0.5
    from_tracks = 0.5
    from_playlists = 0.0
    app.playlist_maker.create_random_playlist(
        number_of_songs=number_of_songs,
        from_albums=from_albums,
        from_tracks=from_tracks,
        from_playlists=from_playlists,
        playlist_name=playlist_name,
    )
    logger.debug("made random playlist")
    return redirect(url_for("index"))


@app.route(
    "/combine_all_top_playlists",
    methods=["GET"],
    endpoint="combine_all_top_playlists",
)
def combine_all_top_playlists():
    logger.debug("combining all top playlists")
    app.playlist_maker.combine_all_top_playlists()
    logger.debug("combined all top playlists")
    return redirect(url_for("index"))


@app.route(
    "/update_liked_album_playlists",
    methods=["GET"],
    endpoint="update_liked_album_playlists",
)
def update_liked_album_playlists():
    logger.debug("updating liked album playlists")
    app.playlist_maker.create_playlists_from_liked_albums()
    logger.debug("updated liked album playlists")
    return redirect(url_for("index"))


@app.route(
    "/update_main_liked_album_playlist",
    methods=["GET"],
    endpoint="update_main_liked_album_playlist",
)
def update_liked_album_playlist():
    logger.debug("updating main liked album playlist")
    app.playlist_maker.create_playlist_from_liked_albums()
    logger.debug("updated main liked album playlist")
    return redirect(url_for("index"))


async def setup():
    logger.info("Setting up")
    app.all_data = await load_data()
    app.spotify_from_mongo = SpotifyFromMongo()
    app.spotify_from_mongo.all_data = app.all_data
    app.playlist_maker = SpotifyPlaylistMaker(use_zip=False, get_data=False)
    app.playlist_maker.all_data = app.all_data
    app.playlist_maker.setup_data_collections()


async def main():
    await setup()

    app.run(use_reloader=False)


if __name__ == "__main__":
    # main()
    # setup_app_logging(logger, logging.DEBUG)

    asyncio.run(main())
