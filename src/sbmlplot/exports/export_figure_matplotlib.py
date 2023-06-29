from exports.export_base import NetworkInfoExportBase
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Polygon, Path, PathPatch
import matplotlib.transforms as plttransform
import matplotlib.cbook as cbook
import numpy as np
import math


class NetworkInfoExportToMatPlotLib(NetworkInfoExportBase):
    def __init__(self):
        self.sbml_figure, self.sbml_axes = plt.subplots()
        self.sbml_axes.invert_yaxis()
        self.export_figure_format = ".pdf"
        super().__init__()

    def reset(self):
        super().reset()
        self.sbml_axes.clear()
        self.sbml_figure.set_size_inches(1.0, 1.0)
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
                            image_shape = features['graphicalShape']['geometricShapes'][gs_index]

                            # default features
                            position_x = bbox_x
                            position_y = bbox_y
                            dimension_width = bbox_width
                            dimension_height = bbox_height

                            if 'x' in list(image_shape.keys()):
                                position_x += image_shape['x']['abs'] + \
                                              0.01 * image_shape['x']['rel'] * bbox_width
                            if 'y' in list(image_shape.keys()):
                                position_y += image_shape['y']['abs'] + \
                                              0.01 * image_shape['y']['rel'] * bbox_height
                            if 'width' in list(image_shape.keys()):
                                dimension_width = image_shape['width']['abs'] + \
                                                  0.01 * image_shape['width']['rel'] * bbox_width
                            if 'height' in list(image_shape.keys()):
                                dimension_height = image_shape['height']['abs'] + \
                                                   0.01 * image_shape['height']['rel'] * bbox_height

                            # add a rounded rectangle to plot
                            if 'href' in list(image_shape.keys()):
                                with cbook.get_sample_data(image_shape['href']) as image_file:
                                    image = plt.imread(image_file)
                                    image_axes = ax.imshow(image)
                                    image_axes.set_extent([position_x, position_x + dimension_width, position_y +
                                                           dimension_height, position_y])
                                    image_axes.set_zorder(z_order)
                                    if offset_x or offset_y:
                                        image_axes.set_transform(plttransform.Affine2D().
                                                                 rotate_around(offset_x, offset_y,
                                                                               slope) + self.sbml_axes.transData)
                                    else:
                                        image_axes.set_transform(plttransform.Affine2D().
                                                                 rotate_around(position_x + 0.5 * dimension_width,
                                                                               position_y + 0.5 * dimension_height,
                                                                               slope) + self.sbml_axes.transData)

                        # draw a render curve
                        if features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'renderCurve':
                            curve_shape = features['graphicalShape']['geometricShapes'][gs_index]
                            if 'strokeColor' in list(curve_shape.keys()):
                                stroke_color = curve_shape['strokeColor']
                            if 'strokeWidth' in list(curve_shape.keys()):
                                stroke_width = curve_shape['strokeWidth']
                            if 'strokeDashArray' in list(curve_shape.keys()):
                                stroke_dash_array = (0, curve_shape['graphicalShape']['strokeDashArray'])

                            curve_features = {'graphicalCurve': {'strokeColor': stroke_color,
                                                                 'strokeWidth': stroke_width,
                                                                 'strokeDashArray': stroke_dash_array}}

                            # add a render curve to plot
                            if 'vertices' in list(curve_shape.keys()):
                                curve_features['curve'] = []
                                for v_index in range(len(curve_shape['vertices']) - 1):
                                    element_ = {'startX': curve_shape['vertices'][v_index]['renderPointX']['abs'] +
                                                          0.01 * curve_shape['vertices'][v_index]['renderPointX'][
                                                              'rel'] *
                                                          bbox_width + bbox_x,
                                                'startY': curve_shape['vertices'][v_index]['renderPointY']['abs'] +
                                                          0.01 * curve_shape['vertices'][v_index]['renderPointY'][
                                                              'rel'] *
                                                          bbox_height + bbox_y,
                                                'endX': curve_shape['vertices'][v_index + 1]['renderPointX']['abs'] +
                                                        0.01 * curve_shape['vertices'][v_index + 1]['renderPointX'][
                                                            'rel'] *
                                                        bbox_width + bbox_x,
                                                'endY': curve_shape['vertices'][v_index + 1]['renderPointY']['abs'] +
                                                        0.01 * curve_shape['vertices'][v_index + 1]['renderPointY'][
                                                            'rel'] *
                                                        bbox_height + + bbox_y}

                                    if 'basePoint1X' in list(curve_shape['vertices'][v_index].keys()):
                                        element_ = {
                                            'basePoint1X': curve_shape['vertices'][v_index]['basePoint1X']['abs'] +
                                                           0.01 * curve_shape['vertices'][v_index]['basePoint1X'][
                                                               'rel'] *
                                                           bbox_width + bbox_x,
                                            'basePoint1Y': curve_shape['vertices'][v_index]['basePoint1Y']['abs'] +
                                                           0.01 * curve_shape['vertices'][v_index]['basePoint1Y'][
                                                               'rel'] *
                                                           bbox_height + bbox_y,
                                            'basePoint2X': curve_shape['vertices'][v_index]['basePoint2X']['abs'] +
                                                           0.01 * curve_shape['vertices'][v_index]['basePoint2X'][
                                                               'rel'] *
                                                           bbox_width + bbox_x,
                                            'basePoint2Y': curve_shape['vertices'][v_index]['basePoint2Y']['abs'] +
                                                           0.01 * curve_shape['vertices'][v_index]['basePoint2Y'][
                                                               'rel'] *
                                                           bbox_height + bbox_y}

                                    curve_features['curve'].append(element_)

                                self.add_curve_to_scene(curve_features, z_order=3)

                        # draw a rounded rectangle
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'rectangle':
                            rectangle_shape = features['graphicalShape']['geometricShapes'][gs_index]

                            # default features
                            position_x = bbox_x
                            position_y = bbox_y
                            dimension_width = bbox_width
                            dimension_height = bbox_height
                            corner_radius = 0.0

                            if 'strokeColor' in list(rectangle_shape.keys()):
                                stroke_color = rectangle_shape['strokeColor']
                            if 'strokeWidth' in list(rectangle_shape.keys()):
                                stroke_width = rectangle_shape['strokeWidth']
                            if 'strokeDashArray' in list(rectangle_shape.keys()):
                                stroke_dash_array = (0, rectangle_shape['strokeDashArray'])
                            if 'fillColor' in list(rectangle_shape.keys()):
                                fill_color = rectangle_shape['fillColor']
                            if 'x' in list(rectangle_shape.keys()):
                                position_x += rectangle_shape['x']['abs'] + \
                                              0.01 * rectangle_shape['x']['rel'] * bbox_width
                            if 'y' in list(rectangle_shape.keys()):
                                position_y += rectangle_shape['y']['abs'] + \
                                              0.01 * rectangle_shape['y']['rel'] * bbox_height
                            if 'width' in list(rectangle_shape.keys()):
                                dimension_width = rectangle_shape['width']['abs'] + \
                                                  0.01 * rectangle_shape['width']['rel'] * bbox_width
                            if 'height' in list(rectangle_shape.keys()):
                                dimension_height = rectangle_shape['height']['abs'] + \
                                                   0.01 * rectangle_shape['height']['rel'] * bbox_height
                            if 'ratio' in list(rectangle_shape.keys()) and rectangle_shape['ratio'] > 0.0:
                                if (bbox_width / bbox_height) <= rectangle_shape['ratio']:
                                    dimension_width = bbox_width
                                    dimension_height = bbox_width / rectangle_shape['ratio']
                                    position_y += 0.5 * (bbox_height - dimension_height)
                                else:
                                    dimension_height = bbox_height
                                    dimension_width = rectangle_shape['ratio'] * bbox_height
                                    position_x += 0.5 * (bbox_width - dimension_width)
                            if 'rx' in list(rectangle_shape.keys()):
                                corner_radius = rectangle_shape['rx']['abs'] + \
                                                0.01 * rectangle_shape['rx']['rel'] * 0.5 * (bbox_width + bbox_height)
                            elif 'ry' in list(rectangle_shape.keys()):
                                corner_radius = rectangle_shape['ry']['abs'] + \
                                                0.01 * rectangle_shape['ry']['rel'] * 0.5 * (bbox_width + bbox_height)

                            # add a rounded rectangle to plot
                            fancy_box = FancyBboxPatch((position_x, position_y), dimension_width, dimension_height,
                                                       edgecolor=self.graph_info.find_color_value(stroke_color, False),
                                                       facecolor=self.graph_info.find_color_value(fill_color),
                                                       fill=True,
                                                       linewidth=stroke_width, linestyle=stroke_dash_array,
                                                       zorder=z_order, antialiased=True)
                            fancy_box.set_boxstyle("round", rounding_size=corner_radius)
                            if offset_x or offset_y:
                                fancy_box.set_transform(plttransform.Affine2D().
                                                        rotate_around(offset_x, offset_y,
                                                                      slope) + self.sbml_axes.transData)
                            else:
                                fancy_box.set_transform(plttransform.Affine2D().
                                                        rotate_around(position_x + 0.5 * dimension_width,
                                                                      position_y + 0.5 * dimension_height,
                                                                      slope) + self.sbml_axes.transData)
                            self.sbml_axes.add_patch(fancy_box)

                        # draw an ellipse
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'ellipse':
                            ellipse_shape = features['graphicalShape']['geometricShapes'][gs_index]

                            # default features
                            position_cx = bbox_x
                            position_cy = bbox_y
                            dimension_rx = 0.5 * bbox_width
                            dimension_ry = 0.5 * bbox_height

                            if 'strokeColor' in list(ellipse_shape.keys()):
                                stroke_color = ellipse_shape['strokeColor']
                            if 'strokeWidth' in list(ellipse_shape.keys()):
                                stroke_width = ellipse_shape['strokeWidth']
                            if 'strokeDashArray' in list(ellipse_shape.keys()):
                                stroke_dash_array = (0, ellipse_shape['strokeDashArray'])
                            if 'fillColor' in list(ellipse_shape.keys()):
                                fill_color = ellipse_shape['fillColor']
                            if 'cx' in list(ellipse_shape.keys()):
                                position_cx += ellipse_shape['cx']['abs'] + 0.01 * ellipse_shape['cx'][
                                    'rel'] * bbox_width
                            if 'cy' in list(ellipse_shape.keys()):
                                position_cy += ellipse_shape['cy']['abs'] + 0.01 * ellipse_shape['cy'][
                                    'rel'] * bbox_height
                            if 'rx' in list(ellipse_shape.keys()):
                                dimension_rx = ellipse_shape['rx']['abs'] + 0.01 * ellipse_shape['rx'][
                                    'rel'] * bbox_width
                            if 'ry' in list(ellipse_shape.keys()):
                                dimension_ry = ellipse_shape['ry']['abs'] + \
                                               0.01 * ellipse_shape['ry']['rel'] * bbox_height
                            if 'ratio' in list(ellipse_shape.keys()) and ellipse_shape['ratio'] > 0.0:
                                if (bbox_width / bbox_height) <= ellipse_shape['ratio']:
                                    dimension_rx = 0.5 * bbox_width
                                    dimension_ry = (0.5 * bbox_width / ellipse_shape['ratio'])
                                else:
                                    dimension_ry = 0.5 * bbox_height
                                    dimension_rx = ellipse_shape['ratio'] * 0.5 * bbox_height

                            # add an ellipse to plot
                            ellipse = Ellipse((position_cx, position_cy), 2 * dimension_rx, 2 * dimension_ry,
                                              edgecolor=self.graph_info.find_color_value(stroke_color, False),
                                              facecolor=self.graph_info.find_color_value(fill_color), fill=True,
                                              linewidth=stroke_width, linestyle=stroke_dash_array,
                                              zorder=z_order, antialiased=True)
                            if offset_x or offset_y:
                                ellipse.set_transform(plttransform.Affine2D().rotate_around(offset_x,
                                                                                            offset_y,
                                                                                            slope) + self.sbml_axes.transData)
                            else:
                                ellipse.set_transform(plttransform.Affine2D().
                                                      rotate_around(position_cx, position_cy,
                                                                    slope) + self.sbml_axes.transData)
                            self.sbml_axes.add_patch(ellipse)

                        # draw a polygon
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'polygon':
                            polygon_shape = features['graphicalShape']['geometricShapes'][gs_index]

                            if 'strokeColor' in list(polygon_shape.keys()):
                                stroke_color = polygon_shape['strokeColor']
                            if 'strokeWidth' in list(polygon_shape.keys()):
                                stroke_width = polygon_shape['strokeWidth']
                            if 'strokeDashArray' in list(polygon_shape.keys()):
                                stroke_dash_array = (0, polygon_shape['strokeDashArray'])
                            if 'fillColor' in list(polygon_shape.keys()):
                                fill_color = polygon_shape['fillColor']
                            # if 'fillRule' in list(polygon_shape.keys()):
                            # fill_rule = polygon_shape['fillRule']

                            # add a polygon to plot
                            if 'vertices' in list(polygon_shape.keys()):
                                vertices = np.empty((0, 2))
                                for v_index in range(len(polygon_shape['vertices'])):
                                    vertices = np.append(vertices,
                                                         np.array([[polygon_shape['vertices'][v_index]
                                                                    ['renderPointX']['abs'] +
                                                                    0.01 * polygon_shape['vertices'][v_index]
                                                                    ['renderPointX']['rel'] * bbox_width,
                                                                    polygon_shape['vertices'][v_index]
                                                                    ['renderPointY']['abs'] +
                                                                    0.01 * polygon_shape['vertices'][v_index]
                                                                    ['renderPointY']['rel'] * bbox_height]]), axis=0)

                                if offset_x or offset_y:
                                    vertices[:, 0] += offset_x - bbox_width
                                    vertices[:, 1] += offset_y - 0.5 * bbox_height
                                    polygon = Polygon(vertices, closed=True,
                                                      edgecolor=self.graph_info.find_color_value(stroke_color, False),
                                                      facecolor=self.graph_info.find_color_value(fill_color),
                                                      fill=True, linewidth=stroke_width, linestyle=stroke_dash_array,
                                                      antialiased=True)
                                    polygon.set_transform(
                                        plttransform.Affine2D().rotate_around(offset_x, offset_y,
                                                                              slope) + self.sbml_axes.transData)
                                else:
                                    polygon = Polygon(vertices, closed=True,
                                                      edgecolor=self.graph_info.find_color_value(stroke_color, False),
                                                      facecolor=self.graph_info.find_color_value(fill_color),
                                                      fill=True, linewidth=stroke_width, linestyle=stroke_dash_array,
                                                      zorder=z_order, antialiased=True)
                                self.sbml_axes.add_patch(polygon)

                else:
                    # add a simple rectangle to plot
                    rectangle = Rectangle((bbox_x, bbox_y), bbox_width, bbox_height, slope * (180.0 / math.pi),
                                          edgecolor=self.graph_info.find_color_value(stroke_color, False),
                                          facecolor=self.graph_info.find_color_value(fill_color), fill=True,
                                          linewidth=stroke_width, linestyle=stroke_dash_array,
                                          zorder=z_order, antialiased=True)
                    self.sbml_axes.add_patch(rectangle)

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

            for v_index in range(len(features['curve'])):
                vertices = [(features['curve'][v_index]['startX'], features['curve'][v_index]['startY'])]
                codes = [Path.MOVETO]
                if 'basePoint1X' in list(features['curve'][v_index].keys()):
                    vertices.append(
                        (features['curve'][v_index]['basePoint1X'], features['curve'][v_index]['basePoint1Y']))
                    vertices.append(
                        (features['curve'][v_index]['basePoint2X'], features['curve'][v_index]['basePoint2Y']))
                    codes.append(Path.CURVE4)
                    codes.append(Path.CURVE4)
                    codes.append(Path.CURVE4)
                else:
                    codes.append(Path.LINETO)
                vertices.append((features['curve'][v_index]['endX'], features['curve'][v_index]['endY']))

                # draw a curve
                curve = PathPatch(Path(vertices, codes),
                                  edgecolor=self.graph_info.find_color_value(stroke_color, False),
                                  facecolor='none', linewidth=stroke_width, linestyle=stroke_dash_array,
                                  capstyle='butt', zorder=z_order, antialiased=True)
                self.sbml_axes.add_patch(curve)

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

                        # draw text
                        self.ax.text(position_x + 0.5 * bbox_width, position_y + 0.5 * bbox_height, plain_text,
                                     color=font_color, fontfamily=font_family, fontsize=font_size,
                                     fontstyle=font_style, fontweight=font_weight,
                                     va=v_text_anchor, ha=h_text_anchor, zorder=5)

                # draw the text itself
                else:
                    self.sbml_axes.text(bbox_x + 0.5 * bbox_width, bbox_y + 0.5 * bbox_height, plain_text,
                                        color=font_color, fontfamily=font_family, fontsize=font_size,
                                        fontstyle=font_style, fontweight=font_weight,
                                        va=v_text_anchor, ha=h_text_anchor, zorder=5)

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

    def set_export_figure_format(self, export_figure_format):
        self.export_figure_format = export_figure_format

    def export(self, file_name):
        if self.export_figure_format in [".pdf", ".svg", ".png"] and len(self.sbml_axes.patches):
            self.sbml_axes.set_aspect('equal')
            self.sbml_figure.set_size_inches(max(1.0, (self.graph_info.extents['maxX'] -
                                                       self.graph_info.extents['minX']) / 72.0),
                                             max(1.0, (self.graph_info.extents['maxY'] -
                                                       self.graph_info.extents['minY']) / 72.0))
            plt.axis('equal')
            plt.axis('off')
            plt.tight_layout()
            self.sbml_figure.savefig(file_name.split('.')[0] + self.export_figure_format, transparent=True,
                                     dpi=300)
            plt.close('all')