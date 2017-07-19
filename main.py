import os
import vlc
import time
import calendar


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
                    played = bool(parts[1].replace('\n', ''))
                songs[parts[0].replace('\n', '')] = played
    return songs


def update_list(songname, playlist_dict):
    with open('playlist.csv', 'w') as f:
        for song in playlist_dict:
            if song == songname:
                played = True
            else:
                played = playlist_dict[song]
            f.write("%s,%s\n" % (song, str(played)))
    with open('mindful.log', 'a') as f:
        f.write("Played %s\n" % songname)


def load_playlist():
    return load_csv('playlist.csv')


def play_mindful():
    songname = "mindful.mp3"
    print("Playing %s" % songname)
    play_mp3(songname)


def play_mp3(songname):
    played = False
    p = vlc.MediaPlayer(songname)
    length = p.get_length()
    start_time = calendar.timegm(time.gmtime())
    print("Playing %s" % songname)
    p.play()
    time.sleep(10)
    while p.is_playing():
        time.sleep(2)
        played = True
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


def play_song(songname):
    songname = "song.mkv"
    return play_mp3(songname)


def download_song(songname):
    local_song = "song"
    os.system("youtube-dl %s -o %s" % (songname, local_song))


def main():
    playlist_dict = load_playlist()
    song = select_song(playlist_dict)
    if song is not None:
        download_song(song)
    # play_mindful()
    if song is not None:
        played = True  # play_song(song)
        if played:
            os.remove("song.mkv")
            update_list(song, playlist_dict)


if __name__ == '__main__':
    main()
