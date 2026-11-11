from dataclasses import asdict
from app.scripts.classes import DrawingRoot, CurvedEdge, StraightEdge, Node
from app.scripts.drawing.nodes_in_radius import TIMELESS_JEWEL_RADIUS
from app.scripts.parse_data_files.classes import Node

# TODO - I think we need to truncate floats here as well

def convert_drawing_to_minified_json(drawing: DrawingRoot) -> dict:
    return {
        'jewel_type': drawing.jewel_type,
        'jewel_id': None,
        'jewel_stats': drawing.jewel_stats.as_list(),
        'api_idx': drawing.api_idx,
        'radius': TIMELESS_JEWEL_RADIUS,
        'nodes': {str(node.node_id): minimize_node(node) for node_id, node in drawing.nodes},
        'curved_edges': [minimize_curved_edge(edge) for edge in drawing.curved_edges or []],
        'straight_edges': [minimize_straight_edge(edge) for edge in drawing.straight_edges or []]
    }

def minimize_node(node: Node) -> dict:
    return {
        'n': node.name,
        't': [tag.value for tag in node.tags],
        'a': node.allocated,
        'c': {
            'x': node.relative_coordinates.x,
            'y': node.relative_coordinates.y
        },
        'l': asdict(node.tooltip)
    }

def minimize_straight_edge(edge: StraightEdge) -> dict:
    return {
        'a': edge.allocated,
        'c': [
            {
                'x': edge.ends[0].x,
                'y': edge.ends[0].y
            },
            {
                'x': edge.ends[1].x,
                'y': edge.ends[1].y
            }
        ]
    }

def minimize_curved_edge(edge: CurvedEdge) -> dict:
    return {
        'a': edge.allocated,
        'c': {
            'x': edge.relative_center.x,
            'y': edge.relative_center.y
        },
        'o': edge.rotation,
        'r': edge.radius,
        't': edge.angle
    }
