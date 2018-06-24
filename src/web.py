import datetime
import os

import click
from flask import Flask, render_template, url_for, request, redirect

import database
import playlists
import utils

TEMPLATE_DIR = os.path.join(utils.BASE_PATH, "templates")
STATIC_DIR = os.path.join(utils.BASE_PATH, "static")
INDEX_HTML = 'index.html'
CHRISTMAS_MODE = utils.read_config('modes', 'christmas', type=bool, default=False)
GOOGLE_CLIENT_ID = utils.read_config('google', 'client_id', type=str, default='')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)


@click.command()
@click.option('--christmas', default=False)
@app.route("/")
def main(christmas=CHRISTMAS_MODE):
    return render_template(INDEX_HTML,
                           christmas_mode=christmas,
                           googleClientId=GOOGLE_CLIENT_ID)


@app.route('/playlist')
def print_csv():
    """ This prints out the CSV with a header added """
    # read lines, and make the first a link
    show_played = request.args.get('showPlayed', 'true') == 'true'
    show_out_of_office = request.args.get('showOutOfOffice', 'true') == 'true'
    show_cycle_filter = request.args.get('showCycleFilter', 'true') == 'true'
    show_priority_filter = request.args.get('showPriorityFilter', 'true') == 'true'
    songs = playlists.get_songs(include_played=show_played, include_out_of_office=show_out_of_office,
                                cycle_users=show_cycle_filter, priority_filter=show_priority_filter)
    entries = ['<a href={url}>{url}</a>,{title},{username},{priority}'.format(
        url=s.url, title=s.title, username=s.username, priority=str(s.day is not None or s.month is not None))
               for s in songs]
    header_line = "YouTube Link,Song Name,Added by,Priority day/month"
    return "{}\n{}".format(header_line, '\n'.join(entries))


@app.route('/song_name')
def get_song_name():
    """ This gets the song name from the YouTube address """
    try:
        url = request.args.get('url')
        if url:
            return utils.get_title_from_youtube_url(url)
        else:
            return '<URL was missing>'
    except Exception as ex:
        return str(ex.message)


@app.route("/add-entry/", methods=["POST"])
def add_entry():
    """ Adds an entry to the CSV database, and refreshes the home page to update """
    username = request.form['username']
    email = request.form['email']
    link = utils.remove_commas_from_string(request.form["ytLink"])
    song = utils.remove_commas_from_string(request.form["songName"])

    festive = CHRISTMAS_MODE and "christmasSong" in request.form

    try:
        database.add_song(link, song, username, month=12 if festive else None, email=email)
    except database.KeyExistsError:
        pass

    return redirect(url_for('main'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=utils.read_config('server', 'port', type=int, default=utils.DEFAULT_PORT))
