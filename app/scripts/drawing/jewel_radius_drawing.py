import math
import re
from typing import List, Dict, Tuple
from collections import defaultdict, deque
from math import isclose
from numpy import inf
import copy
import logging
import app.scripts.get_jewel_effects as je
from app.scripts.classes import DrawingRoot, StraightEdge, CurvedEdge, Jewel, Vertex
from app.scripts.parse_tree_json.classes import Node
from app.scripts.parse_tree_json.constants import TreeConstants
from app.scripts.parse_tree_json.nodes import TreeNodes
from app.util.parse_jewel import ParsedJewel

RELEVANT_NODE_TYPES = ['keystone', 'notable', 'small_passive', 'jewel_socket']

ZORATH_UNSUPPORTED_CLASSES = ['ASCENDANT', 'RELIQUARIAN']

CLASS_START_NODE_ALIASES = {
    "SHADOW": "SIX",
    "SCION": "SEVEN"
}

logger = logging.getLogger('main')


def node_is_in_jewel_radius(n: Vertex, j: Vertex, radius):
    xComponent = (n.x - j.x) ** 2
    yComponent = (n.y - j.y) ** 2
    return math.sqrt(xComponent + yComponent) <= radius


class JewelDrawing:
    """
    Encompasses everything required to generate a json definition of how to draw the nodes and edges
    of a particular jewel socket for a particular character.
    """

    def __init__(self):
        self._nodes = TreeNodes()
        self._constants = TreeConstants()

        # self._TREE_DATA = None
        # TODO - marauder bottom starting node and quickstep have caused problems before
        #        I don't have an intelligent reason for this value, it's a manual tuning issue
        self.TIMELESS_JEWEL_RADIUS = 1800

    @property
    def nodes(self):
        return self._nodes

    def make_timeless_drawing(self, jewel: ParsedJewel, allocated_hashes:List[int], anointed_node_names: List[str]) -> DrawingRoot:
        """ We need the api response for the list of allocated nodes and the jewel api id
            (since we're not saving that one in the db).

            Returns the full json that the frontend will need to draw a cutout of the passive tree.
        """
        logger.debug(f'Begin drawing for jewel: {jewel.jewel_type} {jewel.seed} {jewel.general}')

        # find the nodeIds for the allocated nodes, add them to the list
        anointed_hashes = self.lookup_hashes_from_node_names(anointed_node_names)
        allocated_hashes.extend(anointed_hashes)
        allocated_hashes = list(set(allocated_hashes))

        drawing = self.make_pre_transform_drawing(int(jewel.socket_id), allocated_hashes)
        drawing, jewel_stats, allocated_keystone = self.apply_jewel_changes(drawing, jewel)
        drawing.curved_edges = self.coalesce_curved_edges(drawing)
        drawing.straight_edges = self.coalesce_straight_edges(drawing)
        jewel_stat_list = self.jewel_stats_dict_to_list(jewel_stats)
        drawing.jewel_stats = jewel_stat_list
        drawing.jewel_type = jewel.jewel_type
        drawing = self.truncate_values(drawing)
        return drawing

    def make_abyss_dominion_drawing(self, jewel: ParsedJewel, allocated_hashes:List[int], anointed_node_names: List[str]) -> DrawingRoot:
        pass

    def make_zorath_drawing(self, jewel: ParsedJewel, allocated_hashes:List[int], base_class: str,
                            ascendancy_class: str, ff_ascend_node: str) -> DrawingRoot:



        # if flesh & flame are active, find the node object
        if ff_ascend_node is not None:
            ascend_node = list(filter(lambda n: n['name'] == ff_ascend_node, self.tree_data['nodes']))[0]
            allocated_hashes.append(ascend_node['skill'])

        # make drawing of the ascendancy
        drawing = self.make_pre_transform_ascend_drawing()

        # mutate the node that got replaced by Zorath

        # do the tree crawl and get the nodeIds along the shortest path to class start


        pass

    # def get_passive_coords(self, node: Node) -> Vertex:
    #     anchor = node.anchor
    #
    #     local_x = (math.cos(anchor.angle) * anchor.radius) + anchor.global_x
    #     local_y = (math.sin(anchor.angle) * anchor.radius) + anchor.global_y
    #
    #     return Vertex(local_x, local_y)

    def make_node_objs(self, passive_types: List[str]) -> Dict[int, Node]:

        output = {}
        nodes_json = self.tree_data['nodes']
        for node in nodes_json.values():
            if self.node_type(node) not in passive_types:
                continue

            group = self.tree_data['groups'][str(node['group'])]
            output[int(node['skill'])] = self.make_node(node, group, False)

        return output

    def exclude_connected_class_start(self, node: Node, class_name: str) -> Node:
        if class_name in CLASS_START_NODE_ALIASES:
            class_name = CLASS_START_NODE_ALIASES.get(class_name.lower()).upper()

        # get the actual id of the class start node
        excluded_node = self.nodes.get_by_name(class_name)
        return self.prune_connected_node(node, excluded_node.node_id)

    @staticmethod
    def prune_connected_node(node: Node, node_id: int) -> Node:
        node.connected_nodes.path_in.remove(node_id)
        node.connected_nodes.path_out.remove(node_id)
        return node

    # def make_node(self, node: TreeNode, allocated: bool, excluded_class_start: Optional[str] = None):
    #     connected_node_set = set(node.connected_nodes.path_in + node.connected_nodes.path_out)
    #     if excluded_class_start:
    #         # find the class name alias (only shadow and scion are aliased)
    #         if excluded_class_start in CLASS_START_NODE_ALIASES:
    #             excluded_class_start = CLASS_START_NODE_ALIASES.get(excluded_class_start.lower()).upper()
    #
    #         # get the actual id of the class start node
    #         excluded_node = self.nodes.get_by_name(excluded_class_start)
    #         connected_node_set.remove(excluded_node.node_id)

        # return Node(
        #     name=node.name,
        #     node_id=node.node_id,
        #     node_types=node.tags,
        #     allocated=allocated,
        #     absolute_coords=self.get_passive_coords(node),
        #     relative_coords=None,
        #     mods=node.stats,
        #     reminder=node.reminder_text,
        #     anchor=node.anchor,
        #     connected_nodes=list(connected_node_set),
        #     tooltip=None
        # )

    def make_jewel_objs(self) -> Dict[int, DrawingRoot]:

        output = {}
        jewel_sockets = self._constants.jewel_slots

        for i, jewel_id in enumerate(jewel_sockets):
            try:
                jewel_node = self.nodes.get(jewel_id)
                name = jewel_node.name
                if 'Medium' in name or 'Small' in name:
                    continue

                absolute_coords = self.get_passive_coords(jewel_node)
                output[jewel_id] = DrawingRoot(
                    jewel_id=jewel_id,
                    api_idx=i,
                    jewel_type=None,
                    jewel_stats=None,
                    jewel_coords=absolute_coords,
                    radius=self.TIMELESS_JEWEL_RADIUS,
                    nodes={},
                    curved_edges=[],
                    straight_edges=[]
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
                if not node_is_in_jewel_radius(node.absolute_coords,
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
    
    def truncate_float(self, number, decimal_places):
        factor = 10**decimal_places
        return math.floor(number * factor) / factor
    
    def truncate_vert(self, vert: Vertex, decimal_places):
        return Vertex(
            x=self.truncate_float(vert.x, decimal_places),
            y=self.truncate_float(vert.y, decimal_places)
        )

    def make_straight_edge(self, start_node: Node, end_node: Node) -> StraightEdge:
        edge = StraightEdge(
            allocated=start_node.allocated and end_node.allocated,
            ends=[
                {
                    'node_id': start_node.node_id,
                    'relative': start_node.relative_coords,
                },
                {
                    'node_id': end_node.node_id,
                    'relative': end_node.relative_coords,
                }
            ]
        )
        return edge

    def make_curved_edge(self, start_node: Node, end_node: Node, max_orbits: int):
        edge = CurvedEdge(
            allocated=start_node.allocated and end_node.allocated,
            relative_center=start_node.group_relative_coords,
            rotation=self.calc_arc_rotation(start_node.orbitIndex,
                                            end_node.orbitIndex,
                                            max_orbits, True),
            radius=start_node.orbitRadius,
            angle=self.calc_angle(start_node, end_node, start_node.orbitRadius, max_orbits),
        )
        return edge

    def lookup_hashes_from_node_names(self, anointed_node_names: List[str]) -> List[int]:
        notables_processed = []
        hash_list = []
        # I was tempted to hardcode ignore Worship the Blightheart but we'll keep it in here
        # blighted nodes get filtered in a later process
        tree_notables = [node for node in self.tree_data['nodes'].values() if node.get('isNotable') is True or node.get('isBlighted') is True]
        
        for node in tree_notables:
            try:
                notable_idx = anointed_node_names.index(node['name'])
                # assumed to be found, value error if not
                hash_list.append(node['skill'])
                notables_processed.append(anointed_node_names[notable_idx])
            except ValueError:
                pass

            if set(anointed_node_names) == set(notables_processed):
                break
        
        return hash_list

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
        output_obj.curved_edges = []
        output_obj.straight_edges = []
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
                    output_obj.curved_edges.append(edge)
                else:
                    edge = self.make_straight_edge(start_node, end_node)
                    output_obj.straight_edges.append(edge)

                traversed_edges.add((node_idx, connected_node))
                if output_obj.nodes.get(connected_node) is not None:
                    traverse(connected_node)

        traverse(jewel_obj.jewel_id)

        # wrap up any remaining nodes that didn't get covered by the initial traversal
        # remaining_nodes = (set(jewel_obj.nodes.keys()) & set(allocated_hashes)) - traversed_nodes
        remaining_nodes = set(jewel_obj.nodes.keys()) - traversed_nodes
        for node_idx in remaining_nodes:
            traverse(node_idx)

        jewel_obj.curved_edges = output_obj.curved_edges
        jewel_obj.straight_edges = output_obj.straight_edges

        return jewel_obj

    def make_pre_transform_ascend_drawing(self, allocated_hashes: List[int], base_class: str, ascendancy_class: str):
        """
        Makes a drawing of the primary ascendancy for this class.

        Each base class has a dummy 'starting node' that connects the ascendancy tree to the rest of the actual passive tree.
        That dummy node also connects to the 'start nodes' of the base class.

        Normally we'd crawl this tree, but since Forbidden Flesh and Flame can allocate these nodes, and the tree is rather small,
        it's probably fine to just filter for nodes that have a matching ascendancyName.
        """

        ascend_nodes = [node for node in self.nodes.values()
                        if node.get('ascendancyName', '') == ascendancy_class]

        # find the 'root node' of the ascendancy - this node has no stats and shouldn't have a tooltip
        # but it does need to be rendered (probably as a small node)
        ascend_root_node = list(filter(lambda n: n.get('isAscendancyStart', False) is True,
                                  ascend_nodes))[0]

        # fortunately all ascendancy nodes are part of their own group
        ascend_group = self.groups[str(ascend_root_node['group'])]

        # make the friggin drawing
        nodes = []
        for node in ascend_nodes:
            nodes.append(self.make_node(node=node, group=ascend_group, allocated=node['skill'] in allocated_hashes))

        # remove the class start node
        self.make_node(node=ascend_root_node, group=ascend_group, allocated=False, excluded_class_start=base_class)

        # now make the edges (MUCH simpler since we're trapped in this group)
        straight_edges = []
        curved_edges = []

        def traverse(start_node_id: int, flow_direction: str, is_root: bool):
            start_node = self.nodes[str(start_node_id)]

            start_is_allocated = is_root or start_node_id in allocated_hashes
            start_orbit = start_node['orbit']

            for end_node_id in start_node[flow_direction]:
                end_node = self.get_node_by_id(end_node_id)
                end_orbit = end_node['orbit']

                if start_orbit == end_orbit:
                    self.make_curved_edge(start_node, end_node,
                                          self.tree_data['constants']['skillsPerOrbit'][start_node.orbit])
                else:
                    self.make_straight_edge()

                traverse(node, flow_direction)

        # all ascendancies except Reliquarian go 'out' from class node
        traverse(ascend_root_node['skill'], 'out', True)


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
        elif timeless_jewel.jewel_type == 'Heroic Tragedy':
            main_string = f'Remembrancing {timeless_jewel.seed} songworthy deeds by the line of {timeless_jewel.general}'
            conquered_str += 'Kalguur'
        body = [main_string, conquered_str]
        if timeless_jewel.mf_mods:
            body += timeless_jewel.mf_mods
        body += ['Historic']
        return NodeTooltip(
            title=timeless_jewel.jewel_type,
            body=body,
            replaced_title=None
        )

    def get_stat_from_effect_dict(self, effect: dict):

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
                if effect['dn'] in ('Legacy of the Vaal', 'Might of the Vaal'):
                    # these come with their own pre-formatted values
                    if jewel_stats.get(stat_name) is None:
                        jewel_stats[stat_name] = {
                            'template': v['template'],
                            'val': v['val']
                        }
                    else:
                        jewel_stats[stat_name]['val'] += v['val']
                else:
                    # string in sd
                    sd = effect['sd'][stat_index]
                    # get val of stat
                    val = re.search(capture_val, sd).group(0)
                    val = float(val) if '.' in str(val) else int(val)

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
            val = round(per_ten_numeric * coeff, 1)

            template = re.sub(str(per_ten_devotion), '{val}', mod, count=1)
            # get rid of the per 10 Devotion suffix, it's misleading
            template = re.sub(' per 10 Devotion', '', template)

            jewel_stats[f'mf_mod_{i + 1}'] = {
                'template': template,
                'val': val
            }
        
        return jewel_stats

    def build_keystone_details(self, keystone_node: dict, replaced_node: dict) -> dict:
        """
        Now that there are keystones that will be invisible to the jewel drawing, it's especially nice to provide
        some info about the allocated keystone so the frontend can display it.

        'keystone': {
            'name': 'From Below',
            'description': [
                'Insufficient Mana doesn't prevent your Spells',
                'Cannot recover Mana'
            ],
            'replaced': 'Void Beacon'
        }
        """

        return {
            'name': keystone_node['dn'],
            'description': keystone_node['sd'],
            'replaced': replaced_node['name']
        }
    

    def apply_jewel_changes(self, jewel_drawing: DrawingRoot, timeless_jewel: ParsedJewel) -> Tuple[DrawingRoot, Dict, Dict]:
        """ Determines the changes that will apply to all nodes in the jewel, and applies them (as tooltips). """

        jewel_stats = {}
        converter = je.NodeLookup()
        # first, the layups (keystone / small nodes)
        if timeless_jewel.general != 'Zorath':
            keystone = converter.lookup_jewel_keystone(timeless_jewel.general)
        else:
            # TODO
            keystone = None

        allocated_keystone = None

        for k, node in jewel_drawing.nodes.items():
            # logger.debug(f'Processing {node.name}, {node.node_id}')
            if node.has_tag('jewel_socket'):
                if node.node_id == jewel_drawing.jewel_id:
                    # timeless jewel socket
                    node.tooltip = self.make_timeless_jewel_tooltip(timeless_jewel)
                else:
                    # socket in radius
                    node.tooltip = self.make_tooltip(node, {'sd': []}, False)
            elif node.has_tag('keystone'):
                node.tooltip = self.make_tooltip(node, keystone, True)

                if node.allocated and allocated_keystone is None and timeless_jewel.general != 'Zorath':
                    allocated_keystone = self.build_keystone_details(keystone, node)


            elif node.has_tag('small_passive') and timeless_jewel.jewel_type != 'Glorious Vanity':
                effect, replaced = converter.lookup_small_node(timeless_jewel.jewel_type, node)
                node.tooltip = self.make_tooltip(node, effect, replaced)

                if node.allocated:
                    jewel_stats = self.add_effect_to_jewel_stats(jewel_stats, effect)

            elif node.has_tag('notable') and timeless_jewel.jewel_type != 'Glorious Vanity':
                effect = converter.lookup_notable_non_gv(timeless_jewel.jewel_type,
                                                                   int(timeless_jewel.seed),
                                                                   node)
                # TODO - I think we need to format the range placeholders here, or update the jewel stats in the same method

                node.make_tooltip(*effect)

                if node.allocated:
                    jewel_stats = self.add_effect_to_jewel_stats(jewel_stats, effect)
            else:
                # any node type and Glorious Vanity
                effect, replaced = converter.fast_lookup_node_gv(int(timeless_jewel.seed),
                                                                 node)
                node.tooltip = self.make_tooltip(node, effect, replaced)

                if node.allocated:
                    jewel_stats = self.add_effect_to_jewel_stats(jewel_stats, effect)

        # finally apply devotion to jewel mods
        if timeless_jewel.jewel_type == 'Militant Faith':
            jewel_stats = self.add_mf_mod_effect_to_jewel_stats(jewel_stats, timeless_jewel.mf_mods)

        return jewel_drawing, jewel_stats, allocated_keystone

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
    
    def coalesce_curved_edges(self, drawing: DrawingRoot) -> List[CurvedEdge]:
        """ Adjacent edges can situationally be merged into one.
            
            Curved edges with the same center, allocated val and 1 common endpoint can be merged.
        """

        def key(edge: CurvedEdge) -> Tuple[bool, Vertex]:
            return (edge.allocated, edge.relative_center)

        # Group by (allocated, relative_center)
        groups = defaultdict(list)
        for edge in drawing.curved_edges:
            groups[key(edge)].append(edge)

        merged_curved_edges = []

        for group_key, group_edges in groups.items():
            # Sort by rotation
            group_edges.sort(key=lambda e: e.rotation)

            i = 0
            while i < len(group_edges):
                current = group_edges[i]
                start_rotation = current.rotation
                total_angle = current.angle
                radius = current.radius

                j = i + 1
                while j < len(group_edges):
                    next_edge = group_edges[j]
                    end_rotation = start_rotation + total_angle

                    if isclose(end_rotation, next_edge.rotation) and isclose(radius, next_edge.radius):
                        # Extend the arc
                        total_angle += next_edge.angle
                        j += 1
                    else:
                        break

                # Add the merged edge
                merged_curved_edges.append(CurvedEdge(
                    allocated=current.allocated,
                    relative_center=current.relative_center,
                    rotation=start_rotation,
                    radius=radius,
                    angle=total_angle
                ))

                i = j

        return merged_curved_edges

    def coalesce_straight_edges(self, drawing: DrawingRoot) -> List[StraightEdge]:
        """ Adjacent edges can situationally be merged into one.

            Straight edges with at least 1 common endpoint and same slope can be merged.
        """

        def slope(edge: StraightEdge):
            # measure 'starting from bottom left'
            y1 = edge.ends[0]['relative'].y
            y2 = edge.ends[1]['relative'].y
            deltaY = y2 - y1
            x1 = edge.ends[0]['relative'].x
            x2 = edge.ends[1]['relative'].x
            deltaX = x2 - x1

            if isclose(deltaX, 0):
                return inf

            return self.truncate_float(deltaY / deltaX, 1)
        
        # group edges by slope
        edge_groups = defaultdict(list)
        for edge in drawing.straight_edges:
            edge_slope = slope(edge)
            edge_groups[edge_slope].append(edge)
        
        def merge_straight_edges(slope: float, edges: List[StraightEdge]) -> List[StraightEdge]:
            result = []

            # Group edges by allocated value
            groups = defaultdict(list)
            for edge in edges:
                groups[edge.allocated].append(edge)

            for allocated_value, group in groups.items():
                # Build adjacency list and node_id → end_dict mapping
                graph = defaultdict(set)
                node_id_to_end = {}

                for edge in group:
                    id1 = edge.ends[0]['node_id']
                    id2 = edge.ends[1]['node_id']
                    graph[id1].add(id2)
                    graph[id2].add(id1)
                    node_id_to_end[id1] = edge.ends[0]
                    node_id_to_end[id2] = edge.ends[1]

                visited = set()

                def bfs(start):
                    component = set()
                    queue = deque([start])
                    while queue:
                        node = queue.popleft()
                        if node not in visited:
                            visited.add(node)
                            component.add(node)
                            queue.extend(graph[node] - visited)
                    return component

                all_node_ids = set(graph.keys())
                for node_id in all_node_ids:
                    if node_id not in visited:
                        component = bfs(node_id)
                        if len(component) == 1:
                            # Isolated node, find the full original edge
                            for edge in group:
                                ids = {edge.ends[0]['node_id'], edge.ends[1]['node_id']}
                                if ids == component:
                                    result.append(edge)
                                    break
                        else:
                            # find the extrema
                            if abs(slope) >= 1:
                                dim = 'y'
                            else:
                                dim = 'x'

                            # look for extrema
                            # end1 is max in this dim, end2 is min
                            end1 = None
                            end2 = None
                            for node_id in component:
                                end = node_id_to_end[node_id]
                                if not end1 and not end2:
                                    end1 = end
                                    end2 = end
                                else:
                                    if getattr(end['relative'], dim) > getattr(end1['relative'], dim):
                                        end1 = end
                                    elif getattr(end['relative'], dim) < getattr(end2['relative'], dim):
                                        end2 = end

                            result.append(StraightEdge(
                                allocated=allocated_value,
                                ends=[end1, end2]
                            ))

            return result
        
        merged_straight_edges = []
        for s, group in edge_groups.items():
            merged_straight_edges += merge_straight_edges(s, group)
        
        return merged_straight_edges

    def truncate_values(self, drawing: DrawingRoot) -> DrawingRoot:

        for node in drawing.nodes.values():
            node.absolute_coords = self.truncate_vert(node.absolute_coords, 2)
            node.relative_coords = self.truncate_vert(node.relative_coords, 2)
            node.group_absolute_coords = self.truncate_vert(node.group_absolute_coords, 2)
        
        for edge in drawing.straight_edges:
            for end in edge.ends:
                end['relative'] = self.truncate_vert(end['relative'], 2)
        
        for edge in drawing.curved_edges:
            edge.relative_center = self.truncate_vert(edge.relative_center, 2)
            edge.rotation = self.truncate_float(edge.rotation, 2)
            edge.radius = self.truncate_float(edge.radius, 2)
            edge.angle = self.truncate_float(edge.angle, 2)

        return drawing
