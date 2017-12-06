#!/bin/sh
BASE_DIR=$(crudini --get mindfulness_config.ini general path)
/usr/bin/python $BASE_DIR/src/playlist_to_db.py --playlist $BASE_DIR/playlist.csv
