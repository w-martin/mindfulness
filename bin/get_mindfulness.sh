#!/bin/sh
BASE_DIR=$(crudini --get mindfulness_config.ini general path)
wget -O $BASE_DIR/mindful.mp3 http://mindfulnessatwork.ie/wp-content/uploads/2017/03/1-Minute-Meditation.mp3 
