# mindfulness
Makes us mindful

To use:
- apt install vlc postgresql
- pip install python-vlc ast youtube-dl
- Ensure youtube-dl is system wide.
- Run bin/get_mindful.sh to get the mindfulness mp3
- Run bin/create_database.sh to create the database
- Adjust the config_mindfulness.ini to your requirements (defaults assume mindfulness is installed in /opt/mindfulness
- Run bin/webserver to run the web interface for populating the database
- Run bin/mindfulness to test the system

To deploy for daily use:
- Add the commands in crontab.txt to crontab (crontab -e)
- Ensure the DISPLAY and XDG_RUNTIME_DIR match the variables for your intend crontab user.
- To incorporate as part of a custom slack app - insert the config_mindfulness.ini field for slack with content https://hooks.slack.com/services/<...>
