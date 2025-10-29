import logging

from spotify.spotify_playlist_maker import SpotifyPlaylistMaker
from spotify.spotify_utils import setup_app_logging

logger = logging.getLogger(__name__)


def main():
    setup_app_logging(logger, logging.DEBUG)

    spotify_playlist_maker: SpotifyPlaylistMaker = SpotifyPlaylistMaker(
        use_zip=True
    )
    make_playlists(spotify_playlist_maker)


def make_playlists(spotify_playlist_maker):
    # spotify_playlist_maker.create_playlist_from_liked_albums()
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
    #get list from colours.txt

    with open("data/search_term_files/colours.txt", "r") as f:
        colours = [line.strip() for line in f if line.strip()]

    # colours = ["Red", "blue", "green"]
    spotify_playlist_maker.create_playlist_for_search_terms(colours, "colours", spotify_playlist_maker.saved_tracks)

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
    # spotify_playlist_maker.create_playlist_from_liked_albums()
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


if __name__ == "__main__":
    main()
