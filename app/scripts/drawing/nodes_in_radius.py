
"""
Keeps a record of which nodes we calculated are in radius of each jewel socket.

We can generate these lists once per patch and reuse them rather than doing the search fresh every time.
"""
import json
import math
import pathlib
from typing import List, Dict

from app.app_config import get_data_path
from app.scripts.classes import Vertex
from app.singletons import LD_CACHE, FULL_TREE_DRAWING, NODE_DB
from app.scripts.drawing.domain_node_bounds import DOMAIN_BOUNDS_GUIDE, NodeRef

# TODO - marauder bottom starting node and quickstep have caused problems before
#        I don't have an intelligent reason for this value, it's a manual tuning issue
TIMELESS_JEWEL_RADIUS = 1800

RADIUS_MAP_DIR = get_data_path() + "socket_radius_map.json"
DOMAIN_MAP_DIR = get_data_path() + "socket_domain_map.json"

# add a list of nodes that we want to include that the search isn't picking up
RADIUS_INCLUDES_OVERRIDE = {}
DOMAIN_INCLUDES_OVERRIDE = {}

class SocketToNodesMapper:

    def __init__(self):
        self._radius_map = self.build_or_retrieve_radius_map()
        self._domain_map = self.build_or_retrieve_domain_map()

    def nodes_in_radius(self, socket_id: int) -> List[int]:
        return self._radius_map[socket_id]

    def nodes_in_domain(self, socket_id: int) -> List[int]:
        return self._domain_map[socket_id]

    def build_or_retrieve_radius_map(self) -> Dict[int, List[int]]:
        if pathlib.Path(RADIUS_MAP_DIR).exists():
            with open(RADIUS_MAP_DIR, 'r') as file:
                return json.load(file)
        else:
            socket_map = {socket_id: self.find_nodes_in_radius(socket_id) + RADIUS_INCLUDES_OVERRIDE.get(socket_id, [])
                          for socket_id in LD_CACHE.socket_id_list}
            with open(RADIUS_MAP_DIR, 'w') as file:
                json.dump(socket_map, file)

            return socket_map

    def find_nodes_in_radius(self, socket_id) -> List[int]:
        socket_coords = NODE_DB.get(socket_id).coords
        nodes_in_radius = [node.node_id for node in FULL_TREE_DRAWING.nodes.values()
                           if self.node_is_in_radius(socket_coords, node.coords)]
        return nodes_in_radius

    @staticmethod
    def node_is_in_radius(node1: Vertex, node2: Vertex):
        x_component = (node1.x - node2.x) ** 2
        y_component = (node1.y - node2.y) ** 2
        return math.sqrt(x_component + y_component) <= TIMELESS_JEWEL_RADIUS

    def build_or_retrieve_domain_map(self) -> Dict[int, List[int]]:
        if pathlib.Path(DOMAIN_MAP_DIR).exists():
            with open(DOMAIN_MAP_DIR, 'r') as file:
                return json.load(file)
        else:
            socket_map = {socket_id: self.find_nodes_in_domain(socket_id) + DOMAIN_INCLUDES_OVERRIDE.get(socket_id, [])
                          for socket_id in LD_CACHE.socket_id_list}
            with open(DOMAIN_MAP_DIR, 'w') as file:
                json.dump(socket_map, file)

            return socket_map

    def find_nodes_in_domain(self, socket_id) -> List[int]:
        # find the rect bounds
        # TODO - probably want to make an effort to make it more 'square' by adding some space
        bounds = DOMAIN_BOUNDS_GUIDE[socket_id]
        top = self.get_coords_for_ref(bounds.up).y
        left = self.get_coords_for_ref(bounds.left).x
        bottom = self.get_coords_for_ref(bounds.down).y
        right = self.get_coords_for_ref(bounds.right).x

        return [node.node_id for node in FULL_TREE_DRAWING.nodes.values() if
                 self.node_is_in_bounds(node.coords, top, bottom, left, right)]

    @staticmethod
    def get_coords_for_ref(ref: NodeRef) -> Vertex:
        if ref.type == 'name':
            return NODE_DB.get_by_name(ref.ref).coords
        else:
            return NODE_DB.get(ref.ref).coords

    @staticmethod
    def node_is_in_bounds(node: Vertex, top: float, bottom: float, left: float, right: float) -> bool:
        return top >= node.y >= bottom \
            and left <= node.x <= right