import datetime
from unittest import TestCase
from sqlalchemy import create_engine

import database


class TestDatabase(TestCase):
    """Tests database functions."""

    test_url = 'http://test_url{id}'
    test_title = 'test_title{id}'
    test_user_name = 'test_user_name'

    def _add_song(self, song_no=0, user_name=None, month=None, day=None):
        if user_name is None:
            user_name = self.test_user_name
        song_id = database.add_song(url=self.test_url.format(id=song_no), title=self.test_title.format(id=song_no),
                                    user_name=user_name, month=month, day=day)
        return song_id

    def setUp(self):
        database.db_engine = create_engine('postgresql://{username}:{password}@{hostname}/{database}'.format(
            database='test_mindfulness',
            username='mindfulness',
            password='mindfulness',
            hostname='localhost'
        ))
        database.remove_all_played()
        database.remove_all_songs()
        database.remove_all_users()

    def tearDown(self):
        database.remove_all_played()
        database.remove_all_songs()
        database.remove_all_users()

    def test_add_song(self):
        """Tests the add song function."""
        song_id = self._add_song()
        self.assertIsNotNone(song_id)

    def test_load_songs(self):
        songs = database.load_songs(include_played=True)
        self.assertEqual(len(songs), 0)

        songs = database.load_songs(include_played=False)
        self.assertEqual(len(songs), 0)

        song_id = self._add_song()

        songs = database.load_songs(include_played=True)
        self.assertEqual(len(songs), 1)

        songs = database.load_songs(include_played=False)
        self.assertEqual(len(songs), 1)

        database.mark_song_played(song_id)

        songs = database.load_songs(include_played=True)
        self.assertEqual(len(songs), 1)

        songs = database.load_songs(include_played=False)
        self.assertEqual(len(songs), 0)

    def test_cycle_users(self):
        song_id_0 = self._add_song(song_no=0, user_name='user0')
        _ = self._add_song(song_no=1, user_name='user0')
        song_id_2 = self._add_song(song_no=2, user_name='user1')
        database.mark_song_played(song_id_0)

        songs = database.load_songs(include_played=True, cycle_users_timedelta=None)
        self.assertEqual(len(songs), 3)

        songs = database.load_songs(include_played=False, cycle_users_timedelta=datetime.timedelta(weeks=1))
        self.assertEqual(len(songs), 1)
        songs = database.load_songs(include_played=True, cycle_users_timedelta=datetime.timedelta(weeks=1))
        self.assertEqual(len(songs), 1)
        self.assertEqual(song_id_2, songs[0].song_id)

        songs = database.load_songs(include_played=False, cycle_users_timedelta=datetime.timedelta(microseconds=1))
        self.assertEqual(len(songs), 2)

        songs = database.load_songs(include_played=False, cycle_users_timedelta=None)
        self.assertEqual(len(songs), 2)

    def test_apply_priority(self):
        _ = self._add_song(song_no=0, user_name='user0')
        today = datetime.date.today().isoweekday()
        song_id_1 = self._add_song(song_no=1, user_name='user1', day=today)
        songs = database.load_songs(include_played=True, cycle_users_timedelta=None, apply_priority=True)
        self.assertEqual(len(songs), 1)
        self.assertEqual(today, songs[0].day)
        self.assertEqual(song_id_1, songs[0].song_id)
        songs = database.load_songs(include_played=True, cycle_users_timedelta=None, apply_priority=False)
        self.assertEqual(len(songs), 2)

    def test_apply_priority_played(self):
        today = datetime.date.today().isoweekday()
        song_id_0 = self._add_song(song_no=0, user_name='user0')
        song_id_1 = self._add_song(song_no=1, user_name='user0', day=today)
        _ = self._add_song(song_no=2, user_name='user0')
        song_id_3 = self._add_song(song_no=3, user_name='user0', day=today)
        database.mark_song_played(song_id_0)
        database.mark_song_played(song_id_1)

        songs = database.load_songs(include_played=False, include_out_of_office=False, apply_priority=False)
        self.assertEqual(len(songs), 2)
        songs = database.load_songs(include_played=True, include_out_of_office=False, apply_priority=False)
        self.assertEqual(len(songs), 4)

        songs = database.load_songs(include_played=False, include_out_of_office=False, apply_priority=True)
        self.assertEqual(len(songs), 1)
        self.assertEqual(song_id_3, songs[0].song_id)
        songs = database.load_songs(include_played=True, include_out_of_office=False, apply_priority=True)
        self.assertEqual(len(songs), 2)

    def test_cycle_played(self):
        song_id_0 = self._add_song(song_no=0, user_name='user0')
        song_id_1 = self._add_song(song_no=1, user_name='user0')
        database.mark_song_played(song_id_0, date=(datetime.datetime.now() - datetime.timedelta(days=1)).date())

        songs = database.load_songs(include_played=False, cycle_users_timedelta=None,
                                    cycle_played_timedelta=None)
        self.assertEqual(len(songs), 1)

        songs = database.load_songs(include_played=False, cycle_users_timedelta=None,
                                    cycle_played_timedelta=datetime.timedelta(microseconds=1))
        self.assertEqual(len(songs), 2)
        songs = database.load_songs(include_played=False, cycle_users_timedelta=None,
                                    cycle_played_timedelta=datetime.timedelta(weeks=1))
        self.assertEqual(len(songs), 1)
        self.assertEqual(song_id_1, songs[0].song_id)
