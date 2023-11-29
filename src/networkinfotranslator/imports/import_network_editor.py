from .import_base import NetworkInfoImportBase
import json
import math
import webcolors


class NetworkInfoImportFromNetworkEditor(NetworkInfoImportBase):
    def __init__(self):
        super().__init__()

    def extract_info(self, graph):
        super().extract_info(graph)

        f =  open(graph)
        self.graph_info = json.load(f)
        self.extract_extents(self.graph_info)
        self.extract_background_color(self.graph_info)
        self.extract_entities(self.graph_info)

    def extract_extents(self, graph_info):
        if 'position' in list(graph_info.keys()):
            if 'x' in list(graph_info['position'].keys()):
                self.extents['minX'] = graph_info['position']['x']
            if 'y' in list(graph_info['position'].keys()):
                self.extents['minY'] = graph_info['position']['y']
        if 'dimensions' in list(graph_info.keys()):
            if 'width' in list(graph_info['dimensions'].keys()):
                self.extents['minX'] -= 0.5 * graph_info['dimensions']['width']
                self.extents['maxX'] = self.extents['minX'] + graph_info['dimensions']['width']
            if 'height' in list(graph_info['dimensions'].keys()):
                self.extents['minY'] -= 0.5 * graph_info['dimensions']['height']
                self.extents['maxY'] = self.extents['minY'] + graph_info['dimensions']['height']

    def extract_background_color(self, graph_info):
        if 'background-color' in list(graph_info.keys()):
            self.background_color = graph_info['background-color']

    def extract_entities(self, graph_info):
        if 'nodes' in list(graph_info.keys()):
            for node in graph_info['nodes']:
                if 'style' in list(node.keys()) and 'category' in list(node['style'].keys()):
                    if node['style']['category'].lower() == "compartment":
                        self.add_compartment(node)
                    elif node['style']['category'].lower() == "species":
                        self.add_species(node)
                    elif node['style']['category'].lower() == "reaction":
                        self.add_reaction(node, graph_info)

    def add_compartment(self, compartment_info):
        compartment_ = {}
        if 'id' in list(compartment_info.keys()):
            compartment_['info'] = compartment_info
            compartment_['id'] = compartment_info['id'] + "_glyph"
            compartment_['referenceId'] = compartment_info['id']
            self.compartments.append(compartment_)

    def add_species(self, species_info):
        species_ = {}
        if 'id' in list(species_info.keys()):
            species_['info'] = species_info
            species_['id'] = species_info['id'] + "_glyph"
            species_['referenceId'] = species_info['id']
            self.species.append(species_)

    def add_reaction(self, reaction_info, graph_info):
        reaction_ = {}
        if 'id' in list(reaction_info.keys()):
            reaction_['info'] = reaction_info
            reaction_['id'] = reaction_info['id'] + "_glyph"
            reaction_['referenceId'] = reaction_info['id']

            reaction_['speciesReferences'] = []
            if 'edges' in list(graph_info.keys()):
                for edge in graph_info['edges']:
                    if ('source' in list(edge.keys()) and
                        'node' in list(edge['source'].keys()) and
                        edge['source']['node'] == reaction_['referenceId']) or \
                            ('target' in list(edge.keys()) and
                             'node' in list(edge['target'].keys()) and
                             edge['target']['node'] == reaction_['referenceId']):
                        self.add_species_reference(reaction_['speciesReferences'], edge)
            self.reactions.append(reaction_)

    @staticmethod
    def add_species_reference(species_references, species_reference_info):
        species_reference_ = {}
        if 'id' in list(species_reference_info.keys()):
            species_reference_['info'] = species_reference_info
            species_reference_['id'] = species_reference_info['id'] + "_glyph"
            species_reference_['referenceId'] = species_reference_info['id']
            species_references.append(species_reference_)

    @staticmethod
    def add_text(node, text_shape):
        if "plain-text" in list(text_shape.keys()):
            node['texts'].append({'id': node['id'] + "_" + text_shape['plain-text'] + "_text",
                            'plain-text': text_shape['plain-text'], 'info': text_shape})

    def add_color(self, color):
        if not self.find_color(color):
            self.colors.append({'id': color})

    def add_line_ending(self, line_ending):
        if 'name' in list(line_ending.keys()) and not self.find_line_ending(line_ending['name']) and \
                'shapes' in list(line_ending.keys()) and len(line_ending['shapes']):
            self.line_endings.append({'id': line_ending['name'], 'info': line_ending})

    def extract_compartment_features(self, compartment):
        self.extract_node_features(compartment)

    def extract_species_features(self, species):
        if 'parent' in list(species['info'].keys()):
            species['compartment'] = species['info']['parent']
        self.extract_node_features(species)

    def extract_reaction_features(self, reaction):
        if 'parent' in list(reaction['info'].keys()):
            reaction['compartment'] = reaction['info']['parent']
        if self.is_centroid_node(reaction):
            self.extract_centroid_node_features(reaction)
        else:
            self.extract_node_features(reaction)

    def extract_species_reference_features(self, species_reference):
        if 'style' in list(species_reference['info'].keys()) and\
                'sub-category' in list(species_reference['info']['style'].keys()):
            species_reference['role'] = species_reference['info']['style']['sub-category']
        self.extract_edge_features(species_reference)

    def extract_color_features(self, color):
        if color['id']:
            if color['id'].startswith("#"):
                color['features'] = {}
                color['features']['value'] = color['id']
                color['id'] = self.find_color_unique_id()
            elif 'features' not in list(color.keys()) or 'value' not in list(color['features'].keys()):
                color['features'] = {}
                try:
                    color['features']['value'] = webcolors.name_to_hex(color['id'])
                except:
                    color['features']['value'] = webcolors.name_to_hex("white")

    def extract_line_ending_features(self, line_ending):
        line_ending['features'] = {}

        # get bounding box features
        line_ending['features']['boundingBox'] = self.get_bounding_box_features(line_ending['info'])
        offset_x = line_ending['features']['boundingBox']['width']
        offset_y = 0.5 * line_ending['features']['boundingBox']['height']

        # get features
        if 'shapes' in list(line_ending['info'].keys()):
            line_ending['features']['graphicalShape'] = \
                self.extract_graphical_shape_features(line_ending['info']['shapes'], offset_x, offset_y)

        line_ending['features']['enableRotation'] = True

    def extract_node_features(self, node):
        node['features'] = {}
        node['texts'] = []
        # get bounding box features
        node['features']['boundingBox'] = self.get_bounding_box_features(node['info'])
        offset_x = 0.5 * node['features']['boundingBox']['width']
        offset_y = 0.5 * node['features']['boundingBox']['height']

        # get style features
        if 'style' in list(node['info'].keys()):
            if 'name' in list(node['info']['style']):
                node['features']['styleName'] = node['info']['style']['name']
            if 'shapes' in list(node['info']['style']):
                node['features']['graphicalShape'] = \
                    self.extract_graphical_shape_features(node['info']['style']['shapes'], offset_x, offset_y)
                for shape in node['info']['style']['shapes']:
                    if 'shape' in list(shape.keys()) and shape['shape'].lower() == "text":
                        self.add_text(node, shape)

        # get text features
        if 'texts' in list(node.keys()):
            self.extract_text_features(node)

    def extract_centroid_node_features(self, centroid_node):
        centroid_node['features'] = {'graphicalCurve': {}, 'curve': []}
        centroid_node['texts'] = []

        # get curve features
        bounding_box = self.get_bounding_box_features(centroid_node['info'])
        centroid_node['features']['curve'] = [{'startX': bounding_box['x'] + 0.5 * bounding_box['width'],
                                               'startY': bounding_box['y'] + 0.5 * bounding_box['height'],
                                               'endX': bounding_box['x'] + 0.5 * bounding_box['width'],
                                               'endY': bounding_box['y'] + 0.5 * bounding_box['height']}]

        # get style features
        if 'style' in list(centroid_node['info'].keys()):
            if 'name' in list(centroid_node['info']['style']):
                centroid_node['features']['styleName'] = centroid_node['info']['style']['name']
            centroid_shape = centroid_node['info']['style']['shapes'][0]
            # get border color
            if 'border-color' in list(centroid_shape.keys()):
                centroid_node['features']['graphicalCurve']['strokeColor'] = centroid_shape['border-color']
            # get border width
            if 'border-width' in list(centroid_shape.keys()):
                centroid_node['features']['graphicalCurve']['strokeWidth'] = centroid_shape['border-width']
            # get fill color
            if 'fill-color' in list(centroid_shape.keys()):
                centroid_node['features']['graphicalCurve']['fillColor'] = centroid_shape['fill-color']

    @staticmethod
    def is_centroid_node(node):
        if 'style' in list(node['info'].keys()) \
                and 'shapes' in list(node['info']['style'].keys()) \
                and len(node['info']['style']['shapes']) == 1 \
                and 'shape' in list(node['info']['style']['shapes'][0].keys()) \
                and node['info']['style']['shapes'][0]['shape'] == "centroid":
            return True

        return False

    def extract_edge_features(self, edge):
        edge['features'] = {}
        if 'source' in list(edge['info'].keys()):
            if 'node' in list(edge['info']['source'].keys()):
                if self.find_species(edge['info']['source']['node']):
                    edge['species'] = edge['info']['source']['node']
                    edge['speciesGlyph'] = edge['info']['source']['node'] + "_glyph"
                elif self.find_reaction(edge['info']['source']['node']):
                    edge['reaction'] = edge['info']['source']['node']
                    edge['reactionGlyph'] = edge['info']['source']['node'] + "_glyph"
            if 'position' in list(edge['info']['source'].keys()):
                edge['features']['startPoint'] = edge['info']['source']['position']
        if 'target' in list(edge['info'].keys()):
            if 'node' in list(edge['info']['target'].keys()):
                if self.find_species(edge['info']['target']['node']):
                    edge['species'] = edge['info']['target']['node']
                    edge['speciesGlyph'] = edge['info']['target']['node'] + "_glyph"
                elif self.find_reaction(edge['info']['target']['node']):
                    edge['reaction'] = edge['info']['target']['node']
                    edge['reaction'] = edge['info']['target']['node'] + "_glyph"
            if 'position' in list(edge['info']['target'].keys()):
                edge['features']['endPoint'] = edge['info']['target']['position']

        curve_ = []
        if 'x' in list(edge['features']['startPoint'].keys()) and \
                'y' in list(edge['features']['startPoint'].keys()) and \
                'x' in list(edge['features']['endPoint'].keys()) and \
                'y' in list(edge['features']['endPoint'].keys()):
            edge['features']['startSlope'] = math.atan2(
                edge['features']['startPoint']['y'] - edge['features']['endPoint']['y'],
                edge['features']['startPoint']['x'] - edge['features']['endPoint']['x'])
            edge['features']['endSlope'] = math.atan2(
                edge['features']['endPoint']['y'] - edge['features']['startPoint']['y'],
                edge['features']['endPoint']['x'] - edge['features']['startPoint']['x'])
            curve_.append({'startX': edge['features']['startPoint']['x'],
                           'startY': edge['features']['startPoint']['y'],
                           'endX': edge['features']['endPoint']['x'],
                           'endY': edge['features']['endPoint']['y']})
        edge['features']['curve'] = curve_

        # get style features
        if 'style' in list(edge['info'].keys()):
            if 'name' in list(edge['info']['style']):
                edge['features']['styleName'] = edge['info']['style']['name']
            if 'shapes' in list(edge['info']['style']) and len(edge['info']['style']['shapes']):
                edge['features']['graphicalCurve'] = \
                    self.extract_curve_features(edge['info']['style']['shapes'][0], edge['features']['curve'])
                if 'arrow-head' in list(edge['info']['style']):
                    if 'name' in list(edge['info']['style']['arrow-head'].keys()):
                        edge['features']['graphicalCurve']['heads'] = {
                            'end': edge['info']['style']['arrow-head']['name']}
                    self.add_line_ending(edge['info']['style']['arrow-head'])



    def extract_graphical_shape_features(self, shapes, offset_x=0, offset_y=0):
        graphical_shape_info = {'geometricShapes': []}

        for shape in list(shapes):
            if 'shape' in list(shape.keys()):
                # get geometric shape specific features
                geometric_shape_info = self.extract_geometric_shape_exclusive_features(shape, offset_x, offset_y)

                # get border color
                if 'border-color' in list(shape.keys()):
                    geometric_shape_info['strokeColor'] = shape['border-color']
                    self.add_color(shape['border-color'])

                # get border width
                if 'border-width' in list(shape.keys()):
                    geometric_shape_info['strokeWidth'] = shape['border-width']

                if 'shape' in list(geometric_shape_info.keys()):
                    graphical_shape_info['geometricShapes'].append(geometric_shape_info)

        return graphical_shape_info

    def extract_curve_features(self, shape, curve):
        curve_info = {}
        if 'shape' in list(shape.keys()) and (shape['shape'].lower() == "line" or \
                                              shape['shape'].lower() == "connected-to-source-centroid-shape-line" or \
                                              shape['shape'].lower() == "connected-to-target-centroid-shape-line"):
            # get border color
            if 'border-color' in list(shape.keys()):
                curve_info['strokeColor'] = shape['border-color']
                self.add_color(shape['border-color'])
            # get border width
            if 'border-width' in list(shape.keys()):
                curve_info['strokeWidth'] = shape['border-width']

            # get bezier features
            if len(curve):
                element = curve[0]
                if 'p1' in list(shape.keys()) and \
                        'x' in list(shape['p1'].keys()) and 'y' in list(shape['p1'].keys()) and\
                        'p2' in list(shape.keys()) and \
                        'x' in list(shape['p2'].keys()) and 'y' in list(shape['p2'].keys()):
                    if shape['p1']['x'] > 0.0 or shape['p1']['y'] or shape['p2']['x'] or shape['p2']['y']:
                        element['basePoint1X'] = element['startX'] + 0.01 * shape['p1']['x'] *\
                                                 (element['endX'] - element['startX'])
                        element['basePoint1Y'] = element['startY'] + 0.01 * shape['p1']['y'] *\
                                                 (element['endY'] - element['startY'])
                        element['basePoint2X'] = element['endX'] + 0.01 * shape['p2']['x'] *\
                                                 (element['endX'] - element['startX'])
                        element['basePoint2Y'] = element['endY'] + 0.01 * shape['p2']['y'] *\
                                                 (element['endY'] - element['startY'])

        return curve_info

    def extract_text_features(self, node):
        for text in node['texts']:
            text['features'] = {}
            # get plain text
            text['features']['plainText'] = text['plain-text']
            # get bounding box features of the text glyph
            text['features']['boundingBox'] = dict(x=node['features']['boundingBox']['x'],
                                                           y=node['features']['boundingBox']['y'],
                                                           width=node['features']['boundingBox']['width'],
                                                           height=node['features']['boundingBox']['height'])
            graphical_text_info = {}
            if 'shape' in list(text['info'].keys()) and text['info']['shape'].lower() == "text":
                # get border color
                if 'text-color' in list(text['info'].keys()):
                    graphical_text_info['strokeColor'] = text['info']['text-color']
                    self.add_color(text['info']['text-color'])

                # get position x
                if 'x' in list(text['info'].keys()):
                    text['features']['boundingBox']['x'] = text['info']['x'] +\
                                                           text['features']['boundingBox']['x'] +\
                                                           0.5 * text['features']['boundingBox']['width']

                # get position y
                if 'y' in list(text['info'].keys()):
                    text['features']['boundingBox']['y'] = text['info']['y'] +\
                                                           text['features']['boundingBox']['y'] +\
                                                           0.5 * text['features']['boundingBox']['height']

                # get dimension width
                if 'width' in list(text['info'].keys()):
                    text['features']['boundingBox']['width'] = text['info']['width']

                # get dimension width
                if 'height' in list(text['info'].keys()):
                    text['features']['boundingBox']['height'] = text['info']['height']

                # get font family
                if 'font-family' in list(text['info'].keys()):
                    graphical_text_info['fontFamily'] = text['info']['font-family']

                # get font size
                if 'font-size' in list(text['info'].keys()):
                    graphical_text_info['fontSize'] = {'abs': text['info']['font-size'], 'rel': 0.0}

                # get font weight
                if 'font-wight' in list(text['info'].keys()):
                    graphical_text_info['fontWeight'] = text['info']['font-weight']

                # get font style
                if 'font-style' in list(text['info'].keys()):
                    graphical_text_info['fontStyle'] = text['info']['font-style']

                # get horizontal text anchor
                if 'horizontal-alignment' in list(text['info'].keys()):
                    graphical_text_info['hTextAnchor'] = text['info']['horizontal-alignment']

                # get vertical text anchor
                if 'vertical-alignment' in list(text['info'].keys()):
                    graphical_text_info['vTextAnchor'] = text['info']['vertical-alignment']

            # get group features
            text['features']['graphicalText'] = graphical_text_info


    def extract_geometric_shape_exclusive_features(self, shape, offset_x=0, offset_y=0):
        if shape['shape'].lower() == "rectangle":
            return self.extract_rectangle_shape_features(shape, offset_x, offset_y)
        elif shape['shape'].lower() == "ellipse":
            return self.extract_ellipse_shape_features(shape, offset_x, offset_y)
        elif shape['shape'].lower() == "polygon":
            return self.extract_polygon_shape_features(shape, offset_x, offset_y)
        return {}

    def extract_rectangle_shape_features(self, rect_shape, offset_x=0, offset_y=0):
        rect_shape_info = {'shape': "rectangle"}

        # get fill color
        if 'fill-color' in list(rect_shape.keys()):
            rect_shape_info['fillColor'] = rect_shape['fill-color']
            self.add_color(rect_shape['fill-color'])

        # get position x
        if 'x' in list(rect_shape.keys()):
            rect_shape_info['x'] = {'abs': rect_shape['x'] + offset_x, 'rel': 0}

        # get position y
        if 'y' in list(rect_shape.keys()):
            rect_shape_info['y'] = {'abs': rect_shape['y'] + offset_y, 'rel': 0}

        # get dimension width
        if 'width' in list(rect_shape.keys()):
            rect_shape_info['width'] = {'abs': rect_shape['width'], 'rel': 0}

        # get dimension height
        if 'height' in list(rect_shape.keys()):
            rect_shape_info['height'] = {'abs': rect_shape['height'], 'rel': 0}

        # get corner curvature radius rx
        if 'rx' in list(rect_shape.keys()):
            rect_shape_info['rx'] = {'abs': rect_shape['rx'], 'rel': 0}

        # get corner curvature radius ry
        if 'ry' in list(rect_shape.keys()):
            rect_shape_info['ry'] = {'abs': rect_shape['ry'], 'rel': 0}

        return rect_shape_info

    def extract_ellipse_shape_features(self, ellipse_shape, offset_x=0, offset_y=0):
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if 'fill-color' in list(ellipse_shape.keys()):
            ellipse_shape_info['fillColor'] = ellipse_shape['fill-color']
            self.add_color(ellipse_shape['fill-color'])

        # get position cx
        if 'cx' in list(ellipse_shape.keys()):
            ellipse_shape_info['cx'] = {'abs': ellipse_shape['cx'] + offset_x, 'rel': 0}

        # get position cy
        if 'cy' in list(ellipse_shape.keys()):
            ellipse_shape_info['cy'] = {'abs': ellipse_shape['cy'] + offset_y, 'rel': 0}

        # get dimension rx
        if 'rx' in list(ellipse_shape.keys()):
            ellipse_shape_info['rx'] = {'abs': ellipse_shape['rx'], 'rel': 0}

        # get dimension ry
        if 'ry' in list(ellipse_shape.keys()):
            ellipse_shape_info['ry'] = {'abs': ellipse_shape['ry'], 'rel': 0}

        return ellipse_shape_info

    def extract_polygon_shape_features(self, polygon_shape, offset_x=0, offset_y=0):
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if 'fill-color' in list(polygon_shape.keys()):
            polygon_shape_info['fillColor'] = polygon_shape['fill-color']
            self.add_color(polygon_shape['fill-color'])

        # set vertices
        if 'points' in list(polygon_shape.keys()):
            vertices_ = []
            for point in polygon_shape['points']:
                vertex_ = {}
                if 'x' in list(point.keys()) and 'y' in list(point.keys()):
                    vertex_['renderPointX'] = {'abs': point['x'] + offset_x, 'rel': 0}
                    vertex_['renderPointY'] = {'abs': point['y'] + offset_y, 'rel': 0}
                vertices_.append(vertex_)

            polygon_shape_info['vertices'] = vertices_
        return polygon_shape_info

    @staticmethod
    def get_bounding_box_features(info):
        bounding_box = {'x': 0.0, 'y': 0.0, 'width': 0.0, 'height': 0.0}
        if 'position' in list(info.keys()) and \
                'x' in list(info['position'].keys()) and \
                'y' in list(info['position'].keys()):
            bounding_box['x'] = info['position']['x']
            bounding_box['y'] = info['position']['y']
        if 'dimensions' in list(info.keys()) and \
                'width' in list(info['dimensions'].keys()) and \
                'height' in list(info['dimensions'].keys()):
            bounding_box['x'] -= 0.5 * info['dimensions']['width']
            bounding_box['y'] -= 0.5 * info['dimensions']['height']
            bounding_box['width'] = info['dimensions']['width']
            bounding_box['height'] = info['dimensions']['height']
        return bounding_box