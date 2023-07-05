from exports.export_base import NetworkInfoExportBase
import json
from pathlib import Path as pathlib


class NetworkInfoExportToEscher(NetworkInfoExportBase):
    def __init__(self):
        self.nodes = {}
        super().__init__()

    def reset(self):
        super().reset()
        self.nodes = {}

    def add_species(self, species):
        if 'id' in list(species.keys()) and 'referenceId' in list(species.keys()):
            self.add_node(species, "Species")

    def add_reaction(self, reaction):
        if 'id' in list(reaction.keys()) and 'referenceId' in list(reaction.keys()):
            self.add_node(reaction, "Reaction")

    def add_node(self, go, category=""):
        node_ = self.initialize_node(go)
        self.set_node_biggid(node_, go)
        self.set_node_type(node_, go, category)
        self.set_node_is_primary(node_, go)
        self.extract_node_features(go, node_)
        self.nodes.update(node_)

    @staticmethod
    def initialize_node(go):
        return {go['id']: {}}

    @staticmethod
    def set_node_biggid(node, go):
        if 'referenceId' in list(go.keys()):
            node[go['id']]['bigg_id'] = go['referenceId']

    @staticmethod
    def set_node_type(node, go, category):
        if category == "Species":
            node[go['id']]['type'] = "metabolite"
        elif category == "Reaction":
            node[go['id']]['type'] = "midmarker"

    @staticmethod
    def set_node_is_primary(node, go):
        node[go['id']]['node_is_primary'] = True

    def extract_node_features(self, go, node):
        if 'features' in list(go.keys()):
            if 'boundingBox' in list(go['features'].keys()):
                node[go['id']]['x'] = self.get_center_x(go['features']['boundingBox'])
                node[go['id']]['y'] = self.get_center_y(go['features']['boundingBox'])
            elif 'curve' in list(go['features'].keys()):
                print("has curve")

            if 'texts' in list(go.keys()):
                for text in go['texts']:
                    if 'features' in list(text.keys()):
                        if 'plainText' in list(text['features'].keys()):
                            node[go['id']]['name'] = text['features']['plainText']
                        if 'boundingBox' in list(text['features'].keys()):
                            node[go['id']]['label_x'] = self.get_center_x(text['features']['boundingBox'])
                            node[go['id']]['label_y'] = self.get_center_y(text['features']['boundingBox'])
    @staticmethod
    def get_center_x(bounding_box):
        return bounding_box['x'] + 0.5 * bounding_box['width']

    @staticmethod
    def get_center_y(bounding_box):
        return bounding_box['y'] + 0.5 * bounding_box['height']

    def export(self, file_name="file"):
        position_x = self.graph_info.extents['minX'] + 0.5 * (self.graph_info.extents['maxX'] - self.graph_info.extents['minX'])
        position_y = self.graph_info.extents['minY'] + 0.5 * (self.graph_info.extents['maxY'] - self.graph_info.extents['minY'])
        dimensions_width = self.graph_info.extents['maxY'] - self.graph_info.extents['minY']
        dimensions_height = self.graph_info.extents['maxY'] - self.graph_info.extents['minY']
        graph_info = [{'generated_by': "SBMLplot",
                      'name': pathlib(file_name).stem + "_graph",
                      'canvas': {'x': position_x, 'y': position_y, 'width': dimensions_width, 'height': dimensions_height},
                      'nodes': self.nodes,
                      'reactions': {}}]
        with open(file_name.split('.')[0] + ".json", 'w', encoding='utf8') as js_file:
            json.dump(graph_info, js_file, indent=1)
        return graph_info