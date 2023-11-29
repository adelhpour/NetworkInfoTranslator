from .export_json_base import NetworkInfoExportToJsonBase
import json
from pathlib import Path as pathlib


class NetworkInfoExportToCytoscapeJs(NetworkInfoExportToJsonBase):
    def __init__(self):
        self.styles = []
        super().__init__()

    def reset(self):
        super().reset()
        self.styles.clear()

    def add_node(self, go, category = ""):
        node = self.initialize_entity(go)
        self.set_entity_metaid(node, go)
        style = self.initialize_node_style(go)
        selected_style = self.initialize_node_selected_style(go)
        self.set_entity_compartment(node, go)
        self.extract_node_features(go, node, style)
        self.set_entity_selected(node, False)
        self.nodes.append(node)
        self.styles.append(style)
        self.styles.append(selected_style)

    def add_edge(self, species_reference, reaction):
        edge = self.initialize_entity(species_reference)
        self.set_entity_metaid(edge, species_reference)
        style = self.initialize_edge_style(species_reference)
        selected_style = self.initialize_edge_selected_style(species_reference)
        self.set_edge_nodes(edge, species_reference, reaction)
        self.extract_edge_features(species_reference, style)
        self.set_entity_selected(edge, False)
        self.edges.append(edge)
        self.styles.append(style)
        self.styles.append(selected_style)

    @staticmethod
    def initialize_entity(go):
        return {'data': {'id': go['id'], 'referenceId': go['referenceId']}}

    @staticmethod
    def set_entity_metaid(entity, go):
        if 'metaId' in list(go.keys()):
            entity['data']['metaId'] = go['metaId']

    def set_entity_compartment(self, entity, go):
        if 'compartment' in list(go.keys()):
            for c in self.graph_info.compartments:
                if c['referenceId'] == go['compartment']:
                    entity['data']['parent'] = c['id']
                    break

    @staticmethod
    def set_entity_selected(entity, selected):
        entity['selected'] = selected

    @staticmethod
    def initialize_node_style(go):
        return {'selector': "node[id = '" + go['id'] + "']", 'css': {'content': 'data(name)'}}

    @staticmethod
    def initialize_edge_style(species_reference):
        return {'selector': "edge[id = '" + species_reference['id'] + "']",
                'css': {'content': "", 'curve-style': 'bezier'}}

    @staticmethod
    def initialize_node_selected_style(go):
        return {'selector': "node[id = '" + go['id'] + "']:selected",
                'css': {'background-color': '#4169e1'}}

    @staticmethod
    def initialize_edge_selected_style(go):
        return {'selector': "edge[id = '" + go['id'] + "']:selected",
                'css': {'line-color': '#4169e1',
                        'source-arrow-color': '#4169e1',
                        'target-arrow-color': '#4169e1'}}

    def set_edge_nodes(self, edge, species_reference, reaction):
        species = None
        for s in self.graph_info.species:
            if s['referenceId'] == species_reference['species']:
                species = s
                break
        if species and 'role' in list(species_reference.keys()):
            if species_reference['role'].lower() == "product" or species_reference['role'].lower() == "sideproduct"\
                    or species_reference['role'].lower() == "side product":
                edge['data']['source'] = reaction['id']
                edge['data']['target'] = species['id']
            else:
                edge['data']['source'] = species['id']
                edge['data']['target'] = reaction['id']

    def extract_node_features(self, go, node, style):
        if 'features' in list(go.keys()):
            if 'boundingBox' in list(go['features'].keys()):
                node['position'] = self.get_node_position(go)
                style['css'].update(self.get_node_dimensions(go))
            if 'graphicalShape' in list(go['features'].keys()):
                style['css'].update(self.set_shape_style(go))
        if 'texts' in list(go.keys()) and len(go['texts']):
            text = go['texts'][0]
            if 'features' in list(text.keys()):
                if 'plainText' in list(text['features'].keys()):
                    node['data']['name'] = text['features']['plainText']
                if 'graphicalText' in list(text['features'].keys()):
                    style['css'].update(self.set_node_text_style(text))

    def extract_edge_features(self, go, style):
        if 'features' in list(go.keys()):
            if 'graphicalCurve' in list(go['features'].keys()):
                style['css'].update(self.set_curve_style(go))

    @staticmethod
    def get_node_position(go):
        return {'x': go['features']['boundingBox']['x']
                     + 0.5 * go['features']['boundingBox']['width'],
                'y': go['features']['boundingBox']['y']
                     + 0.5 * go['features']['boundingBox']['height']}

    @staticmethod
    def get_node_dimensions(go):
        return {'width': go['features']['boundingBox']['width'],
                'height': go['features']['boundingBox']['height']}

    def set_shape_style(self, go):
        shape_style = {}
        if 'strokeColor' in list(go['features']['graphicalShape'].keys()):
            shape_style['border-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalShape']['strokeColor'])
        if 'strokeWidth' in list(go['features']['graphicalShape'].keys()):
            shape_style['border-width'] = go['features']['graphicalShape']['strokeWidth']
        if 'fillColor' in list(go['features']['graphicalShape'].keys()):
            shape_style['background-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalShape']['fillColor'])
        if 'geometricShapes' in list(go['features']['graphicalShape'].keys()):
            if 'strokeColor' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                shape_style['border-color'] = \
                    self.graph_info.find_color_value(go['features']['graphicalShape']
                                                     ['geometricShapes'][0]['strokeColor'])
            if 'strokeWidth' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                shape_style['border-width'] = \
                    go['features']['graphicalShape']['geometricShapes'][0]['strokeWidth']
            if 'fillColor' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                shape_style['background-color'] = \
                    self.graph_info.find_color_value(
                        go['features']['graphicalShape']['geometricShapes'][0]['fillColor'])
            if 'shape' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                if go['features']['graphicalShape']['geometricShapes'][0]['shape'].lower() == "rectangle":
                    shape_style['shape'] = 'roundrectangle'
                elif go['features']['graphicalShape']['geometricShapes'][0]['shape'].lower() == "ellipse":
                    shape_style['shape'] = 'ellipse'
        return shape_style

    def set_curve_style(self, go):
        curve_style = {}
        if 'strokeColor' in list(go['features']['graphicalCurve'].keys()):
            curve_style['line-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
            curve_style['source-arrow-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
            curve_style['target-arrow-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
        if 'strokeWidth' in list(go['features']['graphicalCurve'].keys()):
            curve_style['width'] = go['features']['graphicalCurve']['strokeWidth']
        if 'role' in list(go.keys()):
            curve_style['target-arrow-shape'] = self.set_edge_target_arrow_shape(go)
        return curve_style

    def set_node_text_style(self, text):
        text_style = {}
        if 'strokeColor' in list(text['features']['graphicalText'].keys()):
            text_style['color'] = \
                self.graph_info.find_color_value(text['features']['graphicalText']['strokeColor'])
        if 'fontFamily' in list(text['features']['graphicalText'].keys()):
            text_style['font-family'] = text['features']['graphicalText']['fontFamily']
        if 'fontWeight' in list(text['features']['graphicalText'].keys()):
            text_style['font-weight'] = text['features']['graphicalText']['fontWeight']
        if 'fontStyle' in list(text['features']['graphicalText'].keys()):
            text_style['font-style'] = text['features']['graphicalText']['fontStyle']
        if 'fontSize' in list(text['features']['graphicalText'].keys()) and \
                'boundingBox' in list(text['features'].keys()):
            text_style['font-size'] = text['features']['graphicalText']['fontSize']['abs'] +\
                                      text['features']['boundingBox']['width'] *\
                                      text['features']['graphicalText']['fontSize']['rel']
        if 'vTextAnchor' in list(text['features']['graphicalText'].keys()):
            if text['features']['graphicalText']['vTextAnchor'] == 'middle':
                text_style['text-valign'] = 'center'
            else:
                text_style['text-valign'] = text['features']['graphicalText']['vTextAnchor']
        if 'hTextAnchor' in list(text['features']['graphicalText'].keys()):
            if text['features']['graphicalText']['hTextAnchor'] == 'start':
                text_style['text-halign'] = 'left'
            elif text['features']['graphicalText']['hTextAnchor'] == 'middle':
                text_style['text-halign'] = 'center'
            elif text['features']['graphicalText']['hTextAnchor'] == 'end':
                text_style['text-halign'] = 'right'
        return text_style

    @staticmethod
    def set_edge_target_arrow_shape(go):
        if go['role'].lower() == "product":
            return "triangle"
        elif go['role'].lower() == "modifier":
            return "diamond"
        elif go['role'].lower() == "activator":
            return "circle"
        elif go['role'].lower() == "inhibitor":
            return "tee"
        return ""

    def export(self, file_name):
        graph_info = dict(data={'generated_by': "NetworkInfoTranslator", 'name': pathlib(file_name).stem,
                                'shared_name': pathlib(file_name).stem, 'selected': True})
        graph_info['elements'] = {'nodes': self.nodes, 'edges': self.edges}
        graph_info['style'] = self.styles
        with open(file_name.split('.')[0] + ".js", 'w', encoding='utf8') as js_file:
            js_file.write("graph_info = ")
            json.dump(graph_info, js_file, indent=1)
            js_file.write(";")
