import ast
import datetime
import logging
import os
import random
import shlex
import shutil
import subprocess
import sys
import time

import click
import vlc

from database import mark_song_played, load_unplayed


root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

BASE_PATH = '/opt/mindfulness' if os.name != 'nt' else os.getcwd()
PLAYLIST_PATH = os.path.join(BASE_PATH, 'playlist.csv')
SONG_PLAY_PATH = os.path.join(BASE_PATH, 'song.webm')
TESTING = False
SKIP_MINDFUL = False
TIMEOUT_MINDFUL = 66
TIMEOUT_SONG = 10


def load_csv():
    songs = dict()
    for l in read_playlist_lines():
        if not l.startswith('#'):
            parts = l.split(',')
            if 0 == len(parts):
                continue
            elif 1 == len(parts):
                played = False
            else:
                played = ast.literal_eval(parts[1].strip())
            songs[parts[0].replace('\n', '')] = played
    logging.info("Loaded %d songs, of which %d have been played" % (len(songs), sum(songs.values())))
    return songs


def read_playlist_without_newlines():
    """ This gets the CSV data, and handles the non-existence of the file """
    try:
        # open read/write, so that we can make sure no new lines are created
        with open(PLAYLIST_PATH, 'r') as f:
            # read the file -- make a list of lines with no empty ones (and line separators removed)
            f_data = "\n".join([x.strip() for x in f.readlines() if x.strip()])
    except (IOError, OSError):
        f_data = ''
    return f_data


def read_playlist_lines():
    return read_playlist_without_newlines().split('\n')


def modify_playlist_lines(callback):
    # edit in place instead of re-writing the file to preserve additional information
    lines = read_playlist_lines()

    # re-open the file otherwise the length of the file is different (len(False) vs. len(True))
    with open(PLAYLIST_PATH, 'w') as f:
        for line in lines:
            try:
                line = callback(line)
            except Exception as ex:
                logging.exception('Problem running callback on line: %s\n%s' % (line, ex))

            # make sure there is a new line
            line = "%s\n" % line.strip()

            # write the line
            f.write(line)


def remove_commas_from_string(input_string):
    return str(input_string).translate(None, ',')


def playlist_line_has_been_played(line):
    try:
        return ast.literal_eval(line.split(',')[1])
    except:
        return False


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
    selected = None
    song = random.choice(songs)
    return song


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


def main():
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


def get_title_from_youtube_url(url):
    try:
        output = str(subprocess.check_output('youtube-dl --get-title %s --no-warnings' % url, stderr=subprocess.STDOUT,
                                             shell=True)).strip()
    except subprocess.CalledProcessError as ex:
        output = str(ex.output).strip()
    except OSError as ex:
        output = 'youtube-dl not found: %s' % ex
    except Exception as ex:
        output = 'Something bad happened: %s' % ex
    return remove_commas_from_string(output)


def fix_playlist_song_titles():
    def callback(line):
        ls = ('%s,,,,' % line).split(',')  # making sure it has enough elements!
        if not str(ls[2]).strip():
            # no song title -- find it automatically
            ls[2] = get_title_from_youtube_url(ls[0])
            line = ",".join(ls[:4])
            logging.info('Added %s for line %s' % (ls[2], line))
        return line

    logging.info('Backing up playlist to playlist.csv.bak')
    shutil.copy(PLAYLIST_PATH, PLAYLIST_PATH + '.bak')

    logging.info('Fixing the missing song titles in the CSV file')
    modify_playlist_lines(callback)


@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('--fix-titles-and-exit', '-f', is_flag=True, help='Fix the song names and exit.')
@click.option('--testing', '-t', is_flag=True, help='Test the script without downloading or playing.')
@click.option('--skip-mindful', '-s', is_flag=True, help='Test the script without playing mindfulnes.')
def mode_select(fix_titles_and_exit, testing=False, skip_mindful=False):
    global TESTING
    if testing:
        TESTING = testing

    global SKIP_MINDFUL
    if skip_mindful:
        SKIP_MINDFUL = skip_mindful

    # switch based on input options
    if fix_titles_and_exit:
        fix_playlist_song_titles()
    else:
        main()


if __name__ == '__main__':
    mode_select()
