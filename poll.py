import pathlib
import os
import logging
from datetime import datetime
from app.app_config import create_config, get_data_path

required_data_files = ['BrutalRestraint',
                       'GloriousVanity',
                       'LethalPride',
                       'ElegantHubris',
                       'MilitantFaith',
                       # node->index lookup
                       'node_indices.csv',
                       # replacements and additions file
                       'LegionPassives.json',
                       # the passive tree
                       'data.json']

if __name__ == '__main__':
    config = create_config('./config/config.ini')
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

    for data_file in required_data_files:
        full_path = get_data_path() + f'{data_file}'
        p = pathlib.Path(full_path)
        if not p.exists() or os.path.getsize(full_path) == 0:
            # poll.sh doesn't retry the downloads right now and it can fail to fetch the data files
            raise Exception(f'Required data file {data_file} was not found at path: {full_path}.\nIs the data dir configured correctly? CWD: {pathlib.Path.cwd()}')
    
    start_time = datetime.now()
    logger.debug(f'Initiating poll_ladder at {start_time}')
    try:
        from app.scripts.poll_character import poll_ladder
        poll_ladder()
        end_time = datetime.now()

        logger.debug(f'poll_ladder() finished at {end_time}')
        delta = end_time - start_time
        total_seconds = delta.total_seconds()
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.debug(f'Polling {config.MAX_PROCESSED_CHARACTERS} took {hours}:{minutes}:{seconds}')
    except Exception as e:
        logger.error('Error while executing poll_ladder: ')
        logger.error(f'{e}')
    finally:
        try:
            os.remove(config.LOCKFILE_NAME)
            logger.debug('Lockfile removed, have a nice day!')
        except Exception as e:
            logger.error(f'Failed to remove lock at {config.LOCKFILE_NAME}, uh oh!')
            logger.error(f'Error: {e}')