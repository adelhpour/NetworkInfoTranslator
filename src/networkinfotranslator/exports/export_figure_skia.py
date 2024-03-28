from .export_figure_base import NetworkInfoExportToFigureBase
import skia
from PIL import Image as PIL_Image
from PIL import ImageColor


class NetworkInfoExportToSkia(NetworkInfoExportToFigureBase):
    def __init__(self):
        super().__init__()
        self.padding = 25
        self.background_canvas = {}
        self.layers = []

    def reset(self):
        super().reset()
        self.background_canvas = {}
        self.layers = []

    def _get_layer(self, layer_index):
        for layer in self.layers:
            if layer_index == layer.layer_index:
                return layer
        new_layer = Layer(layer_index)
        self.layers.append(new_layer)
        return new_layer

    @staticmethod
    def sort_layers(layers):
        layers.sort(key=lambda x: x.layer_index)

    def draw_background_canvas(self, background_color):
        self.background_canvas['rectangle'] = skia.Rect(self.graph_info.extents['minX'] - self.padding,
                                  self.graph_info.extents['minY'] - self.padding,
                                  abs(self.graph_info.extents['minX']) + 2 * self.padding + self.graph_info.extents['maxX'] - self.graph_info.extents['minX'],
                                  abs(self.graph_info.extents['minY']) + 2 * self.padding + self.graph_info.extents['maxY'] - self.graph_info.extents['minY'])
        self.background_canvas['fill'] = self._create_fill_paint(background_color)

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
        simple_rectangle['fill'] = self._create_fill_paint(fill_color, simple_rectangle['rectangle'].x(),
                                                           simple_rectangle['rectangle'].y(),
                                                           simple_rectangle['rectangle'].width(),
                                                           simple_rectangle['rectangle'].height())
        simple_rectangle['border'] = self._create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self._get_layer(z_order).simple_rectangles.append(simple_rectangle)

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
        rounded_rectangle['fill'] = self._create_fill_paint(fill_color, rounded_rectangle['rectangle'].x(),
                                                            rounded_rectangle['rectangle'].y(),
                                                            rounded_rectangle['rectangle'].width(),
                                                            rounded_rectangle['rectangle'].height())
        rounded_rectangle['border'] = self._create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self._get_layer(z_order).rounded_rectangles.append(rounded_rectangle)

    def draw_ellipse(self, cx, cy, rx, ry,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        ellipse = {}
        if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
            ellipse['translate'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + offset_x,
                                              'y': abs(self.graph_info.extents['minY']) + self.padding + offset_y}
            ellipse['rotate'] = slope * 180.0 / 3.141592653589793
            cx -= offset_x
            cy -= offset_y
            ellipse['rectangle'] = skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)
        else:
            ellipse['rectangle'] = skia.Rect(abs(self.graph_info.extents['minX']) + self.padding + cx - rx,
                                  abs(self.graph_info.extents['minY']) + self.padding + cy - ry,
                                  abs(self.graph_info.extents['minX']) + self.padding + cx + rx,
                                  abs(self.graph_info.extents['minY']) + self.padding + cy + ry)
        ellipse['fill'] = self._create_fill_paint(fill_color, ellipse['rectangle'].x(),
                                                 ellipse['rectangle'].y(),
                                                 ellipse['rectangle'].width(),
                                                 ellipse['rectangle'].height())
        ellipse['border'] = self._create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self._get_layer(z_order).ellipses.append(ellipse)

    def draw_polygon(self, vertices, width, height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        if len(vertices):
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
                polygon['move-to-vertex'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + vertices[0][0],
                                             'y': abs(self.graph_info.extents['minY']) + self.padding + vertices[0][1]}
                line_to_vertices = []
                for i in range(1, len(vertices)):
                    line_to_vertices.append({'x': abs(self.graph_info.extents['minX']) + self.padding + vertices[i][0],
                                             'y': abs(self.graph_info.extents['minY']) + self.padding + vertices[i][1]})
                polygon['line-to-vertices'] = line_to_vertices

            polygon['fill'] = self._create_fill_paint(fill_color)
            polygon['border'] = self._create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            self._get_layer(z_order).polygons.append(polygon)

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
        self._get_layer(z_order).curves.append({'vertices': vertices,
                            'border': self._create_border_paint(stroke_color, stroke_width, stroke_dash_array)})

    def draw_text(self, x, y, width, height,
                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                   v_text_anchor, h_text_anchor, z_order):
        text = {}
        text_font = skia.Font(None, font_size)
        if font_weight == "bold":
            if font_style == "italic":
                text_font = skia.Font(skia.Typeface(font_family, skia.FontStyle().BoldItalic()), font_size)
            else:
                text_font = skia.Font(skia.Typeface(font_family, skia.FontStyle().Bold()), font_size)
        else:
            if font_style == "italic":
                text_font = skia.Font(skia.Typeface(font_family, skia.FontStyle.Italic()), font_size)
            else:
                text_font = skia.Font(skia.Typeface(font_family, skia.FontStyle.Normal()), font_size)
        while text_font.measureText(plain_text) > width:
            font_size = font_size - 1
            text_font = skia.Font(None, font_size)
        text_width = text_font.measureText(plain_text)
        text_height = text_font.getSize()
        text['text-paint'] = self._create_text_paint(font_color)
        text['text'] = skia.TextBlob(plain_text, text_font)
        text['x'] = (abs(self.graph_info.extents['minX']) + self.padding + x +
                     self._text_horizontal_adjustment_padding(h_text_anchor, text_width, width))
        text['y'] = abs(self.graph_info.extents['minY']) + self.padding + y + self._text_vertical_adjustment_padding(v_text_anchor, text_height, height)
        self._get_layer(z_order).texts.append(text)

    def _text_horizontal_adjustment_padding(self, h_text_anchor, text_width, width):
        if h_text_anchor == "left":
            return 0.0
        elif h_text_anchor == "right":
            return width - text_width
        elif h_text_anchor == "center":
            return 0.5 * width - 0.5 * text_width

        return 0.0

    def _text_vertical_adjustment_padding(self, v_text_anchor, text_height, height):
        if v_text_anchor == "top":
            return height - text_height + 0.4 * text_height
        elif v_text_anchor == "bottom":
            return height - 0.1 * text_height
        elif v_text_anchor == "center":
            return 0.5 * height + 0.4 * text_height

        return 0.0

    def export(self, file_name=""):
        if file_name.split(".")[-1] == "pdf":
            self._export_as_pdf(file_name)
        else:
            self._export_as(file_name)

    def export_as_pil_image(self):
        return PIL_Image.fromarray(self._get_image().convert(alphaType=skia.kUnpremul_AlphaType, colorType=skia.kRGB_888x_ColorType))

    def _create_fill_paint(self, fill_color, x=0.0, y=0.0, width=0.0, height=0.0):
        gradient = self.graph_info.find_gradient(fill_color)
        if gradient:
            return skia.Paint(Shader=self._get_skia_gradient_shader(gradient, x, y, width, height), AntiAlias=True)
        else:
            return skia.Paint(Color=self._get_skia_color(fill_color), Style=skia.Paint.kFill_Style, AntiAlias=True)

    def _create_border_paint(self, stroke_color, stroke_width, stroke_dash_array):
        if len(stroke_dash_array) and len(stroke_dash_array) % 2 == 0:
            return skia.Paint(Color=self._get_skia_color(stroke_color), Style=skia.Paint.kStroke_Style,
                               PathEffect=skia.DashPathEffect.Make(list(stroke_dash_array), 0.0),
                               StrokeWidth=stroke_width, AntiAlias=True)
        else:
            return skia.Paint(Color=self._get_skia_color(stroke_color), Style=skia.Paint.kStroke_Style,
                               StrokeWidth=stroke_width, AntiAlias=True)

    def _create_text_paint(self, font_color):
        return skia.Paint(Color=self._get_skia_color(font_color), AntiAlias=True)

    def _get_skia_gradient_shader(self, gradient, x, y, width, height):
        stop_colors = []
        stop_positions = []
        for stop in gradient['features']['stops']:
            if 'color' in list(stop.keys()):
                stop_colors.append(self._get_skia_color((stop['color'])))
            else:
                stop_colors.append("#ffffff")
            if 'offset' in list(stop.keys()):
                stop_positions.append(0.01 * stop['offset']['rel'])
            else:
                stop_positions.append(0.0)
        if gradient['features']['type'] == "linear":
            return skia.GradientShader.MakeLinear(points=[(x + 0.01 * width * gradient['features']['start']['x']['rel'],
                                                           y + 0.01 * height * gradient['features']['start']['y']['rel']),
                                                          (x + 0.01 * width * gradient['features']['end']['x']['rel'],
                                                           y + 0.01 * height * gradient['features']['end']['y']['rel'])],
                                                  colors=stop_colors,
                                                  positions=stop_positions)
        else:
            return skia.GradientShader.MakeRadial(center=(x + 0.01 * width * gradient['features']['center']['x']['rel'],
                                                          y + 0.01 * height * gradient['features']['center']['y']['rel']),
                                                  radius=0.01 * width * gradient['features']['radius']['rel'],
                                                  colors=stop_colors,
                                                  positions=stop_positions)

    def _get_skia_color(self, color_name):
        rgb_color = ImageColor.getrgb(self.graph_info.find_color_value(color_name, False))
        return skia.Color(rgb_color[0], rgb_color[1], rgb_color[2])

    def _export_as_pdf(self, file_name):
        stream = skia.FILEWStream(file_name)
        with skia.PDF.MakeDocument(stream) as document:
            with document.page(int(self.graph_info.extents['maxX'] - self.graph_info.extents['minX']) + + 2 * self.padding,
                               int(self.graph_info.extents['maxY'] - self.graph_info.extents['minY']) + + 2 * self.padding) as canvas:
                canvas.drawRect(self.background_canvas['rectangle'], self.background_canvas['fill'])
                self.sort_layers(self.layers)
                for layer in self.layers:
                    for simple_rectangle in layer.simple_rectangles:
                        if 'translate' in list(simple_rectangle.keys()):
                            canvas.translate(simple_rectangle['translate']['x'], simple_rectangle['translate']['y'])
                            canvas.rotate(simple_rectangle['rotate'])
                        canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["border"])
                        canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["fill"])
                        if 'translate' in list(simple_rectangle.keys()):
                            canvas.rotate(-simple_rectangle['rotate'])
                            canvas.translate(-simple_rectangle['translate']['x'], -simple_rectangle['translate']['y'])
                    for rounded_rectangle in layer.rounded_rectangles:
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
                    for ellipse in layer.ellipses:
                        if 'translate' in list(ellipse.keys()):
                            canvas.translate(ellipse['translate']['x'], ellipse['translate']['y'])
                            canvas.rotate(ellipse['rotate'])
                        canvas.drawOval(ellipse["rectangle"], ellipse["border"])
                        canvas.drawOval(ellipse["rectangle"], ellipse["fill"])
                        if 'translate' in list(ellipse.keys()):
                            canvas.rotate(-ellipse['rotate'])
                            canvas.translate(-ellipse['translate']['x'], -ellipse['translate']['y'])
                    for polygon in layer.polygons:
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
                    for curve in layer.curves:
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
                    for text in layer.texts:
                        canvas.drawTextBlob(text['text'], text['x'], text['y'], text['text-paint'])

    def _export_as(self, file_name):
        image = self._get_image()
        if file_name.split(".")[-1] == "jpg":
            image.save(file_name, skia.kJPEG)
        else:
            image.save(file_name, skia.kPNG)

    def _get_image(self):
        surface = skia.Surface(
            int(self.graph_info.extents['maxX'] - self.graph_info.extents['minX'] + 2 * self.padding),
            int(self.graph_info.extents['maxY'] - self.graph_info.extents['minY'] + 2 * self.padding))
        with surface as canvas:
            canvas.drawRect(self.background_canvas['rectangle'], self.background_canvas['fill'])
            self.sort_layers(self.layers)
            for layer in self.layers:
                for simple_rectangle in layer.simple_rectangles:
                    if 'translate' in list(simple_rectangle.keys()):
                        canvas.translate(simple_rectangle['translate']['x'], simple_rectangle['translate']['y'])
                        canvas.rotate(simple_rectangle['rotate'])
                    canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["border"])
                    canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["fill"])
                    if 'translate' in list(simple_rectangle.keys()):
                        canvas.rotate(-simple_rectangle['rotate'])
                        canvas.translate(-simple_rectangle['translate']['x'], -simple_rectangle['translate']['y'])
                for rounded_rectangle in layer.rounded_rectangles:
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
                for ellipse in layer.ellipses:
                    if 'translate' in list(ellipse.keys()):
                        canvas.translate(ellipse['translate']['x'], ellipse['translate']['y'])
                        canvas.rotate(ellipse['rotate'])
                    canvas.drawOval(ellipse["rectangle"], ellipse["border"])
                    canvas.drawOval(ellipse["rectangle"], ellipse["fill"])
                    if 'translate' in list(ellipse.keys()):
                        canvas.rotate(-ellipse['rotate'])
                        canvas.translate(-ellipse['translate']['x'], -ellipse['translate']['y'])
                for polygon in layer.polygons:
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
                for curve in layer.curves:
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
                for text in layer.texts:
                    canvas.drawTextBlob(text['text'], text['x'], text['y'], text['text-paint'])

        return surface.makeImageSnapshot()


class Layer:
    def __init__(self, layer_index):
        self.layer_index = layer_index
        self.simple_rectangles = []
        self.rounded_rectangles = []
        self.ellipses = []
        self.polygons = []
        self.curves = []
        self.texts = []