#!/bin/sh
psql -U postgres --password -h localhost < /opt/mindfulness/templates/test_database.sql
