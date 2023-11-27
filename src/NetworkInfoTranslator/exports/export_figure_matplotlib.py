from .export_figure_base import NetworkInfoExportToFigureBase
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Polygon, Path, PathPatch
import matplotlib.transforms as plttransform
import matplotlib.cbook as cbook
import numpy as np


class NetworkInfoExportToMatPlotLib(NetworkInfoExportToFigureBase):
    def __init__(self):
        self.sbml_figure, self.sbml_axes = plt.subplots()
        self.sbml_axes.invert_yaxis()
        super().__init__()

    def reset(self):
        super().reset()
        self.sbml_axes.clear()
        self.sbml_figure.set_size_inches(1.0, 1.0)

    def draw_image(self, image_shape, x, y, width, height,
                   offset_x, offset_y, slope, z_order):
        # default features
        position_x = x
        position_y = y
        dimension_width = width
        dimension_height = height

        if 'x' in list(image_shape.keys()):
            position_x += image_shape['x']['abs'] + \
                          0.01 * image_shape['x']['rel'] * width
        if 'y' in list(image_shape.keys()):
            position_y += image_shape['y']['abs'] + \
                          0.01 * image_shape['y']['rel'] * height
        if 'width' in list(image_shape.keys()):
            dimension_width = image_shape['width']['abs'] + \
                              0.01 * image_shape['width']['rel'] * width
        if 'height' in list(image_shape.keys()):
            dimension_height = image_shape['height']['abs'] + \
                               0.01 * image_shape['height']['rel'] * height

        # add a rounded rectangle to plot
        if 'href' in list(image_shape.keys()):
            with cbook.get_sample_data(image_shape['href']) as image_file:
                image = plt.imread(image_file)
                image_axes = self.sbml_axes.imshow(image)
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

    def draw_render_curve(self, curve_shape, x, y, width, height,
                          stroke_color, stroke_width, stroke_dash_array,
                          z_order):
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
                                          'rel'] * width + x,
                            'startY': curve_shape['vertices'][v_index]['renderPointY']['abs'] +
                                      0.01 * curve_shape['vertices'][v_index]['renderPointY'][
                                          'rel'] * height + y,
                            'endX': curve_shape['vertices'][v_index + 1]['renderPointX']['abs'] +
                                    0.01 * curve_shape['vertices'][v_index + 1]['renderPointX'][
                                        'rel'] * width + x,
                            'endY': curve_shape['vertices'][v_index + 1]['renderPointY']['abs'] +
                                    0.01 * curve_shape['vertices'][v_index + 1]['renderPointY'][
                                        'rel'] * height + y}

                if 'basePoint1X' in list(curve_shape['vertices'][v_index].keys()):
                    element_ = {
                        'basePoint1X': curve_shape['vertices'][v_index]['basePoint1X']['abs'] +
                                       0.01 * curve_shape['vertices'][v_index]['basePoint1X'][
                                           'rel'] * width + x,
                        'basePoint1Y': curve_shape['vertices'][v_index]['basePoint1Y']['abs'] +
                                       0.01 * curve_shape['vertices'][v_index]['basePoint1Y'][
                                           'rel'] * height + y,
                        'basePoint2X': curve_shape['vertices'][v_index]['basePoint2X']['abs'] +
                                       0.01 * curve_shape['vertices'][v_index]['basePoint2X'][
                                           'rel'] * width + x,
                        'basePoint2Y': curve_shape['vertices'][v_index]['basePoint2Y']['abs'] +
                                       0.01 * curve_shape['vertices'][v_index]['basePoint2Y'][
                                           'rel'] * height + y}

                curve_features['curve'].append(element_)

            self.add_curve_to_scene(curve_features, z_order=z_order)

    def draw_rounded_rectangle(self, rectangle_shape, x, y, width, height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               offset_x, offset_y, slope, z_order):
        position_x = x
        position_y = y
        dimension_width = width
        dimension_height = height
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
                          0.01 * rectangle_shape['x']['rel'] * width
        if 'y' in list(rectangle_shape.keys()):
            position_y += rectangle_shape['y']['abs'] + \
                          0.01 * rectangle_shape['y']['rel'] * height
        if 'width' in list(rectangle_shape.keys()):
            dimension_width = rectangle_shape['width']['abs'] + \
                              0.01 * rectangle_shape['width']['rel'] * width
        if 'height' in list(rectangle_shape.keys()):
            dimension_height = rectangle_shape['height']['abs'] + \
                               0.01 * rectangle_shape['height']['rel'] * height
        if 'ratio' in list(rectangle_shape.keys()) and rectangle_shape['ratio'] > 0.0:
            if (width / height) <= rectangle_shape['ratio']:
                dimension_width = width
                dimension_height = width / rectangle_shape['ratio']
                position_y += 0.5 * (height - dimension_height)
            else:
                dimension_height = height
                dimension_width = rectangle_shape['ratio'] * height
                position_x += 0.5 * (width - dimension_width)
        if 'rx' in list(rectangle_shape.keys()):
            corner_radius = rectangle_shape['rx']['abs'] + \
                            0.01 * rectangle_shape['rx']['rel'] * 0.5 * (width + height)
        elif 'ry' in list(rectangle_shape.keys()):
            corner_radius = rectangle_shape['ry']['abs'] + \
                            0.01 * rectangle_shape['ry']['rel'] * 0.5 * (width + height)

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

    def draw_simple_rectangle(self, x, y, width, height,
                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                              offset_x, offset_y, slope, z_order):
        rectangle = Rectangle((x, y), width, height, slope * (180.0 / math.pi),
                              edgecolor=self.graph_info.find_color_value(stroke_color, False),
                              facecolor=self.graph_info.find_color_value(fill_color), fill=True,
                              linewidth=stroke_width, linestyle=stroke_dash_array,
                              zorder=z_order, antialiased=True)
        self.sbml_axes.add_patch(rectangle)

    def draw_ellipse(self, ellipse_shape, x, y, width, height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        # default features
        position_cx = x
        position_cy = y
        dimension_rx = 0.5 * width
        dimension_ry = 0.5 * height

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
                'rel'] * width
        if 'cy' in list(ellipse_shape.keys()):
            position_cy += ellipse_shape['cy']['abs'] + 0.01 * ellipse_shape['cy'][
                'rel'] * height
        if 'rx' in list(ellipse_shape.keys()):
            dimension_rx = ellipse_shape['rx']['abs'] + 0.01 * ellipse_shape['rx'][
                'rel'] * width
        if 'ry' in list(ellipse_shape.keys()):
            dimension_ry = ellipse_shape['ry']['abs'] + \
                           0.01 * ellipse_shape['ry']['rel'] * height
        if 'ratio' in list(ellipse_shape.keys()) and ellipse_shape['ratio'] > 0.0:
            if (width / height) <= ellipse_shape['ratio']:
                dimension_rx = 0.5 * width
                dimension_ry = (0.5 * width / ellipse_shape['ratio'])
            else:
                dimension_ry = 0.5 * height
                dimension_rx = ellipse_shape['ratio'] * 0.5 * height

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

    def draw_polygon(self, polygon_shape, x, y, width, height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
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
                                                ['renderPointX']['rel'] * width,
                                                polygon_shape['vertices'][v_index]
                                                ['renderPointY']['abs'] +
                                                0.01 * polygon_shape['vertices'][v_index]
                                                ['renderPointY']['rel'] * height]]), axis=0)

            if offset_x or offset_y:
                vertices[:, 0] += offset_x - width
                vertices[:, 1] += offset_y - 0.5 * height
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


    def draw_curve(self, curve, stroke_color, stroke_width, stroke_dash_array,
                   z_order):
        for v_index in range(len(curve)):
            vertices = [(curve[v_index]['startX'], curve[v_index]['startY'])]
            codes = [Path.MOVETO]
            if 'basePoint1X' in list(curve[v_index].keys()):
                vertices.append(
                    (curve[v_index]['basePoint1X'], curve[v_index]['basePoint1Y']))
                vertices.append(
                    (curve[v_index]['basePoint2X'], curve[v_index]['basePoint2Y']))
                codes.append(Path.CURVE4)
                codes.append(Path.CURVE4)
                codes.append(Path.CURVE4)
            else:
                codes.append(Path.LINETO)
            vertices.append((curve[v_index]['endX'], curve[v_index]['endY']))

            # draw a curve
            curve = PathPatch(Path(vertices, codes),
                              edgecolor=self.graph_info.find_color_value(stroke_color, False),
                              facecolor='none', linewidth=stroke_width, linestyle=stroke_dash_array,
                              capstyle='butt', zorder=z_order, antialiased=True)
            self.sbml_axes.add_patch(curve)

    def draw_text(self, x, y, width, height,
                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                   v_text_anchor, h_text_anchor, zorder):
        self.sbml_axes.text(x + 0.5 * width, y + 0.5 * height, plain_text,
                     color=font_color, fontfamily=font_family, fontsize=0.4 * font_size,
                     fontstyle=font_style, fontweight=font_weight,
                     va=v_text_anchor, ha=h_text_anchor, zorder=zorder)

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
