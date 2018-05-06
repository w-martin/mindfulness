To run mindfulness, you will need to do the following:

# Install system packages:
- vlc
- anaconda
- youtube-dl
- postgresql

# Install python environment
- conda create -n mindfulness python=3
- source activate mindfulness
- conda install -y --file requirements.txt
- pip install -r requirements-pip.txt

# Set up database
- bin/create_database.sh

# Set up the cron job
- crontab -e 
- enter necessary commands from templates/crontab.txt

# Run web server
- source activate mindfulness
- bin/web_server

