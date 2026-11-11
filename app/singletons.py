
"""
There are several objects that maintain some global state or load data that we want cached.
This is a place for all files to refer to these objects.
"""
from app.scripts.drawing.nodes_in_radius import SocketToNodesMapper
from app.scripts.drawing.tree_drawing import TreeDrawing
from app.scripts.parse_data_files.nodes import TreeNodes
from app.util.lut_cache import LutData

NODE_DB = TreeNodes()
LD_CACHE = LutData()
FULL_TREE_DRAWING = TreeDrawing()
SOCKET_RADIUS_MAP = SocketToNodesMapper()