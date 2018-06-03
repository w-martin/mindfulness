from unittest import TestCase
from sqlalchemy import create_engine

import database


class TestDatabase(TestCase):
    """Tests database functions."""

    test_url = 'http://test_url'
    test_title = 'test_title'
    test_user_name = 'test_user_name'

    def _add_song(self):
        song_id = database.add_song(url=self.test_url, title=self.test_title,
                                    user_name=self.test_user_name)
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
