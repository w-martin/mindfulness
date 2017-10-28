import logging
from ConfigParser import ConfigParser
from contextlib import contextmanager

import click
import psycopg2 as psycopg2

logging.basicConfig(level=logging.INFO)


def config():
    parser = ConfigParser()
    parser.read('database/config.ini')
    database_params = {param[0]: param[1] for param in parser.items('postgresql')}
    logging.info("Loaded %d database parameters", len(database_params))
    return database_params


@contextmanager
def connect_to_database():
    # connect
    params = config()
    logging.info('Connecting to the mindful database')
    conn = psycopg2.connect(**params)

    cur = conn.cursor()
    yield cur

    # close the connection
    cur.close()
    conn.close()
    logging.info('Database connection closed')


def read_playlist(playlist):
    with open(playlist) as f:
        for line in f.readlines():
            yield line.strip().split(',')


def get_songs_size(db):
    db.execute("select count(song_id) from songs;")
    result = db.fetchone()
    return int(result[0])


@click.option('--playlist', '-p', default=None, type=str, help='Playlist file name', required=True)
def main(playlist=None):
    songs = read_playlist(playlist)
    with connect_to_database() as db:
        db_size_before = get_songs_size(db)
        # for url, played, title, user in songs:
        #     user_id = get_userid(db, user)
        #     added = add_song(db, url, played, title, user_id)
        #     logging.info("%s %s by %s", "Added " if added else "Did not add ",
        #                  title, user)
        db_size_after = get_songs_size(db)

    no_songs_added = db_size_after - db_size_before
    logging.info("Populated database with playlist. Added %d songs. Database size: %d -> %d",
                 no_songs_added, db_size_before, db_size_after)


if __name__ == '__main__':
    main()
