#!/bin/sh
psql -U postgres --password -h localhost < /opt/mindfulness/templates/database.sql
