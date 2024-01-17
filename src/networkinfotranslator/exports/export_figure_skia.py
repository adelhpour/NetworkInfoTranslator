from .export_figure_base import NetworkInfoExportToFigureBase
import webcolors
import skia


class NetworkInfoExportToSkia(NetworkInfoExportToFigureBase):
    def __init__(self):
        super().__init__()
        self.surface = None

    def reset(self):
        super().reset()

    def set_extents(self):
        self.surface = skia.Surface(int(self.graph_info.extents['maxX'] - self.graph_info.extents['minX'] + 50),
                                    int(self.graph_info.extents['maxY'] - self.graph_info.extents['minY']))

    def draw_simple_rectangle(self, x, y, width, height,
                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                              offset_x, offset_y, slope, z_order):
        with self.surface as canvas:
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.translate(abs(self.graph_info.extents['minX']) + offset_x,
                                 abs(self.graph_info.extents['minY']) + offset_y)
                canvas.rotate(slope * 180.0 / 3.141592653589793)
                rectangle = skia.Rect(x, y, x + width, y + height)
            else:
                rectangle = skia.Rect(abs(self.graph_info.extents['minX']) + x,
                                      abs(self.graph_info.extents['minY']) + y,
                                      abs(self.graph_info.extents['minX']) + x + width,
                                      abs(self.graph_info.extents['minY']) + y + height)
            paint = self.create_fill_paint(fill_color)
            canvas.drawRoundRect(rectangle, paint)
            paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            canvas.drawRoundRect(rectangle, paint)
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.rotate(-slope * 180.0 / 3.141592653589793)
                canvas.translate(-(abs(self.graph_info.extents['minX']) + offset_x),
                                 -(abs(self.graph_info.extents['minY']) + offset_y))

    def draw_rounded_rectangle(self, x, y, width, height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               corner_radius_x, corner_radius_y,
                               offset_x, offset_y, slope, z_order):
        with self.surface as canvas:
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.translate(abs(self.graph_info.extents['minX']) + offset_x,
                                 abs(self.graph_info.extents['minY']) + offset_y)
                canvas.rotate(slope * 180.0 / 3.141592653589793)
                rectangle = skia.Rect(x, y, x + width, y + height)
            else:
                rectangle = skia.Rect(abs(self.graph_info.extents['minX']) + x,
                                      abs(self.graph_info.extents['minY']) + y,
                                      abs(self.graph_info.extents['minX']) + x + width,
                                      abs(self.graph_info.extents['minY']) + y + height)
            paint = self.create_fill_paint(fill_color)
            canvas.drawRoundRect(rectangle, corner_radius_x, corner_radius_y, paint)
            paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            canvas.drawRoundRect(rectangle, corner_radius_x, corner_radius_y, paint)
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.rotate(-slope * 180.0 / 3.141592653589793)
                canvas.translate(-(abs(self.graph_info.extents['minX']) + offset_x),
                                 -(abs(self.graph_info.extents['minY']) + offset_y))

    def draw_ellipse(self, cx, cy, rx, ry,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        with self.surface as canvas:
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.translate(abs(self.graph_info.extents['minX']) + offset_x,
                                 abs(self.graph_info.extents['minY']) + offset_y)
                canvas.rotate(slope * 180.0 / 3.141592653589793)
                rectangle = skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)
            else:
                rectangle = skia.Rect(abs(self.graph_info.extents['minX']) + cx - rx,
                                      abs(self.graph_info.extents['minY']) + cy - ry,
                                      abs(self.graph_info.extents['minX']) + cx + rx,
                                      abs(self.graph_info.extents['minY']) + cy + ry)
            paint = self.create_fill_paint(fill_color)
            canvas.drawOval(rectangle, paint)
            paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            canvas.drawOval(rectangle, paint)
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.rotate(-slope * 180.0 / 3.141592653589793)
                canvas.translate(-(abs(self.graph_info.extents['minX']) + offset_x),
                                 -(abs(self.graph_info.extents['minY']) + offset_y))

    def draw_polygon(self, vertices, width, height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        with self.surface as canvas:
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.translate(abs(self.graph_info.extents['minX']) + offset_x,
                                 abs(self.graph_info.extents['minY']) + offset_y)
                canvas.rotate(slope * 180.0 / 3.141592653589793)
                path = skia.Path()
                path.moveTo(vertices[0][0] - width, vertices[0][1] - 0.5 * height)
                for i in range(1, len(vertices)):
                    path.lineTo(vertices[i][0] - width, vertices[i][1] - 0.5 * height)
                path.close()
            else:
                path = skia.Path()
                path.moveTo(abs(self.graph_info.extents['minX']) + vertices[0][0] - width,
                            abs(self.graph_info.extents['minY']) + vertices[0][1] - 0.5 * height)
                for i in range(1, len(vertices)):
                    path.lineTo(abs(self.graph_info.extents['minX']) + vertices[i][0] - width,
                                abs(self.graph_info.extents['minY']) + vertices[i][1] - 0.5 * height)
                path.close()

            paint = self.create_fill_paint(fill_color)
            canvas.drawPath(path, paint)
            paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            canvas.drawPath(path, paint)
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                canvas.rotate(-slope * 180.0 / 3.141592653589793)
                canvas.translate(-(abs(self.graph_info.extents['minX']) + offset_x),
                                 -(abs(self.graph_info.extents['minY']) + offset_y))

    def draw_curve(self, curve, stroke_color, stroke_width, stroke_dash_array,
                   z_order):
        with self.surface as canvas:
            for v_index in range(len(curve)):
                path = skia.Path()
                path.moveTo(abs(self.graph_info.extents['minX']) + curve[v_index]['startX'],
                            abs(self.graph_info.extents['minY']) + curve[v_index]['startY'])
                if "basePoint1X" in list(curve[v_index].keys()) and "basePoint1Y" in list(curve[v_index].keys()):
                    path.cubicTo(abs(self.graph_info.extents['minX']) + curve[v_index]['basePoint1X'],
                                 abs(self.graph_info.extents['minY']) + curve[v_index]['basePoint1Y'],
                                 abs(self.graph_info.extents['minX']) + curve[v_index]['basePoint2X'],
                                 abs(self.graph_info.extents['minY']) + curve[v_index]['basePoint2Y'],
                                 abs(self.graph_info.extents['minX']) + curve[v_index]['endX'],
                                 abs(self.graph_info.extents['minY']) + curve[v_index]['endY'])
                else:
                    path.lineTo(abs(self.graph_info.extents['minX']) + curve[v_index]['endX'],
                                abs(self.graph_info.extents['minY']) + curve[v_index]['endY'])
                paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
                canvas.drawPath(path, paint)

    def draw_text(self, x, y, width, height,
                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                   v_text_anchor, h_text_anchor, zorder):
        with self.surface as canvas:
            paint = self.create_text_paint(font_color)
            text_font = skia.Font(None, font_size)
            text_width = text_font.measureText(plain_text)
            text_height = text_font.getSize()
            text = skia.TextBlob(plain_text, text_font)
            canvas.drawTextBlob(text, abs(self.graph_info.extents['minX']) + x + 0.5 * width - 0.45 * text_width,
                                abs(self.graph_info.extents['minY']) + y + 0.5 * height + 0.4 * text_height, paint)

    def create_fill_paint(self, fill_color):
        return skia.Paint(Color=self.get_skia_color(fill_color), Style=skia.Paint.kFill_Style, AntiAlias=True)

    def create_border_paint(self, stroke_color, stroke_width, stroke_dash_array):
        if len(stroke_dash_array) and len(stroke_dash_array) % 2 == 0:
            return skia.Paint(Color=self.get_skia_color(stroke_color), Style=skia.Paint.kStroke_Style,
                               PathEffect=skia.DashPathEffect.Make(list(stroke_dash_array), 0.0),
                               StrokeWidth=stroke_width, AntiAlias=True)
        else:
            return skia.Paint(Color=self.get_skia_color(stroke_color), Style=skia.Paint.kStroke_Style,
                               StrokeWidth=stroke_width, AntiAlias=True)

    def create_text_paint(self, font_color):
        return skia.Paint(Color=self.get_skia_color(font_color), AntiAlias=True)

    def get_skia_color(self, color_name):
        rgb_color = webcolors.hex_to_rgb(self.graph_info.find_color_value(color_name, False))
        return skia.Color(rgb_color.red, rgb_color.green, rgb_color.blue)

    def export(self, file_directory="", file_name="", file_format=""):
        image = self.surface.makeImageSnapshot()
        image.save('output.jpg', skia.kJPEG)