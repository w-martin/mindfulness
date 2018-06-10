import datetime

import database
import utils


def get_songs(include_played=False, include_out_of_office=False, cycle_users=True, priority_filter=True):
    days = utils.get_user_cycle_days()
    songs = database.load_songs(include_played=include_played, include_out_of_office=include_out_of_office,
                                cycle_users_timedelta=datetime.timedelta(days=days) if cycle_users else None,
                                apply_priority=priority_filter)
    if len(songs) == 0 and not include_played:
        if cycle_users:
            while days > 0 and len(songs) == 0:
                days -= 1
                songs = database.load_songs(include_played=include_played, include_out_of_office=include_out_of_office,
                                            cycle_users_timedelta=datetime.timedelta(days=days),
                                            apply_priority=priority_filter)
        else:
            songs = database.load_songs(include_played=include_played, include_out_of_office=include_out_of_office,
                                        cycle_users_timedelta=None,
                                        cycle_played_timedelta=datetime.timedelta(days=utils.get_played_cycle_days()),
                                        apply_priority=priority_filter)
    return songs
