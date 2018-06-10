import datetime
import logging
from collections import namedtuple
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import BIT
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import utils

logger = logging.getLogger(__name__)
db_engine = None
Base = declarative_base()


class KeyExistsError(Exception):
    pass


def get_db_session():
    global db_engine
    if db_engine is None:
        db_engine = create_engine('postgresql://{username}:{password}@{hostname}/{database}'.format(
            database=utils.read_config('postgresql', 'database'),
            username=utils.read_config('postgresql', 'user'),
            password=utils.read_config('postgresql', 'password'),
            hostname=utils.read_config('postgresql', 'host')
        ))
    return sessionmaker(bind=db_engine)()


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.

    From http://docs.sqlalchemy.org/en/latest/orm/session_basics.html
    """
    session = get_db_session()
    try:
        logger.info('Database connection opened')
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
        logger.info('Database connection closed')


class User(Base):
    """Represents a user from users table."""

    __tablename__ = 'users'

    user_id = Column('user_id', Integer, primary_key=True)
    name = Column('name', String, unique=True)
    admin = Column('admin', Boolean)
    password = Column('password', String)


class Song(Base):
    """Represents a song from songs table."""

    __tablename__ = 'songs'

    song_id = Column('song_id', Integer, primary_key=True)
    title = Column('title', String)
    url = Column('url', String, unique=True)
    day = Column('day', Integer)
    month = Column('month', Integer)
    user_id = Column('user_id', Integer, ForeignKey('users.user_id'))

    user = relationship('User', foreign_keys=[user_id])


class Play(Base):
    """Represents a play from played table."""

    __tablename__ = 'played'

    play_id = Column('play_id', Integer, primary_key=True)
    song_id = Column('song_id', Integer, ForeignKey('songs.song_id'))
    date = Column('date', Date)

    song = relationship('Song', foreign_keys=[song_id])


class OutOfOffice(Base):
    """Represents an out of office entry from out_of_office table."""

    __tablename__ = 'out_of_office'

    ooo_id = Column('ooo_id', Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('users.user_id'))
    to_date = Column('to', Date)
    from_date = Column('from', Date)

    user = relationship('User', foreign_keys=[user_id])


class Vote(Base):
    """Represents a vote from votes table."""

    __tablename__ = 'votes'

    vote_id = Column('vote_id', Integer, primary_key=True)
    song_id = Column('song_id', Integer, ForeignKey('songs.song_id'))
    user_id = Column('user_id', Integer, ForeignKey('users.user_id'))
    vote = Column('vote', BIT)

    user = relationship('User', foreign_keys=[user_id])
    song = relationship('Song', foreign_keys=[song_id])


def mark_song_played(song_id, date=None):
    if date is None:
        date = datetime.date.today()
    with session_scope() as session:
        played = Play(song_id=song_id, date=date)
        try:
            session.add(played)
            session.flush()
            session.commit()
        except IntegrityError:
            raise KeyExistsError()


def read_playlist(playlist):
    with open(playlist) as f:
        for line in f.readlines():
            yield line.strip().split(',')


song_tuple = namedtuple('song', ['song_id', 'title', 'url', 'username', 'month', 'day'])


class SongTuple(song_tuple):

    def __str__(self):
        return "%s,%s,%s" % (self.url, self.title, self.username)

    def __repr__(self):
        return "('%s' chosen by %s)" % (self.title, self.username)


user_tuple = namedtuple('user', ['name', 'admin', 'password'])


class UserTuple(user_tuple):

    def __str__(self):
        return '{}'.format(self.name)

    def __repr__(self):
        return "{}".format(self.name)


def filter_priority(songs):
    today = datetime.date.today()
    priority_songs = [s for s in songs if today.weekday() == s.day or today.month == s.month]
    if priority_songs:
        return priority_songs
    else:
        return [s for s in songs if not s.month and not s.day]


def load_songs(include_played=False, include_out_of_office=False, cycle_users_timedelta=None,
               apply_priority=True, cycle_played_timedelta=None):
    """
    Load songs from the database.

    :param bool include_played: include played songs
    :param bool include_out_of_office: include songs from users who are out of office
    :param datetime.timedelta|None cycle_users_timedelta: time delta to cycle users in
    :param bool apply_priority: filters non priority if priority songs are present
    :param datetime.timedelta|None cycle_played_timedelta: time delta to cycle played songs in
    :return: [SongTuple]
    """
    songs = []
    with session_scope() as session:
        query = session.query(Song)

        # filter out of office
        if not include_out_of_office:
            ooo_subquery = session.query(OutOfOffice.user_id).\
                filter(OutOfOffice.from_date <= datetime.date.today()).\
                filter(OutOfOffice.to_date >= datetime.date.today())
            query = query.filter(Song.user_id.notin_(ooo_subquery))

        if cycle_users_timedelta:
            cut_off_date = (datetime.datetime.now() - cycle_users_timedelta).date()
            play_cycle_subquery = session.query(Song.user_id).join(Play).\
                filter(Play.date > cut_off_date)
            query = query.filter(Song.user_id.notin_(play_cycle_subquery))

        if not include_played:
            if cycle_played_timedelta:
                cut_off_date = (datetime.datetime.now() - cycle_played_timedelta).date()
                play_cycle_subquery = session.query(Song.song_id).join(Play).\
                    filter(Play.date > cut_off_date)
                query = query.filter(Song.song_id.notin_(play_cycle_subquery))
            # filter played
            else:
                play_subquery = session.query(Play.song_id)
                query = query.filter(Song.song_id.notin_(play_subquery))

        song_results = query.all()
        for result in song_results:
            song = SongTuple(song_id=result.song_id,
                             title=result.title,
                             url=result.url,
                             username=result.user.name,
                             month=result.month,
                             day=result.day)
            songs += [song]
    if apply_priority:
        day = datetime.date.today().isoweekday()
        month = datetime.date.today().month
        filtered_songs = [s for s in songs if s.month == month or s.day == day]
        if filtered_songs:
            songs = filtered_songs
    return songs


def add_song(url, title, user_name, month=None, day=None):
    with session_scope() as session:
        user_id = get_userid(user_name, add_user=True)
        song = Song(title=title, url=url, user_id=user_id)
        if month:
            song.month = month
        if day:
            song.day = day
        try:
            session.add(song)
            session.flush()
            session.commit()
        except IntegrityError:
            raise KeyExistsError()
        else:
            song_id = song.song_id
    return song_id


def get_songs_size():
    with session_scope() as session:
        songs = session.query(Song).all()
        no_songs = len(songs)
    return no_songs


def get_userid(username, add_user=True):
    user_id = None
    with session_scope() as session:
        users = session.query(User).filter_by(name=username).all()
        if users:
            user = users[0]
        elif add_user:
            user = User(name=username, admin=False)
            try:
                session.add(user)
                session.flush()
                session.commit()
            except IntegrityError:
                raise KeyExistsError()
        else:
            return None
        user_id = user.user_id
    return user_id


def get_users():
    user_tups = []
    with session_scope() as session:
        users = session.query(User).all()
        for user in users:
            user_tups += [UserTuple(name=user.name, admin=user.admin, password=user.password)]
    return user_tups


def set_song_played(url):
    with session_scope() as session:
        song = session.query(Song).filter_by(url=url).one()
        song_id = song.song_id
        play = Play(song_id=song_id, date=datetime.date.today())
        try:
            session.add(play)
            session.flush()
            session.commit()
        except IntegrityError:
            raise KeyExistsError()


def remove_all_songs():
    with session_scope() as session:
        session.query(Song).delete()
        session.flush()
        session.commit()


def remove_all_played():
    with session_scope() as session:
        session.query(Play).delete()
        session.flush()
        session.commit()


def remove_all_users():
    with session_scope() as session:
        session.query(User).delete()
        session.flush()
        session.commit()
