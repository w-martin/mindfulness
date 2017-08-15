import os
import vlc
import time
import logging
import ast
import datetime
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

BASE_PATH = '/opt/mindfulness' if os.name != 'nt' else os.getcwd()
PLAYLIST_PATH = '%s/playlist.csv' % BASE_PATH
SONG_PLAY_PATH = "%s/song.mkv" % BASE_PATH


def load_csv(filename):
    songs = dict()
    with open(filename) as f:
        lines = f.readlines()
        for l in lines:
            if not l.startswith('#'):
                parts = l.split(',')
                if 0 == len(parts):
                    continue
                elif 1 == len(parts):
                    played = False
                else:
                    played = ast.literal_eval(parts[1].replace('\n', ''))
                songs[parts[0].replace('\n', '')] = played
    logging.info("Loaded %d songs, of which %d have been played" % (len(songs), sum(songs.values())))
    return songs


def update_list(songname):
    # edit in place instead of re-writing the file to preserve additional information
    with open(PLAYLIST_PATH, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if songname in line:
                line = line.replace(',False,', ',True,')
            f.write('%s' % line)
    with open('%s/mindful.log' % BASE_PATH, 'a') as f:
        f.write("Played %s at %s\n" % (songname, datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")))


def load_playlist():
    return load_csv(PLAYLIST_PATH)


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
    local_song = "%s/song" % BASE_PATH
    os.system("youtube-dl %s -o %s" % (songname, local_song))
    if os.path.exists(SONG_PLAY_PATH):
        os.remove(SONG_PLAY_PATH)
    if os.path.exists("%s/song" % BASE_PATH):
        os.rename("%s/song" % BASE_PATH, SONG_PLAY_PATH)
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
                logging.info("Removed %s/song.mkv" % BASE_PATH)
            update_list(song)
            logging.info("Updated %s/playlist.csv" % BASE_PATH)
        else:
            logging.info("Song did not play")


if __name__ == '__main__':
    main()
