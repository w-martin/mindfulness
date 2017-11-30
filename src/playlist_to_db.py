import ast
import logging

import click

from database import read_playlist, connect_to_database, get_songs_size, get_userid, add_song, set_song_played

PLAYLIST_CSV = 'playlist.csv'

logging.basicConfig(level=logging.INFO)


@click.option('--playlist', '-p', default=PLAYLIST_CSV, type=str, help='Playlist file name', required=True)
def main(playlist=PLAYLIST_CSV):
    songs = read_playlist(playlist)
    with connect_to_database() as db:
        db_size_before = get_songs_size(db)
        for url, played, title, user in songs:
            played = ast.literal_eval(played)
            assert type(played) is bool
            user_id = get_userid(db, user)
            title = title.replace("'", '')
            added = add_song(db, url, title, user_id)
            logging.info("%s %s by %s", "Added " if added else "Did not add ",
                         title, user)
            if played:
                set_song_played(db, url)
                logging.info("Set song played: %s", title)
        db_size_after = get_songs_size(db)

    no_songs_added = db_size_after - db_size_before
    logging.info("Populated database with playlist. Added %d songs. Database size: %d -> %d",
                 no_songs_added, db_size_before, db_size_after)


if __name__ == '__main__':
    main()
