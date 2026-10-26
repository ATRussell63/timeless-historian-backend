import math
from typing import Dict, List

from app.scripts.parse_tree_json.constants import TreeConstants
from classes import Anchor, ConnectedNodes, TreeNode
from tree_data import TREE_JSON

class TreeNodes:

    def __init__(self):
        self._node_registry: Dict[int, TreeNode] | None = None
        self._constants = TreeConstants()

    @property
    def _nodes(self) -> dict:
        if self._node_registry is None:
            self._build_registry()

        return self._node_registry

    def get(self, node_id: int) -> TreeNode:
        return self._nodes[node_id]

    def get_by_name(self, node_name: str) -> TreeNode:
        return list(filter(lambda n: n.name.upper() == node_name,
                           self._nodes.values))[0]

    @staticmethod
    def _get_node_tags(node: dict) -> List[str]:
        tags = []

        if not node.get('group'):
            tags.append('cluster_passive')
        if node.get('classStartIndex') is not None:
            tags.append('class_start')
        if node.get('isAscendancyStart'):
            tags.append('ascendancy_start')
        if node.get('ascendancyName') is not None:
            tags.append('ascendancy')
        if node.get('isBlighted'):
            tags.append('blight')
        if node.get('isMastery'):
            tags.append('mastery')
        if node.get('isKeystone'):
            tags.append('keystone')
        if node.get('isNotable'):
            tags.append('notable')
        if node.get('isJewelSocket'):
            tags.append('jewel_socket')

        if len(tags) == 0 or tags == ['ascendancy']:
            tags.append('small_passive')

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

            self._node_registry[node['skill']] = TreeNode(node_id=node['skill'],
                                                name=node['name'],
                                                tags=self._get_node_tags(node),
                                                ascendancy=node.get('ascendancyName'),
                                                stats=node.get('stats'),
                                                reminder_text=node.get('reminderText'),
                                                anchor=self._create_anchor(node),
                                                connected_nodes=ConnectedNodes(path_out=node['out'],
                                                                               path_in=node['in']))
