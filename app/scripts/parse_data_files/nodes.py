import math
from enum import Enum
from typing import Dict, List

from app.scripts.parse_data_files.constants import TreeConstants
from app.util.utils import intersection_has_any
from classes import Anchor, ConnectedNodes, Node
from tree_data import TREE_JSON

class Tag(Enum):
    CLUSTER = 'cluster_passive'
    CLASS_START = 'class_start'
    ASCENDANCY_START = 'ascendancy_start'
    ASCENDANCY = 'ascendancy'
    BLIGHT = 'blight'
    MASTERY = 'mastery'
    KEYSTONE = 'keystone'
    NOTABLE = 'notable'
    JEWEL_SOCKET = 'jewel_socket'
    SMALL = 'small_passive'

class TreeNodes:

    def __init__(self):
        self._node_registry: Dict[int, Node] | None = None
        self._constants = TreeConstants()

    @property
    def _nodes(self) -> dict:
        if self._node_registry is None:
            self._build_registry()

        return self._node_registry or {}

    def get(self, node_id: int) -> Node:
        return self._nodes[node_id]

    def get_by_name(self, node_name: str) -> Node:
        return list(filter(lambda n: n.name.upper() == node_name,
                           self._nodes.values()))[0]

    def get_all_by_tags(self, select_tags: List[Tag]) -> Dict[int, Node]:

        return {node_id: node for node_id, node in self._nodes.items() \
                if intersection_has_any([tag.values for tag in node.tags], select_tags)}

    @staticmethod
    def _get_node_tags(node: dict) -> List[Tag]:
        tags = []

        if not node.get('group'):
            tags.append(Tag.CLUSTER)
        if node.get('classStartIndex') is not None:
            tags.append(Tag.CLASS_START)
        if node.get('isAscendancyStart'):
            tags.append(Tag.ASCENDANCY_START)
        if node.get('ascendancyName') is not None:
            tags.append(Tag.ASCENDANCY)
        if node.get('isBlighted'):
            tags.append(Tag.BLIGHT)
        if node.get('isMastery'):
            tags.append(Tag.MASTERY)
        if node.get('isKeystone'):
            tags.append(Tag.KEYSTONE)
        if node.get('isNotable'):
            tags.append(Tag.NOTABLE)
        if node.get('isJewelSocket'):
            tags.append(Tag.JEWEL_SOCKET)

        if len(tags) == 0 or tags == ['ascendancy']:
            tags.append(Tag.SMALL)

        return tags

    def _calc_anchor_angle(self, node: dict) -> float:
        skills_per_orbit = self._constants.skills_per_orbit(node['orbit'])
        # hardcoded angles from pob /src/Classes/PassiveTree.lua
        if skills_per_orbit == 16:
            angles = [0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330]

        elif skills_per_orbit == 40:
            angles = [0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 110, 120, 130, 135, 140,
                      150, 160, 170, 180, 190, 200, 210, 220, 225, 230, 240, 250, 260, 270, 280,
                      290, 300, 310, 315, 320, 330, 340, 350]
        else:
            angles = [x * (360 / skills_per_orbit) for x in range(skills_per_orbit)]

        angle = angles[node['orbitIndex']]
        # rotate into our new cursed paradigm
        return math.radians(angle - 90)

    def _create_anchor(self, node: dict) -> Anchor:
        group = TREE_JSON['groups'][str(node['orbit'])]

        return Anchor(id=node['orbit'],
                      global_x=group['x'],
                      global_y=group['y'],
                      radius=self._constants.orbit_radius(node['orbit']),
                      angle=self._calc_anchor_angle(node))

    def _build_registry(self):
        nodes = TREE_JSON['nodes']

        for key in nodes.keys():
            if key == 'root':
                # Currently not using the root for anything, ignore it
                continue

            node = nodes[key]

            self._node_registry[node['skill']] = Node(node_id=node['skill'],
                                                      name=node['name'],
                                                      tags=self._get_node_tags(node),
                                                      ascendancy=node.get('ascendancyName'),
                                                      stats=node.get('stats'),
                                                      anchor=self._create_anchor(node),
                                                      connected_nodes=ConnectedNodes(path_out=node['out'],
                                                                                     path_in=node['in']))
