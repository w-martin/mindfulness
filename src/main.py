import datetime
import glob
import logging
import os
import random
import re
import shlex
import socket
import subprocess
import sys
import time

import click
import vlc
import youtube_dl

import database
import utils

# paths
PLAYLIST_PATH = os.path.join(utils.BASE_PATH, utils.read_config('general', 'playlist'))
SONG_PLAY_PATH = os.path.join(utils.BASE_PATH, utils.read_config('general', 'song', 'song.mkv'))
MINDFUL_SONG = os.path.join(utils.BASE_PATH, utils.read_config('general', 'mindful_file'))
# urls
SERVER_URL = utils.read_config('server', 'url')
REPO_URL = "https://github.com/w-martin/mindfulness/issues"
# testing modes
TESTING = utils.read_config('testing', 'song', type=bool)
# timeouts
TIMEOUT_MINDFUL = utils.read_config('timeout', 'mindful', type=int, default=118)
TIMEOUT_SONG = utils.read_config('timeout', 'song', type=int, default=660)

logger = logging.getLogger(__name__)


def update_list(song):
    if not TESTING:
        database.mark_song_played(song.song_id)
        # log that its done
        with open('%s/mindful.log' % utils.BASE_PATH, 'a') as f:
            f.write("Played %s at %s\n" % (song.title, datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")))


def play_mindful():
    logger.info("Playing %s" % MINDFUL_SONG)
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
    logger.info("Playing %s for %d seconds" % (songname, length))
    p.play()
    time.sleep(5)
    while length > (current_time() - start_time):
        time.sleep(2)
        played = True
    logger.info("%d <= %d - stopping" % (length, (current_time() - start_time)))
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
    with utils.chdir(utils.BASE_PATH):
        logger.info("Downloading {}".format(url))
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.mkv',
            'noplaylist': True
        }
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        ydl.download([url])
    song_path = get_song_path()
    logger.info("Downloaded %s to %s" % (url, song_path))
    return os.path.exists(get_song_path())


def get_song_path():
    potential_song_path = os.path.join(utils.BASE_PATH, SONG_PLAY_PATH)
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

    logger.info('Loading songs')
    unplayed = database.load_songs(include_played=False, include_out_of_office=False)

    logger.info('Selecting song')
    song = select_song(unplayed)
    success = False
    attempts = 5
    if song is not None:
        logger.info('Downloading song')
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
        logger.info('Playing mindful track')
        play_mindful()

    logger.info('Sending notifications')
    msg = notification_message(song)
    if not skip_slack:
        slack_notification(msg)
    if not skip_discord:
        thumbnail_url = get_thumbnail_url(song.url)
        discord_notification(msg, thumbnail_url)

    # play
    logger.info('Playing song at {}'.format(SONG_PLAY_PATH))
    played = play_song()
    if played:
        logger.info("Song played")
        if os.path.exists(SONG_PLAY_PATH):
            os.remove(SONG_PLAY_PATH)
            logger.info("Removed %s" % SONG_PLAY_PATH)
        update_list(song)
        logger.info("Updated database")
    else:
        logger.info("Song did not play")


def slack_notification(msg):
    try:
        # notify on slack
        slack_url = get_slack_url()
        if "None" != slack_url:
            cmd = r"""curl -X POST -H 'Content-type: application/json' --data '{"text":"%s"}' %s""" % (
                msg.replace("'", '"'), slack_url)
            logger.info(cmd)
            subprocess.call(shlex.split(cmd, posix=True))
    except (OSError, Exception) as ex:
        logger.info("Slack notifier failed: %s" % ex)


def discord_notification(msg, thumbnail_url):
    # notify on discord
    discord_url = get_discord_url()
    payload = r"""{{ "embeds": [{{"title": "Mindfulness notification", 
    "thumbnail": {{"url": "{thumbnail}"}}, "description": "{content}"}}] }}""". \
        format(content=msg.replace("'", '"'), thumbnail=thumbnail_url)
    cmd = r"""curl -X POST -H "Content-Type: application/json" --data '{}' {}""".format(payload, discord_url)
    logger.info(cmd)

    if "None" != discord_url:
        for i in range(utils.get_config_parser().getint('discord', 'retries', fallback=2)):
            try:
                subprocess.call(['curl', '-X', 'POST', '-H', '"Content-Type: application/json"',
                                 '--data', payload, discord_url])
            except (OSError, Exception) as ex:
                logger.info("Discord notifier failed: %s" % ex)
            else:
                logger.info("Discord notifier succeeded")
                break


def notification_message(song):
    chosen_str = " chosen by {username}".format(username=song.username) if song.username != "Unknown" else ""
    server_url = SERVER_URL if SERVER_URL != "None" else "http://{hostname}:{port}".format(
        hostname=socket.gethostname(), port=utils.read_config('server', 'port', type=int, default=utils.DEFAULT_PORT))
    msg = "The song of the day is: {song_name}{chosen_str}: {url} \\n" \
          "To add your songs please visit {server_url}, " \
          "or to provide bug reports or feature requests please visit {repo_url}" \
          "\\n{release_notes}".format(song_name=song.title, chosen_str=chosen_str, url=song.url,
                                      server_url=server_url, repo_url=REPO_URL, release_notes="")
    return msg


def get_slack_url():
    slack_url = utils.read_config('slack', 'url')
    return slack_url


def get_discord_url():
    discord_url = utils.read_config('discord', 'url')
    return discord_url


if __name__ == '__main__':
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    main()
