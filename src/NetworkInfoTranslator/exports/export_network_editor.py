from exports.export_json_base import NetworkInfoExportToJsonBase
import json
import math
from pathlib import Path as pathlib


class NetworkInfoExportToNetworkEditor(NetworkInfoExportToJsonBase):
    def __init__(self):
        super().__init__()

    def reset(self):
        super().reset()

    def add_node(self, go, category = ""):
        node_ = self.initialize_entity(go)
        self.set_entity_metaid(node_, go)
        style_ = self.initialize_node_style(go, category)
        self.set_entity_compartment(node_, go)
        self.extract_node_features(go, node_, style_)
        node_['style'] = style_
        self.nodes.append(node_)

    def add_edge(self, species_reference, reaction):
        edge_ = self.initialize_entity(species_reference)
        self.set_entity_metaid(edge_, species_reference)
        style_ = self.initialize_edge_style(species_reference)
        self.set_edge_nodes(edge_, species_reference, reaction)
        self.extract_edge_features(species_reference, style_)
        edge_['style'] = style_
        self.edges.append(edge_)

    @staticmethod
    def initialize_entity(go):
        return {'id': go['id']}

    @staticmethod
    def set_entity_metaid(item, go):
        if 'metaId' in list(go.keys()):
            item['metaId'] = go['metaId']

    def set_entity_compartment(self, item, go):
        if 'compartment' in list(go.keys()):

            for c in self.graph_info.compartments:
                if c['referenceId'] == go['compartment']:
                    item['parent'] = c['id']
                    break

    @staticmethod
    def initialize_node_style(go, category):
        parent_category = ""
        if category == "Compartment":
            parent_category = "Compartment"
        return {'name': go['id'] + "_style", 'category': category,
                'parent-category': parent_category, 'shapes': []}

    @staticmethod
    def initialize_edge_style(species_reference):
        return {'name': species_reference['id'] + "_style", 'category': "SpeciesReference",
                'sub-category': species_reference['role'], 'shapes': []}

    def set_edge_nodes(self, edge, species_reference, reaction):
        species = {}
        for s in self.graph_info.species:
            if s['referenceId'] == species_reference['species']:
                species = s
                break
        if 'role' in list(species_reference.keys()):
            if species_reference['role'].lower() == "product" or species_reference['role'].lower() == "side product":
                edge['source'], edge['target'] = self.get_edge_nodes_features(reaction, species)
            else:
                edge['source'], edge['target'] = self.get_edge_nodes_features(species, reaction)

    def extract_node_features(self, go, node, style):
        if 'features' in list(go.keys()):
            if 'boundingBox' in list(go['features'].keys()):
                node['position'] = self.get_node_position(go)
                node['dimensions'] = self.get_node_dimensions(go)
            if 'graphicalShape' in list(go['features'].keys())\
                    and 'geometricShapes' in list(go['features']['graphicalShape'].keys()):
                style['shapes'] = self.get_shape_style(go, offset_x=-0.5 * go['features']['boundingBox']['width'],
                                     offset_y=-0.5 * go['features']['boundingBox']['height'])
            if 'texts' in list(go.keys()):
                for text in go['texts']:
                    if 'features' in list(text.keys()):
                        style['shapes'].append(self.get_node_text(text, go['features']['boundingBox']))

    def extract_edge_features(self, go, style):
        if 'features' in list(go.keys()) and 'graphicalCurve' in list(go['features'].keys()):
            style['shapes'].append(self.get_curve_style(go))
            if 'heads' in list(go['features']['graphicalCurve'].keys()) \
                    and 'end' in list(go['features']['graphicalCurve']['heads'].keys()):
                style['arrow-head'] =\
                    self.get_arrow_heads(go['features']['graphicalCurve']['heads'], style['name'])

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

    def get_edge_nodes_features(self, source_go, target_go):
        source_node_features = {'node': source_go['id']}
        target_node_features = {'node': target_go['id']}
        source_node_position = self.get_node_position(source_go)
        source_node_dimensions = self.get_node_dimensions(source_go)
        target_node_position = self.get_node_position(target_go)
        target_node_dimensions = self.get_node_dimensions(target_go)
        source_node_radius = 0.5 * max(source_node_dimensions['width'], source_node_dimensions['height'])
        target_node_radius = 0.5 * max(target_node_dimensions['width'], target_node_dimensions['height'])
        slope = math.atan2(target_node_position['y'] - source_node_position['y'],
                           target_node_position['x'] - source_node_position['x'])
        source_node_features['position'] = {'x': source_node_position['x'] + source_node_radius * math.cos(slope),
                                           'y': source_node_position['y'] + source_node_radius * math.sin(slope)}
        target_node_features['position'] = {'x': target_node_position['x'] - target_node_radius * math.cos(slope),
                                         'y': target_node_position['y'] + target_node_radius * math.sin(slope)}

        return source_node_features, target_node_features

    def get_shape_style(self, go, offset_x=0.0, offset_y=0.0):
        geometric_shapes = []
        for gs in go['features']['graphicalShape']['geometricShapes']:
            geometric_shape = {}
            if 'strokeColor' in list(go['features']['graphicalShape'].keys()):
                default_stroke = \
                    self.graph_info.find_color_value(go['features']['graphicalShape']['strokeColor'])
                if default_stroke:
                    geometric_shape['stroke'] = default_stroke
            if 'strokeWidth' in list(go['features']['graphicalShape'].keys()):
                geometric_shape['stroke-width'] = go['features']['graphicalShape']['strokeWidth']
            if 'fillColor' in list(go['features']['graphicalShape'].keys()):
                default_fill = \
                    self.graph_info.find_color_value(go['features']['graphicalShape']['fillColor'])
                if default_fill:
                    geometric_shape['fill'] = default_fill
            geometric_shape.update(
                self.get_geometric_shape_features(gs, self.get_node_dimensions(go), offset_x, offset_y))
            if 'shape' in list(geometric_shape.keys()):
                geometric_shapes.append(geometric_shape)
        return geometric_shapes

    def get_curve_style(self, go):
        geometric_shape = {}
        if 'strokeColor' in list(go['features']['graphicalCurve'].keys()):
            default_stroke = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
            if default_stroke:
                geometric_shape['stroke'] = default_stroke
        if 'strokeWidth' in list(go['features']['graphicalCurve'].keys()):
            geometric_shape['stroke-width'] = go['features']['graphicalCurve']['strokeWidth']
        geometric_shape.update(self.get_curve_style_features(go['features']['graphicalCurve']))
        if len(go['features']['curve']):
            geometric_shape.update(self.get_curve_features(go['features']['curve']))
        return geometric_shape

    def get_geometric_shape_features(self, gs, dimensions, offset_x, offset_y):
        geometric_shape = {}
        if 'strokeColor' in list(gs.keys()):
            geometric_shape['stroke'] = self.graph_info.find_color_value(gs['strokeColor'])
        if 'strokeWidth' in list(gs.keys()):
            geometric_shape['stroke-width'] = gs['strokeWidth']
        if 'fillColor' in list(gs.keys()):
            geometric_shape['fill'] = self.graph_info.find_color_value(gs['fillColor'])
        if 'shape' in list(gs.keys()):
            if gs['shape'].lower() == "rectangle":
                geometric_shape.update(
                    self.get_rectangle_features(gs, dimensions, offset_x, offset_y))
            elif gs['shape'].lower() == "ellipse":
                geometric_shape.update(
                    self.get_ellipse_features(gs, dimensions, offset_x, offset_y))
            elif gs['shape'].lower() == "polygon":
                geometric_shape.update(
                    self.get_polygon_features(gs, dimensions, offset_x, offset_y))
        return geometric_shape

    def get_curve_style_features(self, gc):
        geometric_shape = {}
        if 'strokeColor' in list(gc.keys()):
            geometric_shape['stroke'] = self.graph_info.find_color_value(gc['strokeColor'])
        if 'strokeWidth' in list(gc.keys()):
            geometric_shape['stroke-width'] = gc['strokeWidth']
        if 'fillColor' in list(gc.keys()):
            geometric_shape['fill'] = self.graph_info.find_color_value(gc['fillColor'])
        return geometric_shape

    @staticmethod
    def get_curve_features(curve):
        curve_shape = {}
        element = curve[0]
        if all(k in element.keys() for k in ('startX', 'startY', 'endX', 'endY',
                                             'basePoint1X', 'basePoint1Y', 'basePoint2X', 'basePoint2Y')):
            curve_shape['shape'] = "bezier"
            curve_shape['p1'] = {'x': 0, 'y': 0}
            if abs(element['endX'] - element['startX']) > 0:
                curve_shape['p1']['x'] = \
                    round((element['basePoint1X'] - element['startX']) / (
                            0.01 * (element['endX'] - element['startX'])))
            if abs(element['endY'] - element['startY']) > 0:
                curve_shape['p1']['y'] = \
                    round((element['basePoint1Y'] - element['startY']) / (
                            0.01 * (element['endY'] - element['startY'])))
            curve_shape['p2'] = {'x': 0, 'y': 0}
            if abs(element['endX'] - element['startX']) > 0:
                curve_shape['p2']['x'] = \
                    round(
                        (element['basePoint2X'] - element['endX']) / (0.01 * (element['endX'] - element['startX'])))
            if abs(element['endY'] - element['startY']) > 0:
                curve_shape['p2']['y'] = \
                    round(
                        (element['basePoint2Y'] - element['endY']) / (0.01 * (element['endY'] - element['startY'])))
        else:
            curve_shape['shape'] = "line"
        return curve_shape

    @staticmethod
    def get_ellipse_features(gs, dimensions, offset_x, offset_y):
        ellipse_shape = {'shape': "ellipse"}
        if 'cx' in list(gs.keys()):
            ellipse_shape['cx'] = gs['cx']['abs'] + 0.01 * gs['cx'][
                'rel'] * dimensions['width'] + offset_x
        if 'cy' in list(gs.keys()):
            ellipse_shape['cy'] = gs['cy']['abs'] + 0.01 * gs['cy'][
                'rel'] * dimensions['height'] + offset_y
        if 'rx' in list(gs.keys()):
            ellipse_shape['rx'] = gs['rx']['abs'] + 0.01 * gs['rx'][
                'rel'] * dimensions['width']
        if 'ry' in list(gs.keys()):
            ellipse_shape['ry'] = gs['ry']['abs'] + \
                                  0.01 * gs['ry']['rel'] * dimensions['height']
        if 'ratio' in list(gs.keys()) and gs['ratio'] > 0.0:
            if (dimensions['width'] / dimensions['height']) <= gs['ratio']:
                ellipse_shape['rx'] = 0.5 * dimensions['width']
                ellipse_shape['ry'] = (0.5 * dimensions['width'] / gs['ratio'])
            else:
                ellipse_shape['ry'] = 0.5 * dimensions['height']
                ellipse_shape['rx'] = gs['ratio'] * 0.5 * dimensions['height']
        return ellipse_shape

    @staticmethod
    def get_rectangle_features(gs, dimensions, offset_x, offset_y):
        rectangle_shape = {'shape': "rect"}
        if 'x' in list(gs.keys()):
            rectangle_shape['x'] = gs['x']['abs'] + \
                                   0.01 * gs['x']['rel'] * dimensions['width'] + offset_x
        if 'y' in list(gs.keys()):
            rectangle_shape['y'] = gs['y']['abs'] + \
                                   0.01 * gs['y']['rel'] * dimensions['height'] + offset_y
        if 'width' in list(gs.keys()):
            rectangle_shape['width'] = gs['width']['abs'] + \
                                       0.01 * gs['width']['rel'] * dimensions['width']
        if 'height' in list(gs.keys()):
            rectangle_shape['height'] = gs['height']['abs'] + \
                                        0.01 * gs['height']['rel'] * dimensions['height']
        if 'ratio' in list(gs.keys()) and gs['ratio'] > 0.0:
            if (dimensions['width'] / dimensions['height']) <= gs['ratio']:
                rectangle_shape['width'] = dimensions['width']
                rectangle_shape['height'] = dimensions['height'] / gs['ratio']
                rectangle_shape['y'] += 0.5 * (dimensions['height'] - rectangle_shape['height'])
            else:
                rectangle_shape['height'] = dimensions['height']
                rectangle_shape['width'] = gs['ratio'] * dimensions['height']
                rectangle_shape['x'] += 0.5 * (dimensions['width'] - rectangle_shape['width'])
        if 'rx' in list(gs.keys()):
            rectangle_shape['rx'] = gs['rx']['abs'] + \
                                    0.01 * gs['rx']['rel'] * 0.5 * dimensions['width']
        if 'ry' in list(gs.keys()):
            rectangle_shape['ry'] = gs['ry']['abs'] + \
                                    0.01 * gs['ry']['rel'] * 0.5 * dimensions['height']
            return rectangle_shape

    @staticmethod
    def get_polygon_features(gs, dimensions, offset_x, offset_y):
        polygon_shape = {'shape': "polygon"}
        if 'vertices' in list(gs.keys()):
            points = []
            for v_index in range(len(gs['vertices'])):
                points.append({'x': gs['vertices'][v_index]['renderPointX']['abs'] + 0.01 *
                                    gs['vertices'][v_index]['renderPointX']['rel'] * dimensions['width'] + offset_x,
                               'y': gs['vertices'][v_index]['renderPointY']['abs'] + 0.01 *
                                    gs['vertices'][v_index]['renderPointY']['rel'] * dimensions['height'] + offset_y})
        polygon_shape['points'] = points
        return polygon_shape

    def get_node_text(self, text, go_bounding_box):
        text_shape = {'shape': "text"}
        if 'plainText' in list(text['features'].keys()):
            text_shape['plain-text'] = text['features']['plainText']
        if 'graphicalText' in list(text['features'].keys()):
            text_shape.update(self.get_text_features(text, go_bounding_box))
        return text_shape

    def get_text_features(self, text, go_bounding_box):
        features = {}
        if 'strokeColor' in list(text['features']['graphicalText'].keys()):
            features['color'] = \
                self.graph_info.find_color_value(text['features']['graphicalText']['strokeColor'])
        if 'fontFamily' in list(text['features']['graphicalText'].keys()):
            features['font-family'] = text['features']['graphicalText']['fontFamily']
        if 'fontWeight' in list(text['features']['graphicalText'].keys()):
            features['font-weight'] = text['features']['graphicalText']['fontWeight']
        if 'fontStyle' in list(text['features']['graphicalText'].keys()):
            features['font-style'] = text['features']['graphicalText']['fontStyle']
        if 'hTextAnchor' in list(text['features']['graphicalText'].keys()):
            features['text-anchor'] = text['features']['graphicalText']['hTextAnchor']
        if 'vTextAnchor' in list(text['features']['graphicalText'].keys()):
            features['vtext-anchor'] = text['features']['graphicalText']['vTextAnchor']
        if 'boundingBox' in list(text['features'].keys()):
            features['x'] = text['features']['boundingBox']['x'] -\
                            (go_bounding_box['x'] + 0.5 * go_bounding_box['width'])
            features['y'] = text['features']['boundingBox']['y'] -\
                            (go_bounding_box['y'] + 0.5 * go_bounding_box['height'])
            features['width'] = text['features']['boundingBox']['width']
            features['height'] = text['features']['boundingBox']['height']
            if 'fontSize' in list(text['features']['graphicalText'].keys()):
                features['font-size'] = text['features']['graphicalText']['fontSize']['abs'] +\
                                        text['features']['boundingBox']['width'] * \
                                        text['features']['graphicalText']['fontSize']['rel']
        return features

    def get_arrow_heads(self, heads, style_name):
        line_ending_style = {'name': style_name + "_ArrowHead", 'category': "LineEnding", 'shapes': []}
        line_ending = self.graph_info.find_line_ending(heads['end'])
        if line_ending and 'graphicalShape' in list(line_ending['features'].keys())\
            and 'geometricShapes' in list(line_ending['features']['graphicalShape'].keys()):
            line_ending_style['shapes'] =\
                self.get_shape_style(line_ending,
                                     offset_x=line_ending['features']['boundingBox']['x'],
                                     offset_y=line_ending['features']['boundingBox']['y'])
        return line_ending_style

    def export(self, file_name="file"):
        position = {'x': self.graph_info.extents['minX'] + 0.5 * (self.graph_info.extents['maxX'] - self.graph_info.extents['minX']),
                    'y': self.graph_info.extents['minY'] + 0.5 * (self.graph_info.extents['maxY'] - self.graph_info.extents['minY'])}
        dimensions = {'width': self.graph_info.extents['maxX'] - self.graph_info.extents['minX'],
                      'height': self.graph_info.extents['maxY'] - self.graph_info.extents['minY']}
        graph_info = {'generated_by': "NetworkInfoTranslator",
                      'name': pathlib(file_name).stem + "_graph",
                      'position': position,
                      'dimensions': dimensions,
                      'nodes': self.nodes,
                      'edges': self.edges}
        with open(file_name.split('.')[0] + ".json", 'w', encoding='utf8') as js_file:
            json.dump(graph_info, js_file, indent=1)
        return graph_info
