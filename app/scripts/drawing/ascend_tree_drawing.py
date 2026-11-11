

"""
Specialized drawing method that's used for Reclaimed Malevolence.

Only draws ascendancy trees, and excludes Ascendant and Reliquarian.

TODO - I'll need to handle modal passives here, just for assassin.
"""

ZORATH_UNSUPPORTED_CLASSES = ['ASCENDANT', 'RELIQUARIAN']

CLASS_START_NODE_ALIASES = {
    "SHADOW": "SIX",
    "SCION": "SEVEN"
}


def make_zorath_drawing(self, jewel: ParsedJewel, allocated_hashes: List[int], base_class: str,
                        ascendancy_class: str, ff_ascend_node: Optional[str]) -> DrawingRoot:
    # if flesh & flame are active, find the node object
    if ff_ascend_node is not None:
        ascend_node = list(filter(lambda n: n['name'] == ff_ascend_node, self.tree_data['nodes']))[0]
        allocated_hashes.append(ascend_node['skill'])

    # make drawing of the ascendancy
    drawing = self.make_pre_transform_ascend_drawing()

    # mutate the node that got replaced by Zorath

    # do the tree crawl and get the nodeIds along the shortest path to class start

    pass

    def make_pre_transform_ascend_drawing(self, allocated_hashes: List[int], base_class: str, ascendancy_class: str) -> DrawingRoot:
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