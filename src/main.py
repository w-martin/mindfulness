import datetime
import glob
import logging
import os
import random
import shlex
import socket
import subprocess
import sys
import time

import click
import re
import vlc

import database
import util

root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

# paths
PLAYLIST_PATH = os.path.join(util.BASE_PATH, util.read_config('general')['playlist'])
SONG_PLAY_PATH = os.path.join(util.BASE_PATH, util.read_config('general')['song'])
MINDFUL_SONG = os.path.join(util.BASE_PATH, util.read_config('general')['mindful_file'])
# urls
SERVER_URL = util.read_config('server')['url']
REPO_URL = "https://github.com/w-martin/mindfulness/issues"
# testing modes
TESTING = util.read_config('testing')['song'] == 'True'
# timeouts
TIMEOUT_MINDFUL = int(util.read_config('timeout')['mindful'])
TIMEOUT_SONG = int(util.read_config('timeout')['song'])


def update_list(song):
    if not TESTING:
        database.mark_song_played(song.song_id)
        # log that its done
        with open('%s/mindful.log' % util.BASE_PATH, 'a') as f:
            f.write("Played %s at %s\n" % (song.title, datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")))


def play_mindful():
    logging.info("Playing %s" % MINDFUL_SONG)
    play_mp3(MINDFUL_SONG, TIMEOUT_MINDFUL)


def current_time():
    t = int(time.time())
    return t


def play_mp3(songname, timeout=None):
    if TESTING:
        return True
    played = False
    p = vlc.MediaPlayer(songname)
    length = p.get_length()
    if -1 == length and timeout:
        length = timeout
    start_time = current_time()
    logging.info("Playing %s for %d seconds" % (songname, length))
    p.play()
    time.sleep(5)
    while length > (current_time() - start_time):
        time.sleep(2)
        played = True
    logging.info("%d <= %d - stopping" % (length, (current_time() - start_time)))
    if timeout:
        p.stop()
    return played


def select_song(songs):
    if len(songs) > 0:
        song = random.choice(songs)
        return song
    else:
        return None


def play_song():
    return play_mp3(get_song_path(), TIMEOUT_SONG)


def download_song(url):
    if TESTING:
        return True

    # remove previous song if it exists
    if os.path.exists(get_song_path()):
        os.remove(get_song_path())

    # download and move to correct play path (for some versions only)
    command = "youtube-dl %s -o %s" % (url, "song.mkv")
    with util.chdir(util.BASE_PATH):
        os.system(command)
    song_path = get_song_path()
    logging.info("Downloaded %s to %s" % (url, song_path))
    return os.path.exists(get_song_path())


def get_song_path():
    potential_song_path = os.path.join(util.BASE_PATH, SONG_PLAY_PATH)
    try:
        return glob.glob(potential_song_path)[0]
    except IndexError:
        # song didn't exist
        return potential_song_path


def get_thumbnail_url(url):
    try:
        youtube_id = re.compile('.*\/(\S+)\??$').match(url).groups(1)[0]
    except AttributeError as ex:
        logging.exception('Failed to parse youtube song identifier')
    else:
        url = 'https://img.youtube.com/vi/{}/0.jpg'.format(youtube_id)
        return url
    return ''


@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('--testing', is_flag=True, help='Test the script without downloading or playing.')
@click.option('--skip-mindful', is_flag=True, help='Test the script without playing mindfulness.', default=False)
@click.option('--skip-slack', is_flag=True, help='Test the script without notifying slack.', default=False)
@click.option('--skip-discord', is_flag=True, help='Test the script without notifying discord.', default=False)
def main(testing=False, skip_mindful=False, skip_slack=False, skip_discord=False):
    if testing:
        global TESTING
        TESTING = testing

    unplayed = database.load_songs(include_played=False, include_out_of_office=False, priority=True)
    song = select_song(unplayed)
    success = False
    attempts = 5
    if song is not None:
        while not success and attempts > 0:
            attempts -= 1
            success = download_song(song.url)
    else:
        logging.error("No song. Exiting.")
        sys.exit(1)

    if not success:
        logging.error("Download failed. Exiting.")
        sys.exit(1)

    if not skip_mindful:
        # play the mindfulness mp3
        play_mindful()

    msg = notification_message(song)
    if not skip_slack:
        slack_notification(msg)
    if not skip_discord:
        thumbnail_url = get_thumbnail_url(song.url)
        discord_notification(msg, thumbnail_url)

    # play
    played = play_song()
    if played:
        logging.info("Song played")
        if os.path.exists(SONG_PLAY_PATH):
            os.remove(SONG_PLAY_PATH)
            logging.info("Removed %s" % SONG_PLAY_PATH)
        update_list(song)
        logging.info("Updated database")
    else:
        logging.info("Song did not play")


def slack_notification(msg):
    try:
        # notify on slack
        slack_url = get_slack_url()
        if "None" != slack_url:
            cmd = r"""curl -X POST -H 'Content-type: application/json' --data '{"text":"%s"}' %s""" % (
                msg, slack_url)
            logging.info(cmd)
            subprocess.call(shlex.split(cmd, posix=True))
    except (OSError, Exception) as ex:
        logging.info("Slack notifier failed: %s" % ex)


def discord_notification(msg, thumbnail_url):
    try:
        # notify on discord
        discord_url = get_discord_url()
        if "None" != discord_url:
            payload = r"""{{ "embeds": [{{"title": "Mindfulness notification", "thumbnail": {{"url": "{thumbnail}"}}, "description": "{content}"}}] }}""".format(content=msg, thumbnail=thumbnail_url)
            cmd = r"""curl -X POST -H "Content-Type: application/json" --data {} {}""".format(payload, discord_url)
            logging.info(cmd)
            subprocess.call(['curl', '-X', 'POST', '-H', '"Content-Type: application/json"', '--data', payload, discord_url])
    except (OSError, Exception) as ex:
        logging.info("Discord notifier failed: %s" % ex)


def notification_message(song):
    chosen_str = " chosen by {username}".format(username=song.username) if song.username != "Unknown" else ""
    server_url = SERVER_URL if SERVER_URL != "None" else "http://{hostname}:{port}".format(
        hostname=socket.gethostname(), port=int(util.read_config('server')['port']))
    msg = "The song of the day is: {song_name}{chosen_str}: {url} \\n" \
          "To add your songs please visit {server_url}, " \
          "or to provide bug reports or feature requests please visit {repo_url}" \
          "\\n{release_notes}".format(song_name=song.title.replace('-', ''), chosen_str=chosen_str, url=song.url,
                                     server_url=server_url, repo_url=REPO_URL, release_notes="")
    return msg


def get_slack_url():
    slack_url = util.read_config('slack')['url']
    return slack_url


def get_discord_url():
    discord_url = util.read_config('discord')['url']
    return discord_url


if __name__ == '__main__':
    main()
