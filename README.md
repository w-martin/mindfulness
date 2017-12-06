# mindfulness
Makes us mindful

To use:
- apt install vlc postgresql crudini
- pip install python-vlc ast youtube-dl click flask psycopg2
- Ensure youtube-dl is system wide.
- Adjust the config_mindfulness.ini to your requirements, most importantly the value for `path` (defaults assume this is installed in /opt/mindfulness)
- Ensure locale "en_GB.UTF-8" is installed on linux system (`locale -a` checks installed locales, `sudo locale-gen en_GB.UTF-8` installs it if not)
- Ensure that postgres server is running (`ps -fu postgres` checks, `sudo /etc/init.d/postgresql restart` starts the server if not)
- Run bin/get_mindful.sh to get the mindfulness mp3
- Run bin/create_database.sh to create the database
- Run bin/webserver to run the web interface for populating the database
- Run bin/mindfulness to test the system

To deploy for daily use:
- Add the commands in crontab.txt to crontab (crontab -e)
- Ensure the DISPLAY and XDG_RUNTIME_DIR match the variables for your intend crontab user.
- To incorporate as part of a custom slack app - insert the config_mindfulness.ini field for slack with content https://hooks.slack.com/services/<...>
