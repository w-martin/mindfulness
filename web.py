import os

from flask import Flask, render_template, send_file, url_for, request, redirect
from main import PLAYLIST_PATH, read_playlist_without_newlines

PLAYLIST_NAME = os.path.basename(PLAYLIST_PATH)

app = Flask(__name__)


@app.route("/")
def main():
    return render_template('index.html')


@app.route('/playlist.csv')
def plot_csv():
    """ This downloads the original file as a CSV """
    return send_file(PLAYLIST_PATH,
                     mimetype='text/csv',
                     attachment_filename=PLAYLIST_NAME,
                     as_attachment=True)


@app.route('/playlist')
def print_csv():
    """ This prints out the CSV with a header added """
    header_line = "YouTube Link,Played,Song Name,Added by\n"
    return "%s%s" % (header_line, read_playlist_without_newlines())


@app.route("/add-entry/", methods=["POST"])
def add_entry():
    """ Adds an entry to the CSV database, and refreshes the home page to update """
    username = request.form["name"]
    link = request.form["ytLink"]
    song = request.form["songName"]

    # playlist data
    f_playlist = read_playlist_without_newlines()

    # open read/write, so that we can make sure no new lines are created
    with open(PLAYLIST_PATH, 'w') as f:
        # the new line to be written
        new_line = ",".join([link, str(False), song, username])

        # write out the file with a new line (if it existed, else just the new line)
        if f_playlist:
            f.write("%s\n%s" % (f_playlist, new_line))
        else:
            f.write("%s" % new_line)

    return redirect(url_for('main'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8484)
