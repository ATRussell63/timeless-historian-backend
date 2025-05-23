import math
import json
import re
from typing import List, Dict, Tuple
import copy
import logging
import app.scripts.get_jewel_effects as je
from app.scripts.classes import Vertex, NodeTooltip, Node, DrawingRoot, StraightEdge, CurvedEdge, Jewel
from app.util.parse_jewel import ParsedJewel
from app.app_config import get_data_path

RELEVANT_NODE_TYPES = ['keystone', 'notable', 'small_passive', 'jewel_socket']

logger = logging.getLogger('main')


class JewelDrawing():
    """
    Encompasses everything required to generate a json definition of how to draw the nodes and edges
    of a particular jewel socket for a particular character.
    """

    def __init__(self):
        self._TREE_DATA = None
        # TODO - marauder bottom starting node and quickstep have caused problems before
        #        I don't have an intelligent reason for this value, it's a manual tuning issue
        self.TIMELESS_JEWEL_RADIUS = 1792

    @property
    def tree_data(self):
        # TODO - I think I want to save the tree data in the db later on
        if not self._TREE_DATA:
            with open(get_data_path() + 'data.json', 'r') as tree_file:
                self._TREE_DATA = json.load(tree_file)

        return self._TREE_DATA

    def node_type(self, node_obj) -> str:
        if not node_obj.get('group'):
            return 'cluster_passive'
        elif 'classStartIndex' in node_obj.keys():
            return 'class_start'
        elif node_obj.get('isKeystone'):
            return 'keystone'
        elif node_obj.get('isNotable'):
            return 'notable'
        elif node_obj.get('isJewelSocket'):
            return 'jewel_socket'
        elif node_obj.get('isMastery'):
            return 'mastery'
        elif node_obj.get('ascendancyName') is not None:
            return 'ascendancy'
        elif node_obj.get('isBlighted'):
            return 'blight'
        # root node
        elif node_obj['group'] == 0:
            return 'root'
        else:
            return 'small_passive'

    def node_is_in_jewel_radius(self, n: Vertex, j: Vertex, radius):
        xComponent = (n.x - j.x) ** 2
        yComponent = (n.y - j.y) ** 2
        return math.sqrt(xComponent + yComponent) <= radius

    def get_passive_coords(self, passive: int) -> Vertex:
        group_idx = self.tree_data['nodes'][str(passive)]['group']
        gX, gY = self.tree_data['groups'][str(group_idx)]['x'], self.tree_data['groups'][str(group_idx)]['y']
        pOrbit = self.tree_data['nodes'][str(passive)]['orbit']
        pOrbitIndex = self.tree_data['nodes'][str(passive)]['orbitIndex']
        pOrbitRadius = self.tree_data['constants']['orbitRadii'][pOrbit]
        skillsPerOrbit = self.tree_data['constants']['skillsPerOrbit'][pOrbit]

        angle = math.radians(pOrbitIndex * (360 / skillsPerOrbit))
        # convert angle to our new cursed paradigm
        angle = angle - math.radians(90)

        pX = (math.cos(angle) * pOrbitRadius) + gX
        pY = (math.sin(angle) * pOrbitRadius) + gY

        return Vertex(pX, pY)

    def make_node_objs(self, passive_types: List[str]) -> Dict[int, Node]:

        output = {}
        nodes_json = self.tree_data['nodes']
        for node in nodes_json.values():
            if self.node_type(node) not in passive_types:
                continue

            group = self.tree_data['groups'][str(node['group'])]
            output[int(node['skill'])] = self.make_node(node, group, False)

        return output

    def make_node(self, node: dict, group: dict, allocated: bool):
        return Node(
            name=node['name'],
            node_id=int(node['skill']),
            node_type=self.node_type(node),
            allocated=allocated,
            absolute_coords=self.get_passive_coords(node['skill']),
            relative_coords=None,
            mods=node.get('stats'),
            reminder=node.get('reminderText'),
            orbit=node['orbit'],
            orbitRadius=self.tree_data['constants']['orbitRadii'][node['orbit']],
            orbitIndex=node['orbitIndex'],
            connected_nodes=node['out'] + node['in'],
            group_id=node['group'],
            group_absolute_coords=Vertex(group['x'],
                                         group['y']),
            group_relative_coords=None,
            tooltip=None
        )

    def make_jewel_objs(self) -> Dict[int, DrawingRoot]:

        output = {}
        jewel_sockets = self.tree_data['jewelSlots']
        nodes_json = self.tree_data['nodes']

        for i, jewel in enumerate(jewel_sockets):
            try:
                name = nodes_json[str(jewel)]['name']
                if 'Medium' in name or 'Small' in name:
                    continue

                absolute_coords = self.get_passive_coords(jewel)
                output[jewel] = DrawingRoot(
                    jewel_id=jewel,
                    api_idx=i,
                    jewel_type=None,
                    jewel_stats=None,
                    jewel_coords=absolute_coords,
                    radius=self.TIMELESS_JEWEL_RADIUS,
                    nodes={},
                    edges=[]
                )
            except KeyError:
                continue

        return output

    def build_jewel_to_nodes_in_radius_map(self) -> Dict[int, DrawingRoot]:
        nodes = self.make_node_objs(RELEVANT_NODE_TYPES)
        jewels = self.make_jewel_objs()

        output = {}
        for jewel in jewels.values():
            for node in nodes.values():
                if not self.node_is_in_jewel_radius(node.absolute_coords,
                                                    jewel.jewel_coords,
                                                    self.TIMELESS_JEWEL_RADIUS):
                    continue

                if output.get(jewel.jewel_id) is None:
                    output[jewel.jewel_id] = copy.deepcopy(jewel)

                output[jewel.jewel_id].nodes[node.node_id] = copy.deepcopy(node)

                # apply relative coords
                if node.node_id != jewel.jewel_id:
                    output[jewel.jewel_id].nodes[node.node_id].relative_coords = \
                        node.absolute_coords - jewel.jewel_coords
                else:
                    output[jewel.jewel_id].nodes[node.node_id].relative_coords = Vertex(0, 0)

                # update group with relative coords
                group_absolute_coords = output[jewel.jewel_id].nodes[node.node_id].group_absolute_coords
                output[jewel.jewel_id].nodes[node.node_id].group_relative_coords = \
                    group_absolute_coords - jewel.jewel_coords

        return output

    def adjust_orbit_index(self, index, maxOrbits):
        three_o_clock = math.ceil(maxOrbits / 4)
        if index < math.ceil(three_o_clock):
            index += maxOrbits

        index -= math.ceil(three_o_clock)
        return index

    def index_dist(self, a: int, b: int, m: int):
        return min(abs(a - b),
                   abs(a - (b + m)),
                   abs((a + m) - b))

    def calc_arc_len(self, a: Node, b: Node, r: float, maxOrbits: int) -> float:
        i_dist = self.index_dist(a.orbitIndex, b.orbitIndex, maxOrbits)
        angle = 360 * (i_dist / maxOrbits)
        # print(f'Angle between nodes {a.name} and {b.name} is {angle} degrees')
        arc_len = math.radians(angle) * r
        # print(f'Orbit radius between nodes {a.name} and {b.name} is {r}')
        return arc_len

    def calc_angle(self, a: Node, b: Node, r: float, maxOrbits: int) -> float:
        i_dist = self.index_dist(a.orbitIndex, b.orbitIndex, maxOrbits)
        angle = 360 * (i_dist / maxOrbits)
        return angle

    def calc_arc_rotation(self, orbitIndexA: int, orbitIndexB: int, maxOrbits: int, preserve_order=False) -> float:
        """ Konva's arcs behave similarly to the 'orbit' system on the PoE tree in the sense that they rotate clockwise.
            However, they always begin at 3 o-clock. This means we need to find the amount to rotate the arc by
            after drawing it.

            We can do this by establishing one of the nodes as the 'start' of the arc by finding the earlier orbitIndex.
            The PoE orbit indices start at 12 o-clock, though, so we need to account for that as well.
        """

        # make both indices 0-indexed off of the 3 o-clock position
        a = self.adjust_orbit_index(orbitIndexA, maxOrbits)
        b = self.adjust_orbit_index(orbitIndexB, maxOrbits)

        def measure_clockwise_dist(a, b, max):
            dist = 0
            pos = a
            while pos != b:
                if pos >= max:
                    pos = 0
                else:
                    pos += 1
                dist += 1

            return dist

        a_to_b = measure_clockwise_dist(a, b, maxOrbits)
        b_to_a = measure_clockwise_dist(b, a, maxOrbits)

        start_index = None
        if a_to_b < b_to_a:
            start_index = a
        elif a_to_b > b_to_a:
            start_index = b
        elif a_to_b == b_to_a:
            # god willing this never happens because this is arbitrary
            start_index = min(a, b)

        # find the rotation from arc start
        rotation = 360 * (start_index / maxOrbits)
        return rotation

    def make_straight_edge(self, start_node: Node, end_node: Node) -> StraightEdge:
        """
        Spec for an edge:
            {
                ?ends: [
                    {
                        'absX': 12345,
                        'absY': 12345,
                        'relX': 12345,
                        'relY': 12345
                    },
                    {
                        'absX': 23456,
                        'absY': 23456,
                        'relX': 12345,
                        'relY': 12345
                    }
                ]
                ?orbitCenter: {
                    'absX': 12345,
                    'absY': 12345,
                    'relX': 12345,
                    'relY': 12345
                },
                ?orbitRadius: 12345
            }
        """
        edge = StraightEdge(
            start=start_node.node_id,
            end=end_node.node_id,
            allocated=start_node.allocated and end_node.allocated,
            edge_type='StraightEdge',
            ends=[
                {
                    'absolute': start_node.absolute_coords,
                    'relative': start_node.relative_coords
                },
                {
                    'absolute': end_node.absolute_coords,
                    'relative': end_node.relative_coords
                }
            ]
        )
        return edge

    def make_curved_edge(self, start_node: Node, end_node: Node, max_orbits: int):
        edge = CurvedEdge(
            start=start_node.node_id,
            end=end_node.node_id,
            allocated=start_node.allocated and end_node.allocated,
            edge_type='CurvedEdge',
            absolute_center=start_node.group_absolute_coords,
            relative_center=start_node.group_relative_coords,
            rotation=self.calc_arc_rotation(start_node.orbitIndex,
                                            end_node.orbitIndex,
                                            max_orbits, True),
            arc_len=self.calc_arc_len(start_node, end_node, start_node.orbitRadius, max_orbits),
            radius=start_node.orbitRadius,
            angle=self.calc_angle(start_node, end_node, start_node.orbitRadius, max_orbits)
        )
        return edge

    def make_pre_transform_drawing(self, api_jewel_id: int, allocated_hashes: List[int]) -> dict:
        j_map = self.build_jewel_to_nodes_in_radius_map()

        output_obj = None
        for jewel_obj in j_map.values():
            if jewel_obj.api_idx == api_jewel_id:
                output_obj = jewel_obj
                break

        # label all allocated nodes
        for node in output_obj.nodes.values():
            node.allocated = node.node_id in allocated_hashes

        # identify all edges we need to make
        output_obj.edges = []
        edge_objects = []
        traversed_edges = set()
        traversed_nodes = set()

        def traverse(node_idx: int):
            try:
                traversed_nodes.add(node_idx)
                connected_nodes = set(list(int(x) for x in output_obj.nodes.get(node_idx).connected_nodes))
                # connected_nodes = list(connected_nodes & set(allocated_hashes))
            except KeyError:
                # node_idx was outside of radius which means it's time to stop traversing
                return

            for connected_node in connected_nodes:
                # exclude masteries
                if self.node_type(self.tree_data['nodes'][str(connected_node)]) not in RELEVANT_NODE_TYPES:
                    continue

                # has this edge already been processed?
                if (node_idx, connected_node) in traversed_edges \
                   or (connected_node, node_idx) in traversed_edges:
                    continue

                # mark it as traversed

                # if the connected node is in radius, we keep traversing
                if output_obj.nodes.get(connected_node) is not None:
                    end_node = output_obj.nodes[connected_node]
                else:
                    # node is outside the radius which means we need to get its coord details
                    node_json = self.tree_data['nodes'][str(connected_node)]
                    group_id = self.tree_data['nodes'][str(connected_node)]['group']
                    group = self.tree_data['groups'][str(group_id)]
                    nCoords = self.get_passive_coords(int(node_json['skill']))
                    jX, jY = output_obj.jewel_coords.x, output_obj.jewel_coords.y

                    # is the end node allocated?
                    end_allocated = node_json['skill'] in allocated_hashes

                    end_node = self.make_node(node_json, group, end_allocated)
                    end_node.relative_coords = Vertex(nCoords.x - jX, nCoords.y - jY)
                    end_node.group_relative_coords = Vertex(group['x'] - jX, group['y'] - jY)

                start_node = output_obj.nodes[node_idx]

                # nodes are in same group and orbit
                if start_node.group_id == end_node.group_id and start_node.orbit == end_node.orbit:
                    edge = self.make_curved_edge(start_node,
                                                 end_node,
                                                 self.tree_data['constants']['skillsPerOrbit'][start_node.orbit])
                else:
                    edge = self.make_straight_edge(start_node, end_node)

                edge_objects.append(edge)
                traversed_edges.add((node_idx, connected_node))
                if output_obj.nodes.get(connected_node) is not None:
                    traverse(connected_node)

        traverse(jewel_obj.jewel_id)

        # wrap up any remaining nodes that didn't get covered by the initial traversal
        # remaining_nodes = (set(jewel_obj.nodes.keys()) & set(allocated_hashes)) - traversed_nodes
        remaining_nodes = set(jewel_obj.nodes.keys()) - traversed_nodes
        for node_idx in remaining_nodes:
            traverse(node_idx)

        jewel_obj.edges = edge_objects

        # finally filter out all nodes that aren't allocated
        # jewel_obj.nodes = {k: v for k, v in jewel_obj.nodes.items() if v.node_id in allocated_hashes}
        return jewel_obj

    def make_tooltip(self, node: Node, change_data: dict, replaced: bool) -> NodeTooltip:
        if replaced:
            return NodeTooltip(
                title=change_data['dn'],
                body=change_data['sd'],
                replaced_title=node.name
            )
        else:
            return NodeTooltip(
                title=node.name,
                body=node.mods + change_data['sd'],
                replaced_title=None
            )

    def make_timeless_jewel_tooltip(self, timeless_jewel: ParsedJewel) -> NodeTooltip:
        conquered_str = 'Passives in radius are Conquered by the '
        if timeless_jewel.jewel_type == 'Glorious Vanity':
            main_string = f'Bathed in the blood of {timeless_jewel.seed} sacrificed in the name of {timeless_jewel.general}'
            conquered_str += 'Vaal'
        elif timeless_jewel.jewel_type == 'Elegant Hubris':
            main_string = f'Commissioned {timeless_jewel.seed} coins to commemorate {timeless_jewel.general}'
            conquered_str += 'Eternal Empire'
        elif timeless_jewel.jewel_type == 'Militant Faith':
            main_string = f'Carved to glorify {timeless_jewel.seed} new faithful converted by High Templar {timeless_jewel.general}'
            conquered_str += 'Templars'
        elif timeless_jewel.jewel_type == 'Lethal Pride':
            main_string = f'Commanded leadership over {timeless_jewel.seed} warriors under {timeless_jewel.general}'
            conquered_str += 'Karui'
        elif timeless_jewel.jewel_type == 'Brutal Restraint':
            main_string = f'Denoted service of {timeless_jewel.seed} dekhara in the akhara of {timeless_jewel.general}'
            conquered_str += 'Maraketh'
        body = [main_string, conquered_str]
        if timeless_jewel.mf_mods:
            body += timeless_jewel.mf_mods
        body += ['Historic']
        return NodeTooltip(
            title=timeless_jewel.jewel_type,
            body=body,
            replaced_title=None
        )

    def add_effect_to_jewel_stats(self, jewel_stats: dict, effect: dict) -> dict:
        """The effect of a jewel will either be to add or replace stats.
           To present the user with a total of all the stats the jewel represents,
           we build a list as we apply jewel changes.

           jewel_stats = {
                'fire_damage_+%': {
                    'template': '{val}% increased Fire Damage',
                    'val': 45
                },
                'energy_shield_recharge_rate_+%': {
                    'template': '{val}% increased Energy Shield Recharge Rate',
                    'val': 20
                },
                'base_energy_shield_leech_from_spell_damage_permyriad': {
                    'template': '{val}% of spell damage leeched as energy shield',
                    'val': 0.3
                }
           }
        """

        # do nothing for price of glory, at all
        if effect['dn'] == 'Price of Glory':
            return jewel_stats

        UNSCALABLE_STATS = [
            # Cloistered
            'immune_to_elemental_ailments_while_on_consecrated_ground_at_devotion_threshold',
            # Zealot
            'gain_arcane_surge_on_hit_at_devotion_threshold',
            # Add Onslaught
            'onslaught_buff_duration_on_kill_ms'
        ]

        capture_val = r'(\d+\.?\d*)'
        for k, v in effect['stats'].items():
            stat_index = v['index'] - 1
            stat_name = k
            # if stat is unscalable and not in jewel stats, just add it as is with no formatting
            if stat_name in UNSCALABLE_STATS:
                if jewel_stats.get(stat_name) is None:
                    jewel_stats[k] = {
                        'template': effect['sd'][stat_index],
                        # 'val': None
                    }
                else:
                    continue
            else:
                # string in sd
                sd = effect['sd'][stat_index]
                # get val of stat
                val = re.search(capture_val, sd).group(0)
                val = float(val) if '.' in val else int(val)

                if jewel_stats.get(stat_name) is None:
                    template_str = re.sub(str(val), '{val}', sd, count=1)
                    jewel_stats[stat_name] = {
                        'template': template_str,
                        'val': val
                    }
                else:
                    jewel_stats[stat_name]['val'] += val

        return jewel_stats

    def add_mf_mod_effect_to_jewel_stats(self, jewel_stats: dict, mf_mods: List[str]) -> dict:
        """ MF mods can be very powerful based on how much devotion the jewel is granting.
            This function updates the jewel mods based on the devotion total and adds them to the mf mods.
        """

        # get devotion total
        devotion = jewel_stats['base_devotion']['val']

        # get coeff value
        capture_val = r'(\d+\.?\d*)'

        for i, mod in enumerate(mf_mods):
            per_ten_devotion = re.search(capture_val, mod).group(0)
            per_ten_numeric = float(per_ten_devotion) if '.' in per_ten_devotion else int(per_ten_devotion)

            # these stats really are hard breakpoints at every 10 devotion
            # so we truncate the result
            coeff = math.floor(devotion / 10)
            val = per_ten_numeric * coeff

            template = re.sub(str(per_ten_devotion), '{val}', mod, count=1)
            # get rid of the per 10 Devotion suffix, it's misleading
            template = re.sub(' per 10 Devotion', '', template)

            jewel_stats[f'mf_mod_{i + 1}'] = {
                'template': template,
                'val': val
            }
        
        return jewel_stats

    def apply_jewel_changes(self, jewel_drawing: DrawingRoot, timeless_jewel: ParsedJewel) -> Tuple[DrawingRoot, Dict]:
        """ Determines the changes that will apply to all nodes in the jewel, and applies them (as tooltips). """

        jewel_stats = {}
        converter = je.NodeLookup()
        # first, the layups (keystone / small nodes)
        keystone = converter.lookup_jewel_keystone(timeless_jewel.general)

        for k, node in jewel_drawing.nodes.items():
            logger.debug(f'Processing {node.name}, {node.node_id}')
            if node.node_type == 'jewel_socket':
                if node.node_id == jewel_drawing.jewel_id:
                    # timeless jewel socket
                    node.tooltip = self.make_timeless_jewel_tooltip(timeless_jewel)
                else:
                    # socket in radius
                    node.tooltip = self.make_tooltip(node, {'sd': []}, False)
            elif node.node_type == 'keystone':
                node.tooltip = self.make_tooltip(node, keystone, True)

            elif node.node_type == 'small_passive' and timeless_jewel.jewel_type != 'Glorious Vanity':
                effect, replaced = converter.lookup_small_node(timeless_jewel.jewel_type, node)
                node.tooltip = self.make_tooltip(node, effect, replaced)
                jewel_stats = self.add_effect_to_jewel_stats(jewel_stats, effect)

            elif node.node_type == 'notable' and timeless_jewel.jewel_type != 'Glorious Vanity':
                effect, replaced = converter.lookup_notable_non_gv(timeless_jewel.jewel_type,
                                                                   int(timeless_jewel.seed),
                                                                   node)
                node.tooltip = self.make_tooltip(node, effect, replaced)
                jewel_stats = self.add_effect_to_jewel_stats(jewel_stats, effect)
            else:
                # any node type and Glorious Vanity
                effect, replaced = converter.fast_lookup_node_gv(int(timeless_jewel.seed),
                                                                 node)
                node.tooltip = self.make_tooltip(node, effect, replaced)
                jewel_stats = self.add_effect_to_jewel_stats(jewel_stats, effect)

        # finally apply devotion to jewel mods
        if timeless_jewel.jewel_type == 'Militant Faith':
            jewel_stats = self.add_mf_mod_effect_to_jewel_stats(jewel_stats, timeless_jewel.mf_mods)

        return jewel_drawing, jewel_stats

    def jewel_stats_dict_to_list(self, jewel_stats: dict) -> List[str]:
        """ Now that we have the stat totals we just need to apply them to the string template and order them.

            While this is pretty arbitrary, I like sorting these stats by value descending.
        """
        
        # get devotion total
        # devotion = jewel_stats.get('base_devotion', {}).get('val', 0)

        # sort the stats dict by val desc
        sorted_stats = dict(sorted(jewel_stats.items(), key=lambda item: item[1].get('val', 0), reverse=True))

        output = []
        for k, v in sorted_stats.items():
            # TODO - this would be a nice thing but I'm not parsing Unnatural Instinct right now
            #        so this could be very misleading
            # skip conditional devotion mods if we dont have enough devotion
            # if '150 Devotion' in v['template'] and devotion < 150:
            #     continue

            # unscalable stat, just add the template to the list
            if not v.get('val'):
                output.append(v['template'])
            else:
                output.append(v['template'].format(val=v['val']))
        
        return output

    def make_drawing(self, api_response: dict, jewel: ParsedJewel) -> DrawingRoot:
        """ We need the api response for the list of allocated nodes and the jewel api id
            (since we're not saving that one in the db).
 
            Returns the full json that the frontend will need to draw a cutout of the passive tree.
        """
        logger.debug(f'Begin drawing for jewel: {jewel.jewel_type} {jewel.seed} {jewel.general}')
        # api_jewel_id = None
        # for k, v in api_response['jewel_data'].items():
        #     if v['type'] == 'JewelTimeless':
        #         api_jewel_id = int(k)
        #         break
        
        allocated_hashes = api_response['hashes']

        drawing = self.make_pre_transform_drawing(int(jewel.socket_id), allocated_hashes)
        logger.debug('Drawing base done.')
        drawing, jewel_stats = self.apply_jewel_changes(drawing, jewel)
        logger.debug('Jewel changes applied.')
        jewel_stat_list = self.jewel_stats_dict_to_list(jewel_stats)
        drawing.jewel_stats = jewel_stat_list
        drawing.jewel_type = jewel.jewel_type
        logger.debug('Stat totals applied.')
        return drawing
