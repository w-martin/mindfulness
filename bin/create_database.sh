#!/bin/sh
psql -U postgres --password -h localhost < ../templates/database.sql
