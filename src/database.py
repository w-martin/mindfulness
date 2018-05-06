import logging
from collections import namedtuple
from contextlib import contextmanager

import datetime
import psycopg2 as psycopg2

import util


@contextmanager
def connect_to_database():
    # connect
    logging.info('Connecting to the mindful database')
    conn = psycopg2.connect(host=util.read_config('postgresql', 'host'),
                            database=util.read_config('postgresql', 'database'),
                            user=util.read_config('postgresql', 'user'),
                            password=util.read_config('postgresql', 'password'))

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


song_tuple = namedtuple('song', ['song_id', 'title', 'url', 'username', 'played', 'month', 'day'])


class Song(song_tuple):

    def __str__(self):
        return "%s,%s,%s,%s" % (self.url, str(self.played), self.title, self.username)

    def __repr__(self):
        return "('%s' chosen by %s)" % (self.title, self.username)


def filter_priority(songs):
    today = datetime.date.today()
    priority_songs = [s for s in songs if today.weekday() == s.day or today.month == s.month]
    if priority_songs:
        return priority_songs
    else:
        return [s for s in songs if not s.month and not s.day]


def load_songs(include_played=False, include_out_of_office=False, priority=True):
    office_join = "left outer join out_of_office o \n on o.user_id=songs.user_id"
    office_conditional = "and songs.user_id not in (select o.user_id from out_of_office o " \
                         "where now() between o.from and o.to )" if not include_out_of_office else ""

    is_played_case = "case when played.song_id is null then false else true end as is_played"
    is_played_join = "left outer join played \n on played.song_id=songs.song_id"
    is_played_conditional = "and songs.song_id not in (select played.song_id from played)" \
        if not include_played else ""

    with connect_to_database() as db:
        query_str = "select songs.song_id,songs.title,songs.url,users.name,{is_played_case},songs.month,songs.day \n" \
                    "from users,songs \n" \
                    " {is_played_join} \n" \
                    " {office_join} \n" \
                    " where songs.user_id=users.user_id \n" \
                    " {office_conditional} \n" \
                    " {is_played_conditional} \n " \
                    ";".format(is_played_case=is_played_case, is_played_join=is_played_join,
                               office_join=office_join, office_conditional=office_conditional,
                               is_played_conditional=is_played_conditional)
        db.execute(query_str)
        results = db.fetchall()
    songs = [Song(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in results]

    if priority:
        songs = filter_priority(songs)

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


def add_song(db, url, title, user_id, month=None, day=None):
    query = "insert into songs (title,url,user_id,month,day) " \
            "select %(title)s,%(url)s,%(user_id)s,%(month)s,%(day)s on conflict do nothing"
    db.execute(query, {'title': title, 'url': url, 'user_id': user_id, 'month': month, 'day': day})
    result = '1' == db.statusmessage.split()[-1]
    return result


def get_song_id(db, url):
    query_str = "select song_id from songs where url='%s';" % url
    db.execute(query_str)
    result = int(db.fetchone()[0])
    return result


def set_song_played(db, url):
    song_id = get_song_id(db, url)
    query_str = "insert into played (song_id,date) select '%d',now() on conflict do nothing;" % song_id
    db.execute(query_str)
