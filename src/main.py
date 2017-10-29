import datetime
import logging
import os
import random
import shlex
import subprocess
import sys
import time

import click
import vlc

from database import mark_song_played, load_unplayed
import util

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

BASE_PATH = util.read_config('general')['path']
PLAYLIST_PATH = os.path.join(BASE_PATH, util.read_config('general')['playlist'])
SONG_PLAY_PATH = os.path.join(BASE_PATH, util.read_config('general')['song'])
TESTING = util.read_config('testing')['song'] == 'True'
SKIP_MINDFUL = util.read_config('testing')['mindfulness'] == 'True'
TIMEOUT_MINDFUL = int(util.read_config('timeout')['mindful'])
TIMEOUT_SONG = int(util.read_config('timeout')['song'])


def update_list(song):
    mark_song_played(song.song_id)
    # log that its done
    with open('%s/mindful.log' % BASE_PATH, 'a') as f:
        f.write("Played %s at %s\n" % (song.title, datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")))


def play_mindful():
    if SKIP_MINDFUL:
        return
    songname = "%s/mindful.mp3" % BASE_PATH
    logging.info("Playing %s" % songname)
    play_mp3(songname, TIMEOUT_MINDFUL)


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
    return play_mp3(SONG_PLAY_PATH, TIMEOUT_SONG)


def download_song(url):
    if TESTING:
        return True

    # remove previous song if it exists
    if os.path.exists(SONG_PLAY_PATH):
        os.remove(SONG_PLAY_PATH)

    # temporary path for some versions of youtube-dl
    local_song = os.path.splitext(SONG_PLAY_PATH)[0]

    # download and move to correct play path (for some versions only)
    os.system("youtube-dl %s -o %s" % (url, local_song))
    if os.path.exists(local_song):
        os.rename(local_song, SONG_PLAY_PATH)
    logging.info("Downloaded %s to %s/song.mkv" % (url, BASE_PATH))
    return os.path.exists(SONG_PLAY_PATH)


@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('--testing', '-t', is_flag=True, help='Test the script without downloading or playing.')
@click.option('--skip-mindful', '-s', is_flag=True, help='Test the script without playing mindfulnes.')
def main(testing=False, skip_mindful=False):
    global TESTING
    if testing:
        TESTING = testing

    global SKIP_MINDFUL
    if skip_mindful:
        SKIP_MINDFUL = skip_mindful

    unplayed = load_unplayed()
    song = select_song(unplayed)
    success = False
    if song is not None:
        success = download_song(song.url)
    if not song:
        logging.error("No song. Exiting.")
        sys.exit(1)
    if not success:
        logging.error("Download failed. Exiting.")
        sys.exit(1)

    # play the mindfulness mp3
    play_mindful()

    # if we've got a song -- play it
    if song is not None:
        # notify on slack
        try:
            slack_url = get_slack_url()
            msg = "The song of the day is: '%s' chosen by %s" % (song.title, song.username)
            cmd = r"""curl -X POST -H 'Content-type: application/json' --data '{"text":"%s"}' %s""" % (msg, slack_url)
            subprocess.call(shlex.split(cmd, posix=True))
        except (OSError, Exception) as ex:
            logging.info("Slack notifier failed: %s" % ex)

        # play
        played = play_song()
        if played:
            logging.info("Song played")
            if os.path.exists(SONG_PLAY_PATH):
                os.remove(SONG_PLAY_PATH)
                logging.info("Removed %s" % SONG_PLAY_PATH)
            update_list(song)
            logging.info("Updated %s" % PLAYLIST_PATH)
        else:
            logging.info("Song did not play")


def get_slack_url():
    with open('%s/slack.url' % BASE_PATH, 'r') as f:
        slack_url = f.read().strip()
    return slack_url


if __name__ == '__main__':
    main()
