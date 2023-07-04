from exports.export_json_base import NetworkInfoExportToJsonBase
import json
from pathlib import Path as pathlib


class NetworkInfoExportToEscher(NetworkInfoExportToJsonBase):
    def __init__(self):
        super().__init__()

    def reset(self):
        super().reset()

    def add_node(self, go, category=""):
        pass

    def add_edge(self, species_reference, reaction):
        pass

    def export(self, file_name="file"):
        position_x = self.graph_info.extents['minX'] + 0.5 * (self.graph_info.extents['maxX'] - self.graph_info.extents['minX'])
        position_y = self.graph_info.extents['minY'] + 0.5 * (self.graph_info.extents['maxY'] - self.graph_info.extents['minY'])
        dimensions_width = self.graph_info.extents['maxY'] - self.graph_info.extents['minY']
        dimensions_height = self.graph_info.extents['maxY'] - self.graph_info.extents['minY']
        graph_info = [{'generated_by': "SBMLplot",
                      'name': pathlib(file_name).stem + "_graph",
                      'canvas': {'x': position_x, 'y': position_y, 'width': dimensions_width, 'height': dimensions_height},
                      'nodes': self.nodes,
                      'reactions': self.edges}]
        with open(file_name.split('.')[0] + ".json", 'w', encoding='utf8') as js_file:
            json.dump(graph_info, js_file, indent=1)
        return graph_info