from .export_figure_base import NetworkInfoExportToFigureBase
import webcolors
import skia


class NetworkInfoExportToSkia(NetworkInfoExportToFigureBase):
    def __init__(self):
        super().__init__()
        self.padding = 25

    def reset(self):
        super().reset()
        self.simple_rectangles = []
        self.rounded_rectangles = []
        self.ellipses = []
        self.polygons = []
        self.curves = []
        self.texts = []

    def draw_simple_rectangle(self, x, y, width, height,
                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                              offset_x, offset_y, slope, z_order):
        simple_rectangle = {}
        if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
            simple_rectangle['translate'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + offset_x,
                                             'y': abs(self.graph_info.extents['minY']) + self.padding + offset_y}
            simple_rectangle['rotate'] = slope * 180.0 / 3.141592653589793
            simple_rectangle['rectangle'] = skia.Rect(x, y, x + width, y + height)
        else:
            simple_rectangle['rectangle'] = skia.Rect(abs(self.graph_info.extents['minX']) + self.padding + x,
                                  abs(self.graph_info.extents['minY']) + self.padding + y,
                                  abs(self.graph_info.extents['minX']) + self.padding + x + width,
                                  abs(self.graph_info.extents['minY']) + self.padding + y + height)
        simple_rectangle['fill'] = self.create_fill_paint(fill_color)
        simple_rectangle['border'] = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self.simple_rectangles.append(simple_rectangle)

    def draw_rounded_rectangle(self, x, y, width, height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               corner_radius_x, corner_radius_y,
                               offset_x, offset_y, slope, z_order):
        rounded_rectangle = {}
        if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
            rounded_rectangle['translate'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + offset_x,
                                             'y': abs(self.graph_info.extents['minY']) + self.padding + offset_y}
            rounded_rectangle['rotate'] = slope * 180.0 / 3.141592653589793
            rounded_rectangle['rectangle'] = skia.Rect(x, y, x + width, y + height)
        else:
            rounded_rectangle['rectangle'] = skia.Rect(abs(self.graph_info.extents['minX']) + self.padding + x,
                                  abs(self.graph_info.extents['minY']) + self.padding + y,
                                  abs(self.graph_info.extents['minX']) + self.padding + x + width,
                                  abs(self.graph_info.extents['minY']) + self.padding + y + height)
        rounded_rectangle['border-radius'] = 0.5 * (corner_radius_x +  corner_radius_y)
        rounded_rectangle['fill'] = self.create_fill_paint(fill_color)
        rounded_rectangle['border'] = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self.rounded_rectangles.append(rounded_rectangle)

    def draw_ellipse(self, cx, cy, rx, ry,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        ellipse = {}
        if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
            ellipse['translate'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + offset_x,
                                              'y': abs(self.graph_info.extents['minY']) + self.padding + offset_y}
            ellipse['rotate'] = slope * 180.0 / 3.141592653589793
            ellipse['rectangle'] = skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)
        else:
            ellipse['rectangle'] = skia.Rect(abs(self.graph_info.extents['minX']) + self.padding + cx - rx,
                                  abs(self.graph_info.extents['minY']) + self.padding + cy - ry,
                                  abs(self.graph_info.extents['minX']) + self.padding + cx + rx,
                                  abs(self.graph_info.extents['minY']) + self.padding + cy + ry)
        ellipse['fill'] = self.create_fill_paint(fill_color)
        ellipse['border'] = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self.ellipses.append(ellipse)

    def draw_polygon(self, vertices, width, height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        polygon = {}
        if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
            polygon['translate'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + offset_x,
                                    'y': abs(self.graph_info.extents['minY']) + self.padding + offset_y}
            polygon['rotate'] = slope * 180.0 / 3.141592653589793
            polygon['move-to-vertex'] = {'x':  vertices[0][0] - width, 'y': vertices[0][1] - 0.5 * height}
            line_to_vertices = []
            for i in range(1, len(vertices)):
                line_to_vertices.append({'x': vertices[i][0] - width, 'y': vertices[i][1] - 0.5 * height})
            polygon['line-to-vertices'] = line_to_vertices
        else:
            polygon['move-to-vertex'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + vertices[0][0] - width,
                                         'y': abs(self.graph_info.extents['minY']) + self.padding + vertices[0][1] - 0.5 * height}
            for i in range(1, len(vertices)):
                line_to_vertices = []
                line_to_vertices.append({'x': abs(self.graph_info.extents['minX']) + self.padding + vertices[i][0] - width,
                                         'y': abs(self.graph_info.extents['minY']) + self.padding + vertices[i][1] - 0.5 * height})
                polygon['line-to-vertices'] = line_to_vertices

        polygon['fill'] = self.create_fill_paint(fill_color)
        polygon['border'] = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self.polygons.append(polygon)

    def draw_curve(self, curve, stroke_color, stroke_width, stroke_dash_array,
                   z_order):
        vertices = []
        for v_index in range(len(curve)):
            vertex = {'move-to': {'x': abs(self.graph_info.extents['minX']) + self.padding + curve[v_index]['startX'],
                                         'y': abs(self.graph_info.extents['minY']) + self.padding + curve[v_index]['startY']}}
            if "basePoint1X" in list(curve[v_index].keys()) and "basePoint1Y" in list(curve[v_index].keys()):
                vertex['cubic-to'] = {'b1x': abs(self.graph_info.extents['minX']) + self.padding + curve[v_index]['basePoint1X'],
                                            'b1y': abs(self.graph_info.extents['minY']) + self.padding + curve[v_index]['basePoint1Y'],
                                            'b2x': abs(self.graph_info.extents['minX']) + self.padding + curve[v_index]['basePoint2X'],
                                            'b2y': abs(self.graph_info.extents['minY']) + self.padding + curve[v_index]['basePoint2Y'],
                                            'x': abs(self.graph_info.extents['minX']) + self.padding + curve[v_index]['endX'],
                                            'y': abs(self.graph_info.extents['minY']) + self.padding + curve[v_index]['endY']}
            else:
                vertex['line-to'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + curve[v_index]['endX'],
                                     'y': abs(self.graph_info.extents['minY']) + self.padding + curve[v_index]['endY']}
            vertices.append(vertex)
        self.curves.append({'vertices': vertices,
                            'border': self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)})

    def draw_text(self, x, y, width, height,
                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                   v_text_anchor, h_text_anchor, zorder):
        text = {}
        text_font = skia.Font(None, font_size)
        while text_font.measureText(plain_text) > width:
            font_size = font_size - 1
            text_font = skia.Font(None, font_size)
        text_width = text_font.measureText(plain_text)
        text_height = text_font.getSize()
        text['text-paint'] = self.create_text_paint(font_color)
        text['text'] = skia.TextBlob(plain_text, text_font)
        text['x'] = abs(self.graph_info.extents['minX']) + self.padding + x + 0.5 * width - 0.5 * text_width
        text['y'] = abs(self.graph_info.extents['minY']) + self.padding + y + 0.5 * height + 0.4 * text_height
        self.texts.append(text)

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
        if file_format == "pdf":
            self._export_as_pdf(file_directory, file_name)
        else:
            self._export_as(file_directory, file_name, file_format)

    def _export_as_pdf(self, file_directory, file_name):
        stream = skia.FILEWStream(self.get_output_name(file_directory, file_name, "pdf"))
        with skia.PDF.MakeDocument(stream) as document:
            with document.page(int(self.graph_info.extents['maxX'] - self.graph_info.extents['minX']),
                               int(self.graph_info.extents['maxY'] - self.graph_info.extents['minY'])) as canvas:
                for simple_rectangle in self.simple_rectangles:
                    if 'translate' in list(simple_rectangle.keys()):
                        canvas.translate(simple_rectangle['translate']['x'], simple_rectangle['translate']['y'])
                        canvas.rotate(simple_rectangle['rotate'])
                    canvas.drawRoundRect(simple_rectangle["rectangle"], rounded_rectangle["border"])
                    canvas.drawRoundRect(simple_rectangle["rectangle"], rounded_rectangle["fill"])
                    if 'translate' in list(simple_rectangle.keys()):
                        canvas.rotate(-simple_rectangle['rotate'])
                        canvas.translate(-simple_rectangle['translate']['x'], -simple_rectangle['translate']['y'])
                for rounded_rectangle in self.rounded_rectangles:
                    if 'translate' in list(rounded_rectangle.keys()):
                        canvas.translate(rounded_rectangle['translate']['x'], rounded_rectangle['translate']['y'])
                        canvas.rotate(rounded_rectangle['rotate'])
                    canvas.drawRoundRect(rounded_rectangle["rectangle"], rounded_rectangle["border-radius"],
                                         rounded_rectangle["border-radius"], rounded_rectangle["border"])
                    canvas.drawRoundRect(rounded_rectangle["rectangle"], rounded_rectangle["border-radius"],
                                         rounded_rectangle["border-radius"], rounded_rectangle["fill"])
                    if 'translate' in list(rounded_rectangle.keys()):
                        canvas.rotate(-rounded_rectangle['rotate'])
                        canvas.translate(-rounded_rectangle['translate']['x'], -rounded_rectangle['translate']['y'])
                for ellipse in self.ellipses:
                    if 'translate' in list(ellipse.keys()):
                        canvas.translate(ellipse['translate']['x'], ellipse['translate']['y'])
                        canvas.rotate(ellipse['rotate'])
                    canvas.drawOval(ellipse["rectangle"], ellipse["border"])
                    canvas.drawOval(ellipse["rectangle"], ellipse["fill"])
                    if 'translate' in list(rounded_rectangle.keys()):
                        canvas.rotate(-ellipse['rotate'])
                        canvas.translate(-ellipse['translate']['x'], -ellipse['translate']['y'])
                for polygon in self.polygons:
                    if 'translate' in list(polygon.keys()):
                        canvas.translate(polygon['translate']['x'], polygon['translate']['y'])
                        canvas.rotate(polygon['rotate'])
                    path = skia.Path()
                    path.moveTo(polygon['move-to-vertex']['x'], polygon['move-to-vertex']['y'])
                    for vertex in polygon['line-to-vertices']:
                        path.lineTo(vertex['x'], vertex['y'])
                    path.close()
                    canvas.drawPath(path, polygon["border"])
                    canvas.drawPath(path, polygon["fill"])
                    if 'translate' in list(polygon.keys()):
                        canvas.rotate(-polygon['rotate'])
                        canvas.translate(-polygon['translate']['x'], -polygon['translate']['y'])
                for curve in self.curves:
                    for vertex in curve['vertices']:
                        path = skia.Path()
                        path.moveTo(vertex['move-to']['x'], vertex['move-to']['y'])
                        if 'cubic-to' in list(vertex.keys()):
                            path.cubicTo(vertex['cubic-to']['b1x'], vertex['cubic-to']['b1y'],
                                         vertex['cubic-to']['b2x'], vertex['cubic-to']['b2y'],
                                         vertex['cubic-to']['x'], vertex['cubic-to']['y'])
                        else:
                            path.lineTo(vertex['line-to']['x'], vertex['line-to']['y'])
                        canvas.drawPath(path, curve["border"])
                for text in self.texts:
                    canvas.drawTextBlob(text['text'], text['x'], text['y'], text['text-paint'])

    def _export_as(self, file_directory, file_name, file_format):
        surface = skia.Surface(int(self.graph_info.extents['maxX'] - self.graph_info.extents['minX'] + 2 * self.padding),
                                    int(self.graph_info.extents['maxY'] - self.graph_info.extents['minY'] + 2 * self.padding))
        with surface as canvas:
            for simple_rectangle in self.simple_rectangles:
                if 'translate' in list(simple_rectangle.keys()):
                    canvas.translate(simple_rectangle['translate']['x'], simple_rectangle['translate']['y'])
                    canvas.rotate(simple_rectangle['rotate'])
                canvas.drawRoundRect(simple_rectangle["rectangle"], rounded_rectangle["border"])
                canvas.drawRoundRect(simple_rectangle["rectangle"], rounded_rectangle["fill"])
                if 'translate' in list(simple_rectangle.keys()):
                    canvas.rotate(-simple_rectangle['rotate'])
                    canvas.translate(-simple_rectangle['translate']['x'], -simple_rectangle['translate']['y'])
            for rounded_rectangle in self.rounded_rectangles:
                if 'translate' in list(rounded_rectangle.keys()):
                    canvas.translate(rounded_rectangle['translate']['x'], rounded_rectangle['translate']['y'])
                    canvas.rotate(rounded_rectangle['rotate'])
                canvas.drawRoundRect(rounded_rectangle["rectangle"], rounded_rectangle["border-radius"],
                                     rounded_rectangle["border-radius"], rounded_rectangle["border"])
                canvas.drawRoundRect(rounded_rectangle["rectangle"], rounded_rectangle["border-radius"],
                                     rounded_rectangle["border-radius"], rounded_rectangle["fill"])
                if 'translate' in list(rounded_rectangle.keys()):
                    canvas.rotate(-rounded_rectangle['rotate'])
                    canvas.translate(-rounded_rectangle['translate']['x'], -rounded_rectangle['translate']['y'])
            for ellipse in self.ellipses:
                if 'translate' in list(ellipse.keys()):
                    canvas.translate(ellipse['translate']['x'], ellipse['translate']['y'])
                    canvas.rotate(ellipse['rotate'])
                canvas.drawOval(ellipse["rectangle"], ellipse["border"])
                canvas.drawOval(ellipse["rectangle"], ellipse["fill"])
                if 'translate' in list(rounded_rectangle.keys()):
                    canvas.rotate(-ellipse['rotate'])
                    canvas.translate(-ellipse['translate']['x'], -ellipse['translate']['y'])
            for polygon in self.polygons:
                if 'translate' in list(polygon.keys()):
                    canvas.translate(polygon['translate']['x'], polygon['translate']['y'])
                    canvas.rotate(polygon['rotate'])
                path = skia.Path()
                path.moveTo(polygon['move-to-vertex']['x'], polygon['move-to-vertex']['y'])
                for vertex in polygon['line-to-vertices']:
                    path.lineTo(vertex['x'], vertex['y'])
                path.close()
                canvas.drawPath(path, polygon["border"])
                canvas.drawPath(path, polygon["fill"])
                if 'translate' in list(polygon.keys()):
                    canvas.rotate(-polygon['rotate'])
                    canvas.translate(-polygon['translate']['x'], -polygon['translate']['y'])
            for curve in self.curves:
                for vertex in curve['vertices']:
                    path = skia.Path()
                    path.moveTo(vertex['move-to']['x'], vertex['move-to']['y'])
                    if 'cubic-to' in list(vertex.keys()):
                        path.cubicTo(vertex['cubic-to']['b1x'], vertex['cubic-to']['b1y'],
                                     vertex['cubic-to']['b2x'], vertex['cubic-to']['b2y'],
                                     vertex['cubic-to']['x'], vertex['cubic-to']['y'])
                    else:
                        path.lineTo(vertex['line-to']['x'], vertex['line-to']['y'])
                    canvas.drawPath(path, curve["border"])
            for text in self.texts:
                canvas.drawTextBlob(text['text'], text['x'], text['y'], text['text-paint'])

        image = surface.makeImageSnapshot()
        if file_format == "jpg":
            image.save(self.get_output_name(file_directory, file_name, "jpg"), skia.kJPEG)
        else:
            image.save(self.get_output_name(file_directory, file_name, "png"), skia.kPNG)
