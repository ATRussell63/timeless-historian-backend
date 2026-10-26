import json
from app.app_config import get_data_path

class TreeData:

    def __init__(self):
        self._TREE_DATA = None

    @property
    def tree_data(self):
        if not self._TREE_DATA:
            with open(get_data_path() + 'data.json', 'r') as tree_file:
                self._TREE_DATA = json.load(tree_file)

        return self._TREE_DATA

TREE_JSON = TreeData()