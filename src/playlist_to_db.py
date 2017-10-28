import logging

import click

from src.database import read_playlist, connect_to_database, get_songs_size, get_userid, add_song

PLAYLIST_CSV = 'playlist.csv'

logging.basicConfig(level=logging.INFO)


@click.option('--playlist', '-p', default=PLAYLIST_CSV, type=str, help='Playlist file name', required=True)
def main(playlist=PLAYLIST_CSV):
    songs = read_playlist(playlist)
    with connect_to_database() as db:
        db_size_before = get_songs_size(db)
        for url, played, title, user in songs:
            user_id = get_userid(db, user)
            added = add_song(db, url, played, title, user_id)
            logging.info("%s %s by %s", "Added " if added else "Did not add ",
                         title, user)
        db_size_after = get_songs_size(db)

    no_songs_added = db_size_after - db_size_before
    logging.info("Populated database with playlist. Added %d songs. Database size: %d -> %d",
                 no_songs_added, db_size_before, db_size_after)


if __name__ == '__main__':
    main()
