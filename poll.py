import pathlib
import os
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
    for data_file in required_data_files:
        full_path = get_data_path() + f'{data_file}'
        p = pathlib.Path(full_path)
        if not p.exists() or os.path.getsize(full_path) == 0:
            # poll.sh doesn't retry the downloads right now and it can fail to fetch the data files
            raise Exception(f'Required data file {data_file} was not found at path: {full_path}.\nIs the data dir configured correctly? CWD: {pathlib.Path.cwd()}')
    
    print('Initiating poll ladder...')
    from app.scripts.poll_character import poll_ladder
    poll_ladder()