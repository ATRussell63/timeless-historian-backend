import logging
from typing import List, Tuple, Optional
from collections import defaultdict, deque
from math import isclose
from itertools import chain

from app.scripts.classes import DrawingRoot, Vertex, CurvedEdge, StraightEdge, Node, Dict
from app.scripts.drawing.nodes_in_radius import TIMELESS_JEWEL_RADIUS
from app.scripts.parse_data_files.jewel_stats import JewelStats
from app.util.parse_jewel import ParsedJewel
from app.util.utils import intersection_has_any

from app.singletons import NODE_DB, FULL_TREE_DRAWING, SOCKET_RADIUS_MAP, LD_CACHE

"""
Build a 'cutout' drawing by selecting the nodes and edges we want.

By default we'll use the same construction we've been using, but the abyss domain jewels can be off-center
and rectangular instead of radial.

We can also hardcode some nodes that have been bugbears in the past when using a strictly radius-based search.
"""

logger = logging.getLogger('main')

def make_timeless_cutout_for_socket(jewel: ParsedJewel, allocated_hashes: List[int], anointed_node_names: List[str]) -> DrawingRoot:
    if jewel.socket_index is None:
        logger.error("ParsedJewel has no socket. How'd that happen?")
        raise Exception(f"ParsedJewel has no socket_id: {jewel}")

    # find the actual node_id of the socket
    socket_node_id = LD_CACHE.socket_to_node_map[jewel.socket_index]['node_id']

    # find the node_ids of any anointed nodes
    anointed_node_ids = [NODE_DB.get_by_name(node_name) for node_name in anointed_node_names]
    allocated_hashes = list(set(allocated_hashes + anointed_node_ids))

    # find all nodes in radius of the socket
    node_ids_in_radius = SOCKET_RADIUS_MAP.nodes_in_radius(socket_node_id)
    nodes = FULL_TREE_DRAWING.get_nodes_by_node_id(node_ids_in_radius)

    # get all edges connected to at least one node
    edges = FULL_TREE_DRAWING.get_edges_by_node_id(node_ids_in_radius)

    # 'allocate' all nodes and edges
    curved_edges, straight_edges = allocate_edges(edges, allocated_hashes)
    nodes = allocate_nodes(nodes, allocated_hashes)

    # coalesce edges where possible
    curved_edges = coalesce_curved_edges(curved_edges)
    straight_edges = coalesce_straight_edges(straight_edges)

    # translate all coordinates based on the center
    center = NODE_DB.get(jewel.socket_index).coords
    nodes = translate_nodes(nodes, center)
    curved_edges = translate_curved_edges(curved_edges, center)
    straight_edges = translate_straight_edges(straight_edges, center)

    # finally create the DrawingRoot
    return DrawingRoot(jewel_type=jewel.jewel_type,
                       jewel_id=socket_node_id,
                       api_idx=jewel.socket_index,
                       radius=TIMELESS_JEWEL_RADIUS,
                       nodes=nodes,
                       curved_edges=curved_edges,
                       straight_edges=straight_edges,
                       jewel_stats=JewelStats())

def make_abyss_cutout():
    # TODO - :)
    pass

def allocate_nodes(nodes: Dict[int, Node], allocated_hashes: List[int]) -> Dict[int, Node]:
    for node in nodes.values():
        node.allocated = node.node_id in allocated_hashes

    return nodes

def allocate_edges(edge_map: Dict[frozenset[int], CurvedEdge | StraightEdge], allocated_hashes: List[int]) \
        -> Tuple[List[CurvedEdge], List[StraightEdge]]:
    for key, val in edge_map.items():
        # if one of the endpoints is allocated, so is the edge
        val.allocated = intersection_has_any(list(key), allocated_hashes)

    curved_edges = [edge for edge in edge_map.values() if type(edge) is CurvedEdge]
    straight_edges = [edge for edge in edge_map.values() if type(edge) is StraightEdge]
    return curved_edges, straight_edges

def translate_nodes(nodes: Dict[int, Node], center: Vertex) -> Dict[int, Node]:
    for node in nodes.values():
        node.relative_coordinates = node.coords - center

    return nodes

def translate_straight_edges(edges: List[StraightEdge], center: Vertex) -> List[StraightEdge]:
    for edge in edges:
        edge.ends = [coordinate - center for coordinate in edge.ends]

    return edges

def translate_curved_edges(edges: List[CurvedEdge], center: Vertex) -> List[CurvedEdge]:
    for edge in edges:
        edge.relative_center = edge.relative_center - center

    return edges

def coalesce_straight_edges(straight_edges: List[StraightEdge]) -> List[StraightEdge]:
    """
    Adjacent edges can situationally be merged into one.

    Straight edges with at least 1 common endpoint, the same slope and same allocated status can be merged.
    """

    # group edges by like slopes - they agree on which direction is positive
    edges_by_slope = defaultdict(list)
    for edge in straight_edges:
        for slope in edges_by_slope.keys():
            if isclose(edge.slope(), slope):
                edges_by_slope[slope].append(edge)
                break

    # sort them by y-ascending order - we don't have the node_ids anymore but the verts are an okay proxy
    edges_by_slope = {key: sorted(value, key=lambda e: e.ends[0].y) for key, value in edges_by_slope.items()}

    def coalesce_segments(edges: List[StraightEdge]) -> List[StraightEdge]:

        def same_vertex(a: Vertex, b: Vertex):
            return isclose(a.x, b.x) and isclose(a.y, b.y)

        remaining = list(edges)
        result = []

        while remaining:
            edge = remaining.pop(0)

            start, end = edge.ends
            allocated = edge.allocated

            merged = True

            while merged:
                merged = False

                for i, candidate in enumerate(remaining):

                    if candidate.allocated != allocated:
                        continue

                    a, b = candidate.ends

                    # Attach to the end of the current segment.
                    if same_vertex(end, a):
                        end = b
                    elif same_vertex(end, b):
                        end = a

                    # Attach to the start of the current segment.
                    elif same_vertex(start, b):
                        start = a
                    elif same_vertex(start, a):
                        start = b
                    else:
                        continue

                    remaining.pop(i)
                    merged = True
                    break

            result.append(StraightEdge(ends=[start, end], allocated=allocated))

        return result

    return chain.from_iterable([coalesce_segments(edge_list) for edge_list in edges_by_slope.values()])

def coalesce_curved_edges(curved_edges: List[CurvedEdge]) -> List[CurvedEdge]:
    """
    Curved edges can be merged similar to straight edges, but instead of grouping by slopes,
    we can compare the center of the arc (the Anchor center).
    """

    def key(e: CurvedEdge) -> Tuple[bool, Vertex]:
        return e.allocated, e.relative_center

    # Group by (allocated, relative_center)
    groups = defaultdict(list)
    for edge in curved_edges:
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