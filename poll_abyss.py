"""
This is a script that's only going to get used for 3.29 to record character data until I can double back and process it all

Basically same steps as the normal poll characters script except that we only care about abyss jewels and
instead of doing any processing we record the relevant data to files

Need a character items response and a passive-skills response
Probably make dirs on a per-league and then per-character basis
"""
import pathlib
import os
import logging
from datetime import datetime
from app.app_config import create_config

config = create_config('./config/config.ini')
config.DATABASE_HOST = 'localhost'
logger = logging.getLogger('main')

if pathlib.Path(config.LOCKFILE_NAME).exists():
    logger.error(f'Lock file at {config.LOCKFILE_NAME} exists, bailing out.')
    exit()
else:
    try:
        lockfile = open(config.LOCKFILE_NAME, 'w')
        lockfile.close()
    except Exception as e:
        logger.error(f'Failed to make lock file at {config.LOCKFILE_NAME}')
        logger.error(f'Error: {e}')

start_time = datetime.now()
logger.debug(f'Initiating abyss data retrieval at {start_time}')
try:
    from app.scripts.poll_character import retrieve_abyss_data

    retrieve_abyss_data()
    end_time = datetime.now()

    logger.debug(f'retrieve_abyss_data() finished at {end_time}')
    delta = end_time - start_time
    total_seconds = delta.total_seconds()
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    logger.debug(f'Polling {config.MAX_PROCESSED_CHARACTERS} took {hours}:{minutes}:{seconds}')
except Exception as e:
    logger.error('Error while executing retrieve_abyss_data: ')
    logger.error(f'{e}')
finally:
    try:
        os.remove(config.LOCKFILE_NAME)
        logger.debug('Lockfile removed, have a nice day!')
    except Exception as e:
        logger.error(f'Failed to remove lock at {config.LOCKFILE_NAME}, uh oh!')
        logger.error(f'Error: {e}')