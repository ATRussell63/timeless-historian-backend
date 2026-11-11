from enum import StrEnum
from typing import Dict, Tuple, List
import pathlib
import csv
import numpy as np
import json
import re
import copy
import pandas
from app.scripts.classes import Node, DrawingRoot
from app.app_config import get_data_path
from app.scripts.parse_data_files.classes import NodeTooltip, Stat
from app.scripts.parse_data_files.jewel_stats import JewelStats
from app.scripts.parse_data_files.nodes import Tag
from app.util.parse_jewel import ParsedJewel


class JewelType(StrEnum):
    LP = 'Lethal Pride'
    BR = 'Brutal Restraint'
    EH = 'Elegant Hubris'
    MF = 'Militant Faith'
    GV = 'Glorious Vanity'
    HT = 'Heroic Tragedy'
    FV = 'Festering Vengeance'
    EG = 'Extinguishing Grasp'
    BD = 'Baleful Dominion'
    DA = 'Destructive Aspiration'
    RM = 'Reclaimed Malevolence'

TIMELESS = [JewelType.LP, JewelType.BR, JewelType.EH, JewelType.MF, JewelType.GV, JewelType.HT]
DOMAIN = [JewelType.FV, JewelType.EG, JewelType.BD, JewelType.DA]

MAGIC_NUMBER = 337


