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


def mark_song_played(song_id):
    with connect_to_database() as db:
        db.execute("insert into played (song_id,date) select %d,now();" % song_id)
        logging.info("Marked song with id %d as played" % song_id)


def read_playlist(playlist):
    with open(playlist) as f:
        for line in f.readlines():
            yield line.strip().split(',')


class Song(object):
    def __init__(self, song_id, title, url, username):
        self.song_id = song_id
        self.title = title
        self.url = url
        self.username = username

    def __str__(self):
        return "('%s' chosen by %s)" % (self.title, self.username)

    def __repr__(self):
        return self.__str__()


def load_unplayed():
    with connect_to_database() as db:
        query_str = "select songs.song_id,songs.title,songs.url,users.name " \
                  "from songs,users " \
                  "where songs.user_id=users.user_id " \
                  "and songs.user_id in (select users.user_id from users where users.in_office=True) " \
                  "and songs.song_id not in (select played.song_id from played);"
        db.execute(query_str)
        results = db.fetchall()
    unplayed = [Song(r[0], r[1], r[2], r[3]) for r in results]
    return unplayed


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
