import re
import json
from collections import defaultdict

JEWEL_TYPE_MAP = {
    1: 'Glorious Vanity',
    2: 'Lethal Pride',
    3: 'Brutal Restraint',
    4: 'Militant Faith',
    5: 'Elegant Hubris',
    6: 'Heroic Tragedy'
}


def convert_lua_to_csv(lua_filepath: str, passive_tree_filepath: str, base_mapping_path: str, repl_mapping_path: str):
    """ Regisle may not publish the updated node_indices file, so we need to make our own from the lua table in PoB. 
    
    Update Mirage League:
        PoB publishes a new format where the node index mapping is split across jewel types.
        This means that to find the correct index in LegionPassives, use the jewel type index AND the offset to find
        which addition/replacement is applicable.
        Worth noting that the original node index mapping is still relevant and needs to be parsed too.                 
    """

    with open(lua_filepath, 'r') as lua_file, open(passive_tree_filepath, 'r') as tree_file, open(base_mapping_path, 'w') as base_mapping, open(repl_mapping_path, 'w') as repl_file:
        tree = tree_file.read()
        base_mapping.write('PassiveSkillGraphId,Name,Datafile Parsing Index\n')
        repl_mapping = defaultdict(dict)
        line = lua_file.readline()
        while line and line != '':
            if 'localIdToGlobalId' in line:
                parseReplacementMapping(line, repl_mapping)
            else:
                parseBaseNodeMapping(line, tree, base_mapping)

            line = lua_file.readline()
        
        repl_file.write(json.dumps(repl_mapping))


def parseBaseNodeMapping(line: str, tree, output_file) -> bool:
    try:
        match = re.search(r'nodeIDList\[(\d+)\] = \{ index = (\d+), size = \d+ \}', line)
        nodeID = match.group(1)
        index = match.group(2)

        # get passive name
        passive_name = re.search(r'"skill": {},\n.+"name": "(.+)"'.format(nodeID), tree).group(1)

        output_file.write(f'{nodeID},"{passive_name}",{index}\n')
    except Exception as e:
        print({e})


def parseReplacementMapping(line: str, repl_mapping: dict):
    try:
        match = re.search(r'GlobalId"\]\[(\d+)\]\[(\d+)\] = (\d+)', line)
        jewel_id = int(match.group(1))
        offset = int(match.group(2))
        index = int(match.group(3))

        jewel = JEWEL_TYPE_MAP[jewel_id]

        # if repl_mapping[jewel].get(offset) is None:
        #     repl_mapping[jewel][offset] = ''

        repl_mapping[jewel][offset] = index
    except Exception as e:
        print(e)


LIVE_PATCH = '3.28'
if __name__ == '__main__':
    convert_lua_to_csv(f'data/{LIVE_PATCH}/NodeIndexMapping.lua', f'data/{LIVE_PATCH}/data.json', f'data/{LIVE_PATCH}/node_indices.csv', f'data/{LIVE_PATCH}/mapping_indices.json')