import click
import os
import vlc
import time
import logging
import ast
import datetime
import sys
import shutil
import subprocess

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

BASE_PATH = '/opt/mindfulness' if os.name != 'nt' else os.getcwd()
PLAYLIST_PATH = os.path.join(BASE_PATH, 'playlist.csv')
SONG_PLAY_PATH = os.path.join(BASE_PATH, 'song.mkv')


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
    """ This gets the CSV data, and handles the non-existance of the file """
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


def playlist_line_has_been_played(line):
    try:
        return ast.literal_eval(line.split(',')[1])
    except:
        return False


def update_list(songname):
    def callback(line):
        if songname in line:
            line_elements = line.split(',')
            line_elements[1] = 'True'
            line = ",".join(line_elements)
        return line

    # modify the playlist using the above callback
    modify_playlist_lines(callback)

    # log that its done
    with open('%s/mindful.log' % BASE_PATH, 'a') as f:
        f.write("Played %s at %s\n" % (songname, datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")))


def load_playlist():
    try:
        return load_csv()
    except (IOError, OSError):
        # file could not be found or opened
        return dict()


def play_mindful():
    songname = "%s/mindful.mp3" % BASE_PATH
    logging.info("Playing %s" % songname)
    play_mp3(songname, 66)


def current_time():
    t = int(time.time())
    return t


def play_mp3(songname, timeout=None):
    played = False
    p = vlc.MediaPlayer(songname)
    length = p.get_length()
    if -1 == length and timeout:
        length = timeout
    start_time = current_time()
    logging.info("Playing %s for %d seconds" % (songname, length))
    p.play()
    time.sleep(10)
    while length > (current_time() - start_time):
        time.sleep(5)
        played = True
    logging.info("%d <= %d - stopping" % (length, (current_time() - start_time)))
    if timeout:
        p.stop()
    return played


def select_song(playlist_dict):
    selected = None
    import random
    if False in playlist_dict.values():
        while selected is None:
            song = random.choice(list(playlist_dict.keys()))
            if not playlist_dict[song]:
                selected = song
    return selected


def play_song():
    return play_mp3(SONG_PLAY_PATH, 60 * 10)


def download_song(songname):
    # remove previous song if it exists
    if os.path.exists(SONG_PLAY_PATH):
        os.remove(SONG_PLAY_PATH)

    # temporary path for some versions of youtube-dl
    local_song = os.path.splitext(SONG_PLAY_PATH)[0]

    # download and move to correct play path (for some versions only)
    os.system("youtube-dl %s -o %s" % (songname, local_song))
    if os.path.exists(local_song):
        os.rename(local_song, SONG_PLAY_PATH)
    logging.info("Downloaded %s to %s/song.mkv" % (songname, BASE_PATH))
    return os.path.exists(SONG_PLAY_PATH)


def main():
    playlist_dict = load_playlist()
    song = select_song(playlist_dict)
    success = False
    if song is not None:
        success = download_song(song)
    if not song:
        logging.error("No song. Exiting.")
        sys.exit(1)
    if not success:
        logging.error("Download failed. Exiting.")
        sys.exit(1)
    play_mindful()
    if song is not None:
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


def get_title_from_youtube_url(url):
    return str(subprocess.check_output('youtube-dl --get-title %s' % url)).strip()


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
def mode_select(fix_titles_and_exit):
    if fix_titles_and_exit:
        fix_playlist_song_titles()
    else:
        main()


if __name__ == '__main__':
    mode_select()
