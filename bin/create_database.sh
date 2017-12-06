#!/bin/sh
BASE_DIR=$(crudini --get mindfulness_config.ini general path)
psql -U postgres --password -h localhost < $BASE_DIR/templates/database.sql
