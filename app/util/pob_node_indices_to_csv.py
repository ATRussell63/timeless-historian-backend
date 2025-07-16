import re


def convert_lua_to_csv(lua_filepath: str, passive_tree_filepath: str, output_filepath: str):
    """ Regisle may not publish the updated node_indices file, so we need to make our own from the lua table in PoB. """

    with open(lua_filepath, 'r') as lua_file, open(passive_tree_filepath, 'r') as tree_file, open(output_filepath, 'w') as output_file:
        tree = tree_file.read()
        output_file.write('PassiveSkillGraphId,Name,Datafile Parsing Index\n')
        line = lua_file.readline()
        while line and line != '':
            try:
                match = re.search(r'nodeIDList\[(\d+)\] = \{ index = (\d+), size = \d+ \}', line)
                nodeID = match.group(1)
                index = match.group(2)

                # get passive name
                passive_name = re.search(r'"skill": {},\n.+"name": "(.+)"'.format(nodeID), tree).group(1)

                output_file.write(f'{nodeID},"{passive_name}",{index}\n')
            except Exception as e:
                print({e})

            line = lua_file.readline()


if __name__ == '__main__':
    convert_lua_to_csv('./NodeIndexMapping.lua', './data.json', './node_indices.csv')