from exports.export_base import NetworkInfoExportBase
import math

class NetworkInfoExportToFigureBase(NetworkInfoExportBase):
    def __init__(self):
        self.export_figure_format = ".pdf"
        super().__init__()

    def reset(self):
        super().reset()
        self.export_figure_format = ".pdf"

    def add_compartment(self, compartment):
        # compartment
        if 'features' in list(compartment.keys()):
            self.add_graphical_shape_to_scene(compartment['features'], z_order=0)
        # compartment text
        if 'texts' in list(compartment.keys()):
            for text in compartment['texts']:
                if 'features' in list(text.keys()):
                    self.add_text_to_scene(text['features'])

    def add_species(self, species):
        # species
        if 'features' in list(species.keys()):
            self.add_graphical_shape_to_scene(species['features'], z_order=4)
        # species text
        if 'texts' in list(species.keys()):
            for text in species['texts']:
                if 'features' in list(text.keys()):
                    self.add_text_to_scene(text['features'])

    def add_reaction(self, reaction):
        # reaction
        if 'features' in list(reaction.keys()):
            # reaction curve
            if 'curve' in list(reaction['features']):
                self.add_curve_to_scene(reaction['features'], z_order=3)
            # reaction graphical shape
            elif 'boundingBox' in list(reaction['features']):
                self.add_graphical_shape_to_scene(reaction['features'], z_order=3)

        # species references
        if 'speciesReferences' in list(reaction.keys()):
            for sr in reaction['speciesReferences']:
                self.add_species_reference(sr)

    def add_species_reference(self, species_reference):
        if 'features' in list(species_reference.keys()):
            # species reference
            self.add_curve_to_scene(species_reference['features'], z_order=1)

            # line endings
            self.add_line_endings_to_scene(species_reference['features'])

    def add_graphical_shape_to_scene(self, features, offset_x=0.0, offset_y=0.0, slope=0.0, z_order=0):
        if 'boundingBox' in list(features.keys()):
            if (offset_x or offset_y) and slope:
                offset_x += 1.5 * math.cos(slope)
                offset_y += 1.5 * math.sin(slope)
            bbox_x = features['boundingBox']['x'] + offset_x
            bbox_y = features['boundingBox']['y'] + offset_y
            bbox_width = features['boundingBox']['width']
            bbox_height = features['boundingBox']['height']

            # default features
            stroke_color = 'black'
            stroke_width = '1.0'
            stroke_dash_array = 'solid'
            fill_color = 'white'

            if 'graphicalShape' in list(features.keys()):
                if 'strokeColor' in list(features['graphicalShape'].keys()):
                    stroke_color = features['graphicalShape']['strokeColor']
                if 'strokeWidth' in list(features['graphicalShape'].keys()):
                    stroke_width = features['graphicalShape']['strokeWidth']
                if 'strokeDashArray' in list(features['graphicalShape'].keys()):
                    stroke_dash_array = (0, features['graphicalShape']['strokeDashArray'])
                if 'fillColor' in list(features['graphicalShape'].keys()):
                    fill_color = features['graphicalShape']['fillColor']

                if 'geometricShapes' in list(features['graphicalShape'].keys()):
                    for gs_index in range(len(features['graphicalShape']['geometricShapes'])):
                        # draw an image
                        if features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'image':
                            self.draw_image(features['graphicalShape']['geometricShapes'][gs_index],
                                       bbox_x, bbox_y, bbox_width, bbox_height,
                                            offset_x, offset_y, slope, z_order)

                        # draw a render curve
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'renderCurve':
                            self.draw_render_curve(features['graphicalShape']['geometricShapes'][gs_index],
                                                   bbox_x, bbox_y, bbox_width, bbox_height,
                                                   stroke_color, stroke_width, stroke_dash_array, z_order)

                        # draw a rounded rectangle
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'rectangle':
                            self.draw_rounded_rectangle(features['graphicalShape']['geometricShapes'][gs_index],
                                                        bbox_x, bbox_y, bbox_width, bbox_height,
                                                        stroke_color, stroke_width, stroke_dash_array, fill_color,
                                                        offset_x, offset_y, slope, z_order)


                        # draw an ellipse
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'ellipse':
                            self.draw_ellipse(features['graphicalShape']['geometricShapes'][gs_index],
                                              bbox_x, bbox_y, bbox_width, bbox_height,
                                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                                              offset_x, offset_y, slope, z_order)

                        # draw a polygon
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'polygon':
                            self.draw_polygon(features['graphicalShape']['geometricShapes'][gs_index],
                                              bbox_x, bbox_y, bbox_width, bbox_height,
                                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                                              offset_x, offset_y, slope, z_order)

                else:
                    self.draw_simple_rectangle(features['graphicalShape']['geometricShapes'][gs_index],
                                               bbox_x, bbox_y, bbox_width, bbox_height,
                                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                                               offset_x, offset_y, slope, z_order)

    def add_curve_to_scene(self, features, z_order=1):
        if 'curve' in list(features.keys()):
            # default features
            stroke_color = 'black'
            stroke_width = '1.0'
            stroke_dash_array = 'solid'

            if 'graphicalCurve' in list(features.keys()):
                if 'strokeColor' in list(features['graphicalCurve'].keys()):
                    stroke_color = features['graphicalCurve']['strokeColor']
                if 'strokeWidth' in list(features['graphicalCurve'].keys()):
                    stroke_width = features['graphicalCurve']['strokeWidth']
                if 'strokeDashArray' in list(features['graphicalCurve'].keys()) \
                        and not features['graphicalCurve']['strokeDashArray'] == 'solid':
                    stroke_dash_array = (0, features['graphicalCurve']['strokeDashArray'])

            self.draw_curve(features['curve'], stroke_color, stroke_width, stroke_dash_array, z_order)

    def add_text_to_scene(self, features):
        if 'plainText' in list(features.keys()) and 'boundingBox' in list(features.keys()):
            plain_text = features['plainText']
            bbox_x = features['boundingBox']['x']
            bbox_y = features['boundingBox']['y']
            bbox_width = features['boundingBox']['width']
            bbox_height = features['boundingBox']['height']

            # default features
            font_color = 'black'
            font_family = 'monospace'
            font_size = '12.0'
            font_style = 'normal'
            font_weight = 'normal'
            h_text_anchor = 'center'
            v_text_anchor = 'center'

            if 'graphicalText' in list(features.keys()):
                if 'strokeColor' in list(features['graphicalText'].keys()):
                    font_color = self.graph_info.find_color_value(features['graphicalText']['strokeColor'], False)
                if 'fontFamily' in list(features['graphicalText'].keys()):
                    font_family = features['graphicalText']['fontFamily']
                if 'fontSize' in list(features['graphicalText'].keys()):
                    font_size = features['graphicalText']['fontSize']['abs'] + \
                                0.01 * features['graphicalText']['fontSize']['rel'] * bbox_width
                if 'fontStyle' in list(features['graphicalText'].keys()):
                    font_style = features['graphicalText']['fontStyle']
                if 'fontWeight' in list(features['graphicalText'].keys()):
                    font_weight = features['graphicalText']['fontWeight']
                if 'hTextAnchor' in list(features['graphicalText'].keys()):
                    if features['graphicalText']['hTextAnchor'] == 'start':
                        h_text_anchor = 'left'
                    elif features['graphicalText']['hTextAnchor'] == 'middle':
                        h_text_anchor = 'center'
                    elif features['graphicalText']['hTextAnchor'] == 'end':
                        h_text_anchor = 'right'
                if 'vTextAnchor' in list(features['graphicalText'].keys()):
                    if features['graphicalText']['vTextAnchor'] == 'middle':
                        v_text_anchor = 'center'
                    else:
                        v_text_anchor = features['graphicalText']['vTextAnchor']

                # get geometric shape features
                if 'geometricShapes' in list(features['graphicalText'].keys()):
                    for gs_index in range(len(features['graphicalText']['geometricShapes'])):
                        position_x = bbox_x
                        position_y = bbox_y

                        if 'x' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            position_x += features['graphicalText']['geometricShapes'][gs_index]['x']['abs'] + \
                                          0.01 * features['graphicalText']['geometricShapes'][gs_index]['x']['rel'] \
                                          * bbox_width
                        if 'y' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            position_y += features['graphicalText']['geometricShapes'][gs_index]['y']['abs'] + \
                                          0.01 * features['graphicalText']['geometricShapes'][gs_index]['y']['rel'] \
                                          * bbox_height
                        if 'strokeColor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_color = self.graph_info.find_color_value(features['graphicalText']
                                                                          ['geometricShapes'][gs_index]['strokeColor'],
                                                                          False)
                        if 'fontFamily' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_family = features['graphicalText']['geometricShapes'][gs_index]['fontFamily']
                        if 'fontSize' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_size = features['graphicalText']['geometricShapes'][gs_index]['fontSize']['abs'] + \
                                        0.01 * features['graphicalText']['geometricShapes'][gs_index]['fontSize']['rel'] \
                                        * bbox_width
                        if 'fontStyle' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_style = features['graphicalText']['geometricShapes'][gs_index]['fontStyle']
                        if 'fontWeight' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_weight = features['graphicalText']['geometricShapes'][gs_index]['fontWeight']
                        if 'hTextAnchor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            if features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'start':
                                h_text_anchor = 'left'
                            elif features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'middle':
                                h_text_anchor = 'center'
                            elif features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'end':
                                h_text_anchor = 'right'
                        if 'vTextAnchor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            if features['graphicalText']['geometricShapes'][gs_index]['vTextAnchor'] == 'middle':
                                v_text_anchor = 'center'
                            else:
                                v_text_anchor = features['graphicalText']['geometricShapes'][gs_index]['vTextAnchor']

                        self.draw_text(position_x, position_y, bbox_width, bbox_height,
                                       plain_text, font_color, font_family, font_size, font_style, font_weight,
                                       v_text_anchor, h_text_anchor, 5)
                else:
                    self.draw_text(bbox_x, bbox_y, bbox_width, bbox_height,
                                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                                   v_text_anchor, h_text_anchor, 5)

    def add_line_endings_to_scene(self, features):
        if 'graphicalCurve' in list(features.keys()) and 'heads' in list(features['graphicalCurve'].keys()):
            # draw start head
            if 'start' in list(features['graphicalCurve']['heads'].keys()):
                line_ending = self.graph_info.find_line_ending(features['graphicalCurve']['heads']['start'])
                if line_ending and 'features' in list(line_ending.keys()):
                    if 'enableRotation' in list(line_ending['features'].keys()) \
                            and not line_ending['features']['enableRotation']:
                        self.add_graphical_shape_to_scene(line_ending['features'],
                                                          offset_x=features['startPoint']['x'],
                                                          offset_y=features['startPoint']['y'], z_order=2)
                    else:
                        self.add_graphical_shape_to_scene(line_ending['features'],
                                                          offset_x=features['startPoint']['x'],
                                                          offset_y=features['startPoint']['y'],
                                                          slope=features['startSlope'], z_order=2)

            # draw end head
            if 'end' in list(features['graphicalCurve']['heads'].keys()):
                line_ending = self.graph_info.find_line_ending(features['graphicalCurve']['heads']['end'])
                if line_ending and 'features' in list(line_ending.keys()):
                    if 'enableRotation' in list(line_ending['features'].keys()) \
                            and not line_ending['features']['enableRotation']:
                        self.add_graphical_shape_to_scene(ax, line_ending['features'],
                                                          offset_x=features['endPoint']['x'],
                                                          offset_y=features['endPoint']['y'], z_order=2)
                    else:
                        self.add_graphical_shape_to_scene(line_ending['features'],
                                                          offset_x=features['endPoint']['x'],
                                                          offset_y=features['endPoint']['y'],
                                                          slope=features['endSlope'], z_order=2)

    def draw_image(self, image_shape, bbox_x, bbox_y, bbox_width, bbox_height,
                   offset_x, offset_y, slope, z_order):
        pass

    def draw_render_curve(self, curve_shape, bbox_x, bbox_y, bbox_width, bbox_height,
                          stroke_color, stroke_width, stroke_dash_array, z_order):
        pass

    def draw_rounded_rectangle(self, rectangle_shape, bbox_x, bbox_y, bbox_width, bbox_height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               offset_x, offset_y, slope, z_order):
        pass

    def draw_simple_rectangle(self, bbox_x, bbox_y, bbox_width, bbox_height,
                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                              offset_x, offset_y, slope, z_order):
        pass

    def draw_ellipse(self, ellipse_shape, bbox_x, bbox_y, bbox_width, bbox_height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        pass

    def draw_polygon(self, polygon_shape, bbox_x, bbox_y, bbox_width, bbox_height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        pass

    def draw_curve(self, curve_shape, stroke_color, stroke_width, stroke_dash_array,
                   z_order):
        pass

    def draw_text(self, position_x, position_y, bbox_width, bbox_height,
                  plain_text, font_color, font_family, font_size, font_style, font_weight,
                  v_text_anchor, h_text_anchor, zorder):
        pass

    def set_export_figure_format(self, export_figure_format):
        self.export_figure_format = export_figure_format

    def export(self, file_name):
        pass