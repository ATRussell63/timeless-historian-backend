import dataclasses
import dacite
import json
import math
import logging
import pathlib
from dataclasses import dataclass
from typing import List, Dict, Tuple

from app.app_config import get_data_path
from app.scripts.classes import StraightEdge, CurvedEdge, Vertex
from app.scripts.parse_data_files.classes import Node
from app.scripts.parse_data_files.constants import TreeConstants
from app.util.utils import intersection_has_any

from app.singletons import NODE_DB

"""
Makes a full 'drawing' of the passive skill tree.

Fairly similar to GGG's method of organization except that we can keep everything
in a pared-down format that's easier for us to use.

1. Nodes are indexed by their node_id. This gives us O(1) to select a node, which is important since we're going to be
doing additive construction of the passive tree cutouts.

2. Edges are indexed by the endpoints. They're bi-directional so we'll use set(node_id, node_id) as the keys.

"""

RELEVANT_NODE_TYPES = ['keystone', 'notable', 'small_passive', 'jewel_socket']

logger = logging.getLogger('main')

NODES_FILE_NAME = 'tree_nodes.json'
EDGES_FILE_NAME = 'tree_edges.json'

@dataclass
class TreeDrawing:
    nodes: Dict[int, Node]
    edges: Dict[frozenset[int], StraightEdge | CurvedEdge]

    def __init__(self):
        if not pathlib.Path(get_data_path() + NODES_FILE_NAME).exists() \
                or not pathlib.Path(get_data_path() + EDGES_FILE_NAME).exists():
            self.nodes, self.edges = TreeDrawingBuilder().build()

        else:
            try:
                self.import_nodes()
            except Exception as e:
                logger.error(f'Failed to load tree data file: {e}')

    def import_nodes(self):
        with open(get_data_path() + NODES_FILE_NAME, 'r') as file:
            nodes_dict = json.load(file)
            self.nodes = {key: dacite.from_dict(Node, value) for key, value in nodes_dict.items()}

    def import_edges(self):
        with open(get_data_path() + EDGES_FILE_NAME, 'r') as file:
            edges_dict = json.load(file)
            self.edges = {key: dacite.from_dict(StraightEdge, value) if 'ends' in value.keys() else dacite.from_dict(CurvedEdge, value)
                          for key, value in edges_dict.items()}

    def get_nodes_by_node_id(self, node_ids: List[int]) -> Dict[int, Node]:
        return {key: value for key, value in self.nodes.items() if key in node_ids}

    def get_edges_by_node_id(self, node_ids: List[int]) -> Dict[frozenset[int], StraightEdge | CurvedEdge]:
        return {key: value for key, value in self.edges.items() if intersection_has_any(list(key), node_ids)}

class TreeDrawingBuilder:
    """
    Encompasses everything required to generate a json definition of how to draw the nodes and edges
    of a particular jewel socket for a particular character.
    """

    def __init__(self):
        self._node_db = NODE_DB
        self._constants = TreeConstants()

    def build(self) -> Tuple[Dict[int, Node], Dict[frozenset[int], StraightEdge | CurvedEdge]]:

        nodes = self._node_db.get_all_by_tags(RELEVANT_NODE_TYPES)
        edges = {}

        for node in nodes.values():
            for connected_node_id in node.all_connected():
                edges[frozenset([node.node_id, connected_node_id])] = self.make_edge(node, self._node_db.get(connected_node_id))

        self.save_nodes_to_file(nodes)
        self.save_edges_to_file(edges)

        return nodes, edges

    def make_edge(self, node1: Node, node2: Node) -> StraightEdge | CurvedEdge:
        if node1.anchor.id == node2.anchor.id and node1.anchor.radius == node2.anchor.radius:
            return self.make_curved_edge(node1, node2,)
        else:
            return self.make_straight_edge(node1, node2)

    @staticmethod
    def save_nodes_to_file(nodes: Dict[int, Node]):
        with open(get_data_path() + NODES_FILE_NAME, 'w') as file:
            nodes_dict = {key: dataclasses.asdict(value) for key, value in nodes.items()}
            json.dump(nodes_dict, file)

    @staticmethod
    def save_edges_to_file(edges: Dict[frozenset[int], StraightEdge | CurvedEdge]):
        with open(get_data_path() + NODES_FILE_NAME, 'w') as file:
            edges_dict = {key: dataclasses.asdict(value) for key, value in edges.items()}
            json.dump(edges_dict, file)

    def make_curved_edge(self, start_node: Node, end_node: Node):
        edge = CurvedEdge(
            allocated=(start_node.allocated or False) and (end_node.allocated or False),
            # we'll update these coords later when we pick a drawing center
            relative_center=Vertex(start_node.anchor.global_x, start_node.anchor.global_y),
            rotation=self.calc_arc_rotation(start_node.anchor.angle,
                                            end_node.anchor.angle),
            radius=start_node.anchor.radius,
            angle=self.calc_arc_length(start_node.anchor.angle, end_node.anchor.angle),
        )
        return edge

    @staticmethod
    def calc_arc_length(angle1: float, angle2: float) -> float:
        return max(angle1, angle2) - min(angle1, angle2)

    @staticmethod
    def calc_arc_rotation(angle1: float, angle2: float):
        """
        Konva starts drawing its arcs at the 12-o-clock position and wants to know
        how much to rotate the arc clockwise.

        We can't just use the minimum angle because that will result in the incorrect
        value if the arc is being drawn between 11 and 1 o-clock.
        Instead we assume that the arc length will never exceed 180 degrees and order
        the two clock positions based on that assumption.
        """

        arc_length = angle2 - angle1
        if arc_length > math.radians(180):
            return angle2
        else:
            return angle1

    @staticmethod
    def make_straight_edge(start_node: Node, end_node: Node) -> StraightEdge:
        return StraightEdge(
            allocated=(start_node.allocated or False) and (end_node.allocated or False),
            ends=[start_node.absolute_coordinates, end_node.absolute_coordinates]
        )
