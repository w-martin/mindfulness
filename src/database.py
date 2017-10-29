import ast
import logging
from contextlib import contextmanager

import psycopg2 as psycopg2

from util import read_config


@contextmanager
def connect_to_database():
    # connect
    database_params = read_config('postgresql')
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
    def __init__(self, song_id, title, url, username, played):
        self.song_id = song_id
        self.title = title
        self.url = url
        self.username = username
        self.played = played

    def __str__(self):
        return "%s,%s,%s,%s" % (self.url, str(self.played), self.title, self.username)

    def __repr__(self):
        return "('%s' chosen by %s)" % (self.title, self.username)


def load_songs(include_played=False, include_out_of_office=False):
    office_conditional = "and songs.user_id in (select users.user_id from users where users.in_office=True)" \
        if not include_out_of_office else ""
    played_conditional = "and songs.song_id not in (select played.song_id from played)" \
        if not include_played else ""

    is_played_case = "case when played.song_id is null then false else true end as is_played"
    is_played_join = "left outer join played on played.song_id=songs.song_id"

    with connect_to_database() as db:
        query_str = "select songs.song_id,songs.title,songs.url,users.name,%s " \
                    "from users,songs " \
                    " %s " \
                    " where songs.user_id=users.user_id " \
                    " %s " \
                    " %s ;" % \
                    (is_played_case, is_played_join, office_conditional, played_conditional)
        db.execute(query_str)
        results = db.fetchall()
    songs = [Song(r[0], r[1], r[2], r[3], r[4]) for r in results]
    return songs


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


def get_users():
    with connect_to_database() as db:
        db.execute("select name,in_office from users")
        results = db.fetchall()
    return results


def set_user_in_office(username=None, in_office=True):
    if username is None:
        return
    with connect_to_database() as db:
        db.execute("update users set in_office=%s where name='%s';" % (str(in_office), username))


def add_song(db, url, title, user_id):
    query_str = "insert into songs (title,url,user_id) select '%s','%s','%d' on conflict do nothing;" % (
        title, url, user_id)
    db.execute(query_str)
    result = '1' == db.statusmessage.split()[-1]
    return result
