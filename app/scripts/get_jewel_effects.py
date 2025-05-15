from typing import Dict, List, Tuple
import pathlib
import csv
import numpy as np
import json
import re
import copy
import pandas
from app.scripts.classes import Node

DATA_DIR = 'app/data/'
GV = 'Glorious Vanity'


class NodeLookup():

    JEWEL_TYPES = {
        'Elegant Hubris': {
            'minimum': 2000,
            'maximum': 160000,
            'increment': 20
        },
        'Brutal Restraint': {
            'minimum': 500,
            'maximum': 8000,
            'increment': 1
        },
        'Lethal Pride': {
            'minimum': 10000,
            'maximum': 18000,
            'increment': 1
        },
        'Militant Faith': {
            'minimum': 2000,
            'maximum': 10000,
            'increment': 1
        },
        'Glorious Vanity': {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        },
    }

    GENERAL_TO_KEYSTONE_MAP = {
        'Asenath': 'Dance with Death',
        'Balbala': 'The Traitor',
        'Nasima': 'Second Sight',
        'Cadiro': 'Supreme Decadence',
        'Caspiro': 'Supreme Ostentation',
        'Victario': 'Supreme Grandstanding',
        'Ahuana': 'Immortal Ambition',
        'Doryani': 'Corrupted Soul',
        'Xibaqua': 'Divine Flesh',
        'Akoya': 'Chainbreaker',
        'Kaom': 'Strength of Blood',
        'Rakiata': 'Tempered by War',
        'Avarius': 'Power of Purpose',
        'Dominus': 'Inner Conviction',
        'Maxarius': 'Transcendence'
    }

    BASIC_STAT_NODES = ['Strength', 'Dexterity', 'Intelligence']

    CSV_PATH = DATA_DIR + 'node_indices.csv'
    PASSIVE_LUT_PATH = DATA_DIR + 'passive_lut.json'
    FAST_GV_LOOKUP = DATA_DIR + 'GloriousVanityFAST'

    def __init__(self):
        self._binary_data = {}
        self._node_id_index_csv = None
        self._node_replacements = None
        self._node_replacements_df = None
        self._node_additions = None
        self._node_additions_df = None
        self._devotion = None
        self._price_of_glory = None

    @property
    def node_id_index_map(self):
        if not self._node_id_index_csv:
            self._node_id_index_csv = {}
            with open(self.CSV_PATH, newline='') as index_csv:
                reader = csv.DictReader(index_csv)
                self._node_id_index_csv = {int(row['PassiveSkillGraphId']): int(row['Datafile Parsing Index'])
                                           for row in reader}

        return self._node_id_index_csv

    @property
    def replacements(self):
        if not self._node_replacements:
            self._node_replacements = None
            with open(self.PASSIVE_LUT_PATH, 'r') as p_lut_file:
                self._node_replacements = json.load(p_lut_file)['nodes']

        return self._node_replacements

    @property
    def replacements_df(self):
        if self._node_replacements_df is None:
            self._node_replacements_df = pandas.DataFrame(self.replacements)
        
        return self._node_replacements_df

    def df_find_replacement_by_name(self, name: str):
        return self.replacements_df[self.replacements_df['dn'].isin([name])].to_dict('records')[0]

    @property
    def additions(self):
        if not self._node_additions:
            self._node_additions = None
            with open(self.PASSIVE_LUT_PATH, 'r') as p_lut_file:
                self._node_additions = json.load(p_lut_file)['additions']

        return self._node_additions

    @property
    def additions_df(self):
        if self._node_additions_df is None:
            self._node_additions_df = pandas.DataFrame(self.additions)
        
        return self._node_additions_df

    def df_find_addition_by_id(self, addition_id: str):
        """ Some additions like Devotion have separate listings for notable vs small passive. """
        return self.additions_df[self.additions_df['id'].isin([addition_id])].to_dict('records')[0]

    def jewel_binary_data(self, jewel_type: str):
        if self._binary_data.get(jewel_type) is None:
            jname_trimmed = jewel_type.replace(' ', '')
            with open(DATA_DIR + jname_trimmed, 'rb') as data_file:
                b_file = data_file.read()
                self._binary_data[jewel_type] = np.frombuffer(b_file, dtype=np.uint8)

        return self._binary_data[jewel_type]

    @property
    def devotion_node(self):
        if self._devotion is None:
            self._devotion = self.df_find_replacement_by_name('Devotion')

        return self._devotion

    @property
    def price_node(self):
        if self._price_of_glory is None:
            self._price_of_glory = self.df_find_replacement_by_name('Price of Glory')

        return self._price_of_glory

    def lookup_jewel_keystone(self, general: str) -> dict:
        """ All keystones are transformed into the same node, determined by the general. """

        try:
            # filter the list and return first element
            return [node for node in self.replacements if node['dn'] == self.GENERAL_TO_KEYSTONE_MAP[general]][0]
        except KeyError:
            return None

    def lookup_small_node(self, jewel_type: str, node: Node) -> Tuple[Dict, bool]:
        """ Everything except GV apply static effects to nodes, no *real* lookup required.
            Returns the data associated with 'what happened' as well as a bool flagging if the change was a replacement.
        """

        if jewel_type == 'Elegant Hubris':
            # replaces all small nodes with Price of Glory
            return self.price_node, True
        elif jewel_type == 'Brutal Restraint':
            # applies +4 Dex to non-attribute small passives
            if node.name not in self.BASIC_STAT_NODES:
                return self.df_find_addition_by_id('maraketh_small_dex'), False
            # applies +2 Dex to attribute small passives
            else:
                return self.df_find_addition_by_id('maraketh_attribute_dex'), False
        elif jewel_type == 'Lethal Pride':
            # applies +4 Str to non-attribute small passives
            if node.name not in self.BASIC_STAT_NODES:
                return self.df_find_addition_by_id('karui_small_strength'), False
            # applies +2 Str to attribute small passives
            else:
                return self.df_find_addition_by_id('karui_attribute_strength'), False
        elif jewel_type == 'Militant Faith':
            # applies +5 to Devotion to non-attribute small passives
            if node.name not in self.BASIC_STAT_NODES:
                return self.df_find_addition_by_id('templar_small_devotion'), False
            # replaces attribute small passives with Devotion (+10 node)
            else:
                return self.devotion_node, True
        elif jewel_type == 'Glorious Vanity':
            raise ValueError("Don't use this function for GV")
        else:
            raise ValueError(f'Not a valid jewel type: {jewel_type}')

    def lookup_notable_non_gv(self, jewel_type: str, jewel_seed: int, notable: Node) -> Tuple[Dict, bool]:
        """ Determines what will happen to the given notable based on the jewel details.
            Returns the data from passive_lut.json associated with the change and whether the notable has been replaced.
            If False, the data indicates stats that are added to the notable.
        """

        increment = self.JEWEL_TYPES[jewel_type].get('increment', 1)
        seed_min = int(self.JEWEL_TYPES[jewel_type].get('minimum') / increment)
        seed_max = int(self.JEWEL_TYPES[jewel_type].get('maximum') / increment)
        jewel_seed = int(jewel_seed / increment)

        int_array = self.jewel_binary_data(jewel_type)

        # find the offset
        seed_offset = jewel_seed - seed_min
        seed_size = seed_max - seed_min + 1
        index = int(self.node_id_index_map[notable.node_id])
        dfile_index = index * seed_size + seed_offset

        index_of_change = int_array[dfile_index]
        offset = index_of_change

        if (int(offset) - 94) < 0:
            # additions
            return self.additions[offset], False
        else:
            # replacements
            return self.replacements[offset - 94], True

    def build_fast_gv_lookup_file(self):
        """ The way the data is layed out makes it impossible to jump directly to the data we want.
            The data for each node can either be 2, 3, 6, or 8 bytes normally.
            By padding every node with 0s we can make everything uniform and obviate the header section
            for the purposes of lookups.
        """

        jname_trimmed = GV.replace(' ', '')
        source_filename = DATA_DIR + jname_trimmed
        new_filename = source_filename + 'FAST'

        node_count = len(self.node_id_index_map)
        increment = self.JEWEL_TYPES[GV].get('increment', 1)
        seed_min = int(self.JEWEL_TYPES[GV].get('minimum') / increment)
        seed_max = int(self.JEWEL_TYPES[GV].get('maximum') / increment)
        max_seed_index = seed_max - seed_min + 1
        header_size = node_count * max_seed_index

        with open(source_filename, 'rb') as original, open(new_filename, 'wb') as new_file:

            # first get the header like normal
            header = np.frombuffer(original.read(header_size), np.uint8)
            original.seek(header_size)

            for x in range(header_size):
                data = copy.deepcopy(np.frombuffer(original.read(header[x]), np.uint8))
                padding = [0 for x in range(8 - header[x])]
                data = np.append(data, np.array(padding, np.uint8))
                new_file.write(data)

    def fast_gv_lookup_file_exists(self):
        path = pathlib.Path(self.FAST_GV_LOOKUP)
        return path.exists()

    def fast_lookup_node_gv(self, jewel_seed: int, node: Node):
        increment = self.JEWEL_TYPES[GV].get('increment', 1)
        seed_min = int(self.JEWEL_TYPES[GV].get('minimum') / increment)
        seed_max = int(self.JEWEL_TYPES[GV].get('maximum') / increment)
        max_seed_index = seed_max - seed_min + 1
        node_index = self.node_id_index_map[node.node_id]
        seed_offset = jewel_seed - seed_min

        node_lut_index = (node_index * max_seed_index + seed_offset) * 8

        # TODO - this is super rickety but for now it's good enough
        # probably want to verify that the file is a valid length, etc
        if not self.fast_gv_lookup_file_exists():
            self.build_fast_gv_lookup_file

        with open(self.FAST_GV_LOOKUP, 'rb') as fast_lut:
            fast_lut.seek(node_lut_index)
            data = np.frombuffer(fast_lut.read(8), np.uint8)

        # convert to int, enough tomfuckery
        trimmed_data = [int(x) for x in data]
        # from end of block, find idx of the first padding zero
        last_zero = None
        for i, x in enumerate(reversed(trimmed_data)):
            if x == 0:
                last_zero = -(i + 1)

        if last_zero is not None:
            trimmed_data = trimmed_data[0:last_zero]

        capture_roll_range = r'(\(\d+-\d+\))'

        # replacement with 1 or 2 variable stats
        if len(trimmed_data) == 2 or len(trimmed_data) == 3:
            replacement_node = copy.deepcopy(self.replacements[int(trimmed_data[0]) - 94])
            new_stats = {}
            for x in range(len(trimmed_data) - 1):

                val = str(trimmed_data[x + 1])
                # stat isn't a whole number, need to format it
                if '.' in replacement_node['sd'][x]:
                    # reverse it and slap a decimal point in there
                    val = val[-1] + '.' + val[0]
                
                # sd is not necessarily sorted in the same order that the data is
                # so (29, 1) might be intended for nodes with ranges [(1-1),(25-30)]
                # need to process in order of node['stats'][x]['index']

                # which stat has index x + 1?
                stat_name = None
                stat_order = None
                for k, v in replacement_node['stats'].items():
                    if v['index'] == x + 1:
                        stat_name = k
                        stat_order = v['statOrder']

                # which index in sd is the stat our val is intended for?
                sd_index = replacement_node['sortedStats'].index(stat_name)
                
                modified_stat = re.sub(capture_roll_range,
                                       val,
                                       replacement_node['sd'][sd_index])
                
                # index indicates where it is in the data, but not the display order
                new_stats[stat_order] = modified_stat
            
            # sort by statOrder, then copy into the replacement node
            replacement_node['sd'] = [v for k, v in sorted(new_stats.items())]

            return replacement_node, True

        # 3 or 4 small nodes in a trenchcoat
        elif len(trimmed_data) == 6 or len(trimmed_data) == 8:
            # Legacy of the Vaal and Might of the Vaal are the only outcomes
            # Legacy is defensive nodes, Might is offense
            # we have to look at the icon filename to determine which we're dealing with

            # the additions object does NOT have any indication of which it is (offense/defense)
            # but it has the same 'id' string as the corresponding replacement node
            additions_id_str = self.additions[trimmed_data[0]]['id']
            icon_name = list(filter(lambda n: n['id'] == additions_id_str, self.replacements))[0]['icon']
            is_offense = 'Offensive' in icon_name
            if is_offense:
                name = 'Might of the Vaal'
            else:
                name = 'Legacy of the Vaal'
            
            replacement_node = {
                'dn': name,
                'sd': []
            }

            half_size = int(len(trimmed_data) / 2)
            for x in range(half_size):
                stat_string = re.sub(capture_roll_range,
                                     str(trimmed_data[x + half_size]),
                                     self.additions[trimmed_data[x]]['sd'][0])
                replacement_node['sd'].append(stat_string)
            
            return replacement_node, True

        else:
            raise Exception(f'Invalid data block for node {node.node_id}: {trimmed_data}')