import ast
import logging
from ConfigParser import ConfigParser
from contextlib import contextmanager

import psycopg2 as psycopg2


def read_database_config():
    parser = ConfigParser()
    parser.read('database/config.ini')
    database_params = {param[0]: param[1] for param in parser.items('postgresql')}
    logging.info("Loaded %d database parameters", len(database_params))
    return database_params


@contextmanager
def connect_to_database():
    # connect
    database_params = read_database_config()
    logging.info('Connecting to the mindful database')
    conn = psycopg2.connect(**database_params)

    cur = conn.cursor()
    yield cur

    # close the connection
    cur.close()
    conn.commit()
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


def get_userid(db, user, add_user=True):
    if len(user) == 0:
        user = "Unknown"
    if add_user:
        db.execute("insert into users (name) select '%s' on conflict do nothing;" % user)
    db.execute("select user_id from users where name='%s';" % user)
    result = db.fetchone()
    user_id = int(result[0])
    return user_id


def add_song(db, url, played, title, user_id):
    db.execute("insert into songs (title,url,user_id,played) select '%s','%s','%d','%s' on conflict do nothing;" %
               (title, url, user_id, "t" if ast.literal_eval(played) else "f"))
    result = '1' == db.statusmessage.split()[-1]
    return result
