import ast
import logging
import shutil
import subprocess
import util

PLAYLIST_PATH = util.read_config('general')['playlist']


@DeprecationWarning
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


@DeprecationWarning
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


@DeprecationWarning
def read_playlist_lines():
    return read_playlist_without_newlines().split('\n')


@DeprecationWarning
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


@DeprecationWarning
def playlist_line_has_been_played(line):
    try:
        return ast.literal_eval(line.split(',')[1])
    except:
        return False


def remove_commas_from_string(input_string):
    return str(input_string).translate(None, ',')


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


@DeprecationWarning
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


if __name__ == '__main__':
    fix_playlist_song_titles()
