from .export_figure_base import NetworkInfoExportToFigureBase
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Polygon, Path, PathPatch
import matplotlib.transforms as plttransform
import matplotlib.cbook as cbook


class NetworkInfoExportToMatPlotLib(NetworkInfoExportToFigureBase):
    def __init__(self):
        self.sbml_figure, self.sbml_axes = plt.subplots()
        self.sbml_axes.invert_yaxis()
        super().__init__()

    def reset(self):
        super().reset()
        self.sbml_axes.clear()
        self.sbml_figure.set_size_inches(1.0, 1.0)

    def draw_image(self, bbox_x, bbox_y, bbox_width, bbox_height,
                   offset_x, offset_y, slope, z_order):
        with cbook.get_sample_data(href) as image_file:
            image = plt.imread(image_file)
            image_axes = self.sbml_axes.imshow(image)
            image_axes.set_extent([x, x + width, y + height, y])
            image_axes.set_zorder(z_order)
            if offset_x or offset_y:
                image_axes.set_transform(plttransform.Affine2D().
                                         rotate_around(offset_x, offset_y,
                                                       slope) + self.sbml_axes.transData)
            else:
                image_axes.set_transform(plttransform.Affine2D().
                                         rotate_around(x + 0.5 * width,
                                                       y + 0.5 * height,
                                                       slope) + self.sbml_axes.transData)

    def draw_rounded_rectangle(self, x, y, width, height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               corner_radius, offset_x, offset_y, slope, z_order):
        fancy_box = FancyBboxPatch((x, y), width, height,
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
                                    rotate_around(position_x + 0.5 * width,
                                                  position_y + 0.5 * height,
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

    def draw_ellipse(self, cx, cy, rx, ry,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        # add an ellipse to plot
        ellipse = Ellipse((cx, cy), 2 * rx, 2 * ry,
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
                                  rotate_around(cx, cy,
                                                slope) + self.sbml_axes.transData)
        self.sbml_axes.add_patch(ellipse)

    def draw_polygon(self, vertices, width, height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
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

    def export(self, file_directory="", file_name="", file_format=""):
        if len(self.sbml_axes.patches):
            self.sbml_axes.set_aspect('equal')
            self.sbml_figure.set_size_inches(max(1.0, (self.graph_info.extents['maxX'] -
                                                       self.graph_info.extents['minX']) / 72.0),
                                             max(1.0, (self.graph_info.extents['maxY'] -
                                                       self.graph_info.extents['minY']) / 72.0))
            plt.axis('equal')
            plt.axis('off')
            plt.tight_layout()

            self.sbml_figure.savefig(self.get_output_name(file_directory, file_name, file_format), transparent=True,
                                     dpi=300)
            plt.close('all')
