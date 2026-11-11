from app.scripts.classes import DrawingRoot
from app.scripts.node_lookup import NodeLookup
from app.util.parse_jewel import ParsedJewel


def apply_timeless_jewel_effects(jewel: ParsedJewel, drawing: DrawingRoot) -> DrawingRoot:
    lookup = NodeLookup(jewel)

    for node_id in drawing.nodes.keys():
        lookup.apply_effects_for_node(node_id, drawing)

    # wrap up by totaling up the MF mod effects
    if jewel.jewel_type == 'Militant Faith':
        drawing.jewel_stats.add_stats_from_mf_mods(jewel.mf_mods)

    return drawing


def apply_abyss_domain_jewel_effects(jewel: ParsedJewel, drawing: DrawingRoot) -> DrawingRoot:
    lookup = NodeLookup(jewel)

def apply_zorath_effects(drawing: DrawingRoot) -> DrawingRoot:
    pass