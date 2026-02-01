import logging

from spotify.spotify_playlist_maker import SpotifyPlaylistMaker
from spotify.spotify_utils import setup_app_logging

logger = logging.getLogger(__name__)


def main():
    setup_app_logging(logger, logging.DEBUG)

    spotify_playlist_maker: SpotifyPlaylistMaker = SpotifyPlaylistMaker(use_zip=True)
    make_playlists(spotify_playlist_maker)


def make_playlists(spotify_playlist_maker):
    albums = spotify_playlist_maker.saved_albums
    tracks = spotify_playlist_maker.saved_tracks
    tracks_including_album_tracks = (
        spotify_playlist_maker.saved_tracks.extend(
            spotify_playlist_maker.saved_album_tracks
        )
        or spotify_playlist_maker.saved_tracks
    )
    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=6, num_tracks_per_album=1
    # )
    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=6, num_tracks_per_album=None, playlist_name="Six Pack"
    # )

    spotify_playlist_maker.create_playlist_from_albums(
        num_albums=10,
        num_tracks_per_album=None,
        playlist_name="1970s 10 Album Pack",
        albums=[album for album in albums if "197" in album["release_date"]],
    )

    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=6,
    #     num_tracks_per_album=None,
    #     playlist_name="1970s Album Six Pack",
    #     albums=[
    #         album
    #         for album in albums
    #         if "197" in album["release_date"] and album["type"] == "album"
    #     ],
    # )

    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=6, num_tracks_per_album=None
    # )
    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=None, num_tracks_per_album=None
    # )
    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=None, num_tracks_per_album=2
    # )
    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=None, num_tracks_per_album=1
    # )
    # spotify_playlist_maker.create_playlist_from_albums(
    #     num_albums=None, num_tracks_per_album=2
    # )

    # spotify_playlist_maker.create_playlist_from_liked_tracks_and_albums(
    #     from_tracks=500, from_albums=500
    # )
    # spotify_playlist_maker.create_playlists_from_liked_albums()
    # spotify_playlist_maker.create_playlists_by_year(
    #     tracks=spotify_playlist_maker.saved_tracks,
    #     start_year=1990,
    #     end_year=2019,
    #     playlist_prefix="Liked",
    # )

    # spotify_playlist_maker.create_playlist_for_artists(["Beach Boys", "Sly & the Family Stone"], "Beach Sly",
    #                                                    spotify_playlist_maker.saved_tracks)

    # spotify_playlist_maker.create_playlist_for_artists(["Tyler, The Creator",], "Tyler",
    #                                                    spotify_playlist_maker.saved_tracks)
    #
    # spotify_playlist_maker.create_playlists_from_liked_albums()
    # get list from colours.txt

    # playlist_from_search_terms(spotify_playlist_maker, theme="colours", playlist_name="Colours", )
    # python
    tracks = (
        spotify_playlist_maker.saved_tracks.extend(
            spotify_playlist_maker.saved_album_tracks
        )
        or spotify_playlist_maker.saved_tracks
    )

    # playlist_from_search_terms(
    #     spotify_playlist_maker, theme="planets", playlist_name="Planets", tracks=tracks
    # )

    # playlist_from_search_terms(
    #     spotify_playlist_maker,
    #     theme="cities",
    #     playlist_name="Cities",
    #     tracks=tracks,
    #     terms=["London", "New York", "Tokyo", "Paris", "Berlin", "Sydney"],
    # )
    # playlist_from_search_terms(
    #     spotify_playlist_maker,
    #     theme="cities",
    #     playlist_name="Cities",
    #     tracks=tracks
    # )

    # spotify_playlist_maker.make_playlists_private(playlists)
    # spotify_playlist_maker.create_multiple_playlists_from_tracks(
    #     tracks=spotify_playlist_maker.saved_tracks,
    #     sort_by="length",
    #     playlist_prefix="Liked ",
    # )
    # spotify_playlist_maker.create_playlists_by_year(
    #     tracks=spotify_playlist_maker.saved_tracks,
    #     start_year=2010,
    #     end_year=2017,
    #     playlist_prefix="Liked",
    # spotify_playlist_maker.create_playlists_by_decade(
    #     tracks=spotify_playlist_maker.saved_tracks,
    #     start_year=193,
    #     end_year=202,
    #     playlist_prefix="Liked",
    # )

    # )
    # spotify_playlist_maker.create_playlists_by_search_term(queries=["label:4ad"],playlist_name="search_1")
    # spotify_playlist_maker.get_tracks_for_year()
    # spotify_playlist_maker.create_playlists_by_decade(
    #     spotify_playlist_maker.saved_tracks, start_year=194, end_year=202
    # )
    # spotify_playlist_maker.create_playlist_from_albums()
    # spotify_playlist_maker.create_random_playlist(
    #     number_of_songs=1000, from_albums=0.4, from_tracks=0.4, from_playlists=0.2
    # )
    # spotify_playlist_maker.create_random_playlist_for_year(
    #     number_of_songs=100, from_albums=0.5, from_tracks=0.5, year="195"
    # )
    # spotify_playlist_maker.create_playlist_from_tracks_and_albums(
    #     from_tracks=500, from_albums=500
    # )
    # playlist_track_ids:list = spotify_playlist_maker.unique_playlist_tracks.keys()
    # spotify_playlist_maker.create_playlist_with_tracks(playlist_track_ids, "Liked Songs")
    # spotify_playlist_maker.remove_from_all_top_playlist()
    # spotify_playlist_maker.combine_all_top_playlists()
    # spotify_playlist_maker.make_decade_playlists()


def playlist_from_search_terms(
    spotify_playlist_maker, theme, playlist_name=None, tracks=None, terms=None
):
    if playlist_name is None:
        playlist_name = f"{theme.capitalize()}"
    if terms is None:
        with open(f"data/search_term_files/{theme}.txt", "r") as f:
            terms = [line.strip() for line in f if line.strip()]
    if tracks is None:
        tracks = spotify_playlist_maker.saved_tracks

    spotify_playlist_maker.create_playlist_for_search_terms(
        search_terms=terms,
        playlist_name=playlist_name,
        tracks=tracks,
    )


if __name__ == "__main__":
    main()
