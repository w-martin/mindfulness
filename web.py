from flask import Flask, render_template, send_file, url_for, request, redirect

app = Flask(__name__)


@app.route("/")
def main():
    return render_template('index.html')


@app.route('/playlist.csv')
def plot_csv():
    """ This downloads the original file as a CSV """
    return send_file('playlist.csv',
                     mimetype='text/csv',
                     attachment_filename='playlist.csv',
                     as_attachment=True)


@app.route('/playlist')
def print_csv():
    """ This prints out the CSV with a header added """
    with open('playlist.csv', 'r') as f:
        return "YouTube Link,Played,Song Name,Added by\n%s" % f.read()


@app.route("/add-entry/", methods=["POST"])
def add_entry():
    """ Adds an entry to the CSV database, and refreshes the home page to update """
    username = request.form["name"]
    link = request.form["ytLink"]
    song = request.form["songName"]

    with open('playlist.csv', 'a') as f:
        f.write("\n%s" % ",".join([link, str(False), song, username]))

    return redirect(url_for('main'))


if __name__ == "__main__":
    app.run()