class NodeLookup:

    JEWEL_TYPES = {
        JewelType.EH: {
            'minimum': 2000,
            'maximum': 160000,
            'increment': 20
        },
        JewelType.BR: {
            'minimum': 500,
            'maximum': 8000,
            'increment': 1
        },
        JewelType.LP: {
            'minimum': 10000,
            'maximum': 18000,
            'increment': 1
        },
        JewelType.MF: {
            'minimum': 2000,
            'maximum': 10000,
            'increment': 1
        },
        JewelType.GV: {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        },
        JewelType.HT: {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        },
        JewelType.FV: {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        },
        JewelType.EG: {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        },
        JewelType.BD: {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        },
        JewelType.DA: {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        },
        JewelType.RM: {
            'minimum': 100,
            'maximum': 8000,
            'increment': 1
        }
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
        'Maxarius': 'Transcendence',
        'Vorana': 'Black Scythe Training',
        'Uhtred': 'Celestial Mathematics',
        'Medved': 'The Unbreaking Circle',
        'Tecrod': 'Festering Vengeance',
        'Ulaman': 'Weighted Exchange',
        'Kurgal': 'Reconstructed Essence',
        'Amanamu': 'The Loyal Few'
    }

    INFLUENCE_LINE_MAP = {
        JewelType.GV: ('Bathed in the blood of {} sacrificed in the name of {}', 'Vaal'),
        JewelType.EH: ('Commissioned {} coins to commemorate {}', 'Eternal Empire'),
        JewelType.MF: ('Carved to glorify {} new faithful converted by High Templar {}', 'Templars'),
        JewelType.LP: ('Commanded leadership over {} warriors under {}', 'Karui'),
        JewelType.BR: ('Denoted service of {} dekhara in the akhara of {}', 'Maraketh'),
        JewelType.HT: ('Remembrancing {} songworthy deeds by the line of {}', 'Kalguur'),
        JewelType.FV: ("Subjugating {} souls in the thrall of {}", "Abyssal"),
        JewelType.EG: ("Subjugating {} souls in the thrall of {}", "Abyssal"),
        JewelType.BD: ("Subjugating {} souls in the thrall of {}", "Abyssal"),
        JewelType.DA: ("Subjugating {} souls in the thrall of {}", "Abyssal"),
        JewelType.RM: ("Binding {} souls to phylacteries to sustain {}", "Abyssal")
    }

    BASIC_STAT_NODES = ['Strength', 'Dexterity', 'Intelligence']
    
    def __init__(self, jewel: ParsedJewel):
        self.DATA_DIR = get_data_path()
        self.CSV_PATH = self.DATA_DIR + 'node_indices.csv'
        self.ADD_REPLACE_PATH = self.DATA_DIR + 'mapping_indices.json'
        self.PASSIVE_LUT_PATH = self.DATA_DIR + 'LegionPassives.json'
        self.FAST_GV_LOOKUP = self.DATA_DIR + 'GloriousVanityFAST'
        self._jewel_type = JewelType(jewel.jewel_type)
        self._seed = int(jewel.seed)
        self._general = jewel.general
        self._mf_mods = jewel.mf_mods
        self._add_replace_map = None
        self._binary_data = None
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
    def add_replace_map(self):
        if not self._add_replace_map:
            with open(self.ADD_REPLACE_PATH, 'r') as map_json:
                self._add_replace_map = json.loads(map_json.read())
        
        return self._add_replace_map

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

    @property
    def jewel_binary_data(self):
        if self._binary_data is None:
            trimmed_jewel_name = self._jewel_type.value.replace(' ', '')

            with open(self.DATA_DIR + trimmed_jewel_name, 'rb') as data_file:
                b_file = data_file.read()
                self._binary_data = np.frombuffer(b_file, dtype=np.uint8)

        return self._binary_data

    def _gv_fast_lookup(self, node_lut_index: int):
        if not pathlib.Path(self.FAST_GV_LOOKUP).exists():
            self._build_fast_gv_lookup_file()

        with open(self.FAST_GV_LOOKUP, 'rb') as fast_lut:
            fast_lut.seek(node_lut_index)
            return np.frombuffer(fast_lut.read(8), np.uint8)

    def apply_effects_for_node(self, node_id: int, drawing: DrawingRoot):
        node = drawing.nodes[node_id]

        if Tag.JEWEL_SOCKET in node.tags:
            self._apply_jewel_socket_toolip(node)
        elif Tag.SMALL in node.tags:
            self._apply_small_node_effects(node, drawing.jewel_stats)
        elif Tag.NOTABLE in node.tags:
            self._apply_notable_effects(node, drawing.jewel_stats)
        elif Tag.KEYSTONE in node.tags:
            self._apply_keystone_effects(node, drawing.jewel_stats)

    def _apply_jewel_socket_toolip(self, node: Node):
        main_string, faction = self.INFLUENCE_LINE_MAP[self._jewel_type]
        main_string = main_string.format(self._seed, self._general)
        conquered_str = f'Passives in radius are Conquered by the {faction}'

        body = [main_string, conquered_str]
        if self._mf_mods:
            body += self._mf_mods
        body += ['Historic']

        node.tooltip = NodeTooltip(title=self._jewel_type.value, body=body, replaced_title=None, reminder_text=None)

    def _apply_keystone_effects(self, node: Node, jewel_stats: JewelStats):
        """ All keystones are transformed into the same node, determined by the general. """

        try:
            # filter the list and return first element
            json_passive = [node for node in self.replacements if node['dn'] == self.GENERAL_TO_KEYSTONE_MAP[self._general]][0]
            node.tooltip = NodeTooltip(title=json_passive['dn'],
                                       body=json_passive['sd'],
                                       replaced_title=node.name)
            jewel_stats.add_stat(json_passive, None)
        except KeyError:
            return None

    def _apply_small_node_effects(self, node: Node, jewel_stats: JewelStats):
        """ Everything except GV apply static effects to nodes, no *real* lookup required.
            Returns the data associated with 'what happened' as well as a bool flagging if the change was a replacement.
        """

        def basic_attr_addition(addition_id: str):
            addition = self.df_find_addition_by_id(addition_id)
            added_stats = jewel_stats.add_stat(addition, addition['stats'].values()[0]['min'])
            node.make_tooltip_from_addition(added_stats)

        match self._jewel_type:
            case JewelType.EH:
                # replaces all small nodes with Price of Glory, no need to update jewel stats
                node.tooltip = NodeTooltip(title='Price of Glory', body=[], replaced_title=node.name)

            case JewelType.BR:
                # adds +4 Dex to non-attr nodes, adds +2 to basic attr nodes
                effect_id = 'maraketh_small_dex' if node.name not in self.BASIC_STAT_NODES else 'maraketh_attribute_dex'
                basic_attr_addition(effect_id)

            case JewelType.LP:
                # adds +4 Str to non-attr nodes, adds +2 to basic attr nodes
                effect_id = 'karui_small_strength' if node.name not in self.BASIC_STAT_NODES else 'karui_attribute_strength'
                basic_attr_addition(effect_id)

            case JewelType.MF:
                # applies +5 to Devotion to non-attr nodes, replaces other smalls with +10 Devotion
                if node.name not in self.BASIC_STAT_NODES:
                    basic_attr_addition('templar_small_devotion')
                else:
                    effect_name = 'Devotion'
                    json_passive = self.df_find_replacement_by_name(effect_name)
                    stats = jewel_stats.add_stat(json_passive)
                    node.make_tooltip_from_replacement(new_name=effect_name, stats=stats)

            case JewelType.GV:
                self._apply_node_effects_gv(node, jewel_stats)

            case JewelType.HT:
                # applies 2% increased ward to non-attribute small passives
                effect_id = 'kalguuran_small_ward' if node.name not in self.BASIC_STAT_NODES else 'kalguuran_attribute_ward'
                basic_attr_addition(effect_id)

    def _apply_notable_effects(self, node: Node, jewel_stats: JewelStats):

        match self._jewel_type:
            case JewelType.EH | JewelType.BR | JewelType.LP | JewelType.HT | JewelType.MF:
                self._apply_notable_effects_non_gv(node, jewel_stats)

            case JewelType.GV:
                self._apply_node_effects_gv(node, jewel_stats)

    def _apply_notable_effects_non_gv(self, node: Node, jewel_stats: JewelStats):
        json_passive, replaced = self._lookup_notable_non_gv(node)
        stats = jewel_stats.add_stat(json_passive)
        if replaced:
            node.make_tooltip_from_replacement(json_passive['dn'], stats)
        else:
            node.make_tooltip_from_addition(stats)

    def _lookup_notable_non_gv(self, notable: Node) -> Tuple[Dict, bool]:
        """ Determines what will happen to the given notable based on the jewel details.
            Returns the data from LegionPassives.json associated with the change and whether the notable has been replaced.
            If False, the data indicates stats that are added to the notable.
        """

        increment = self.JEWEL_TYPES[self._jewel_type].get('increment', 1)
        seed_min = int(self.JEWEL_TYPES[self._jewel_type].get('minimum') / increment)
        seed_max = int(self.JEWEL_TYPES[self._jewel_type].get('maximum') / increment)
        jewel_seed = int(self._seed / increment)

        # find the offset
        seed_offset = jewel_seed - seed_min
        seed_size = seed_max - seed_min + 1
        index = int(self.node_id_index_map[notable.node_id])
        dfile_index = index * seed_size + seed_offset

        index = self._get_add_replace_index(self.jewel_binary_data[dfile_index])

        if (int(index) - MAGIC_NUMBER) < 0:
            # additions
            effect = self.additions[index]
            replacement = False
        else:
            # replacements
            effect = self.replacements[index - MAGIC_NUMBER]
            replacement = True

        return effect, replacement

    def _get_add_replace_index(self, offset: int) -> int:
        """ *Mirage League* The mapping is a little different now. Rather than directly indexing 
            the additions and replacements map, there's a new per-jewel mapping to those node effect indices.
            
            Unfortunately I can't save the json to a file without converting the offset keys to a string,
            so this helper method helps un-spaghettify my random casts everywhere.
        """

        return self.add_replace_map[self._jewel_type][str(offset)]

    def _build_fast_gv_lookup_file(self):
        """ The way the data is laid out makes it impossible to jump directly to the data we want.
            The data for each node can either be 2, 3, 6, or 8 bytes normally.
            By padding every node with 0s we can make everything uniform and obviate the header section
            for the purposes of lookups.
        """

        jname_trimmed = JewelType.GV.value.replace(' ', '')
        source_filename = self.DATA_DIR + jname_trimmed
        new_filename = source_filename + 'FAST'

        node_count = len(self.node_id_index_map)
        increment = self.JEWEL_TYPES[JewelType.GV].get('increment', 1)
        seed_min = int(self.JEWEL_TYPES[JewelType.GV].get('minimum') / increment)
        seed_max = int(self.JEWEL_TYPES[JewelType.GV].get('maximum') / increment)
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

    def _fast_lookup_node_gv(self, jewel_seed: int, node: Node) -> Tuple[str, List[Tuple[dict, List[float | int]]]]:
        increment = self.JEWEL_TYPES[JewelType.GV].get('increment', 1)
        seed_min = int(self.JEWEL_TYPES[JewelType.GV].get('minimum') / increment)
        seed_max = int(self.JEWEL_TYPES[JewelType.GV].get('maximum') / increment)
        max_seed_index = seed_max - seed_min + 1
        node_index = self.node_id_index_map[node.node_id]
        seed_offset = jewel_seed - seed_min

        node_lut_index = (node_index * max_seed_index + seed_offset) * 8
        data = self._gv_fast_lookup(node_lut_index)

        # convert to int, enough tomfuckery
        trimmed_data = [int(x) for x in data]
        # from end of block, find idx of the first padding zero
        last_zero = None
        for i, x in enumerate(reversed(trimmed_data)):
            if x == 0:
                last_zero = -(i + 1)
            else:
                break

        if last_zero is not None:
            trimmed_data = trimmed_data[0:last_zero]

        capture_roll_range = r'(\(\d+-\d+\))'

        # replacement with 1 or 2 variable stats
        if len(trimmed_data) == 2 or len(trimmed_data) == 3:
            index = self._get_add_replace_index(trimmed_data[0]) - MAGIC_NUMBER
            replacement_node = self.replacements[index]
            new_stats: List[Tuple[dict, List[float|int]]] = []

            for x in range(len(trimmed_data) - 1):
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

                val = str(trimmed_data[x + 1])
                # stat isn't a whole number, need to format it
                if '.' in replacement_node['sd'][sd_index]:
                    # reverse it and slap a decimal point in there
                    val = val[-1] + '.' + val[0]
                
                template = re.sub(capture_roll_range,
                                       '{}',
                                       replacement_node['sd'][sd_index])

                stat_dict = {
                    'dn': None,
                    'sd': [template],
                    'stats': {
                        'statOrder': stat_order
                    }
                }
                new_stats.append((stat_dict, [float(val) if '.' in val else int(val)]))

            return replacement_node['dn'], new_stats

        # 3 or 4 small nodes in a trenchcoat
        elif len(trimmed_data) == 6 or len(trimmed_data) == 8:
            node_name = self._get_gv_node_name(trimmed_data)
            new_stats: List[Tuple[dict, List[float | int]]] = []

            half_size = int(len(trimmed_data) / 2)
            parsed_stats = {} # template: {value, order}
            for x in range(half_size):
                index = self._get_add_replace_index(trimmed_data[x])
                stats_dict = self.additions[index]['stats']
                # there's always just 1 stat here, apply the value directly to the 'stat'
                stat_name = next(iter(stats_dict.keys()))
                stat_val = trimmed_data[x + half_size]
                stat_str = self.additions[index]['sd'][0]
                stat_order = stats_dict[stat_name]['statOrder']

                if '(' not in stat_str:
                    template = re.sub(str(trimmed_data[x + half_size]), '{}', stat_str, count=1)
                else:
                    template = re.sub(capture_roll_range, '{}', stat_str, count=1)

                if stat_name in parsed_stats.keys():
                    # we already added this stat, just add its value to the existing one
                    parsed_stats[template]['value'] += stat_val
                else:
                    parsed_stats[template]['value'] = stat_val

                parsed_stats[template]['order'] = stat_order

            for template in parsed_stats.keys():
                stat_dict = {
                    'dn': None,
                    'sd': [template],
                    'stats': {
                        'statOrder': parsed_stats[template]['order']
                    }
                }
                new_stats.append((stat_dict, [parsed_stats[template]['value']]))

            return node_name, new_stats

        else:
            raise Exception(f'Invalid data block for node {node.node_id}: {trimmed_data}')

    def _get_gv_node_name(self, trimmed_data: List[int]) -> str:
        """
        The 'assembled' nodes for GV can either be Might of the Vaal or Legacy of the Vaal

        The addition effects have icons (fist or palm) that they display when they are applied to small nodes
        The name of the assembled node is determined by the last addition that will be applied
        """
        last_addition_idx = trimmed_data[int((len(trimmed_data) / 2)) - 1]
        additions_id_str = self.additions[last_addition_idx]['id']
        icon_name = list(filter(lambda n: n['id'] == additions_id_str, self.replacements))[0]['icon']
        return 'Might of the Vaal' if 'Offensive' in icon_name else 'Legacy of the Vaal'

    def _apply_node_effects_gv(self, node: Node, jewel_stats: JewelStats):
        new_name, add_stat_params = self._fast_lookup_node_gv(int(self._seed), node)
        stats = []
        for param_tuple in add_stat_params:
            stats.append(jewel_stats.add_stat(*param_tuple))
        node.make_tooltip_from_replacement(new_name, stats)