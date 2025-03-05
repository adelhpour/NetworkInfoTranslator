from .export_figure_base import NetworkInfoExportToFigureBase
import skia
import math
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

    def _get_layer(self, layer_index, sublayer_index=0):
        for layer in self.layers:
            if layer_index == layer.layer_index:
                for sub_layer in layer.sub_layers:
                    if sublayer_index == sub_layer.sublayer_index:
                        return sub_layer
                new_sub_layer = SubLayer(sublayer_index)
                layer.sub_layers.append(new_sub_layer)
        new_layer = Layer(layer_index)
        new_sub_layer = SubLayer(sublayer_index)
        new_layer.sub_layers.append(new_sub_layer)
        self.layers.append(new_layer)
        return new_sub_layer

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
                              offset_x, offset_y, slope, layer, sublayer):
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
        self._get_layer(layer, sublayer).simple_rectangles.append(simple_rectangle)

    def draw_rounded_rectangle(self, x, y, width, height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               corner_radius_x, corner_radius_y,
                               offset_x, offset_y, slope, layer, sublayer):
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
        self._get_layer(layer, sublayer).rounded_rectangles.append(rounded_rectangle)

    def draw_ellipse(self, cx, cy, rx, ry,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, layer, sublayer):
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
        ellipse['fill'] = self._create_fill_paint(fill_color, ellipse['rectangle'].x(),
                                                 ellipse['rectangle'].y(),
                                                 ellipse['rectangle'].width(),
                                                 ellipse['rectangle'].height())
        ellipse['border'] = self._create_border_paint(stroke_color, stroke_width, stroke_dash_array)
        self._get_layer(layer, sublayer).ellipses.append(ellipse)

    def draw_polygon(self, vertices,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, layer, sublayer):
        if len(vertices):
            polygon = {}
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                polygon['translate'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + offset_x,
                                        'y': abs(self.graph_info.extents['minY']) + self.padding + offset_y}
                polygon['rotate'] = slope * 180.0 / math.pi
                polygon['move-to-vertex'] = {'x':  vertices[0][0], 'y': vertices[0][1]}
                line_to_vertices = []
                for i in range(1, len(vertices)):
                    line_to_vertices.append({'x': vertices[i][0], 'y': vertices[i][1]})
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
            self._get_layer(layer, sublayer).polygons.append(polygon)

    def draw_curve(self, curve_points, stroke_color, stroke_width, stroke_dash_array, offset_x, offset_y, slope, layer, sublayer):
        if len(curve_points):
            curve = {}
            horziontal_offset = 0.0
            vertical_offset = 0.0
            if abs(offset_x) > 0.001 or abs(offset_y) > 0.001:
                curve['translate'] = {'x': abs(self.graph_info.extents['minX']) + self.padding + offset_x,
                                        'y': abs(self.graph_info.extents['minY']) + self.padding + offset_y}
                curve['rotate'] = slope * 180.0 / math.pi
            else:
                horziontal_offset = self.padding
                vertical_offset = self.padding
            vertices = []
            for i in range(len(curve_points)):
                vertex = {'startX': curve_points[i]['startX'] + horziontal_offset, 'startY': curve_points[i]['startY'] + vertical_offset,
                            'endX': curve_points[i]['endX'] + horziontal_offset, 'endY': curve_points[i]['endY'] + vertical_offset}
                if 'basePoint1X' in list(curve_points[i].keys()):
                    vertex['basePoint1X'] = curve_points[i]['basePoint1X'] + horziontal_offset
                else:
                    vertex['basePoint1X'] = curve_points[i]['startX'] + horziontal_offset
                if 'basePoint1Y' in list(curve_points[i].keys()):
                    vertex['basePoint1Y'] = curve_points[i]['basePoint1Y'] + vertical_offset
                else:
                    vertex['basePoint1Y'] = curve_points[i]['startY'] + vertical_offset
                if 'basePoint2X' in list(curve_points[i].keys()):
                    vertex['basePoint2X'] = curve_points[i]['basePoint2X'] + horziontal_offset
                else:
                    vertex['basePoint2X'] = curve_points[i]['endX'] + horziontal_offset
                if 'basePoint2Y' in list(curve_points[i].keys()):
                    vertex['basePoint2Y'] = curve_points[i]['basePoint2Y'] + vertical_offset
                else:
                    vertex['basePoint2Y'] = curve_points[i]['endY'] + vertical_offset
                vertices.append(vertex)
            curve['vertices'] = vertices
            curve['border'] = self._create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            self._get_layer(layer, sublayer).curves.append(curve)

    def draw_text(self, x, y, width, height,
                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                   v_text_anchor, h_text_anchor, layer, sublayer):
        text = {}
        text_font = skia.Font(None, font_size)
        while text_font.measureText(plain_text) > abs(width):
            font_size = font_size - 1
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
        text_width = text_font.measureText(plain_text)
        text_height = text_font.getSize()
        text['text-paint'] = self._create_text_paint(font_color)
        text['text'] = skia.TextBlob(plain_text, text_font)
        text['x'] = (abs(self.graph_info.extents['minX']) + self.padding + x +
                     self._text_horizontal_adjustment_padding(h_text_anchor, text_width, width))
        text['y'] = abs(self.graph_info.extents['minY']) + self.padding + y + self._text_vertical_adjustment_padding(v_text_anchor, text_height, height)
        self._get_layer(layer, sublayer).texts.append(text)

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
            paint = skia.Paint(Color=self._get_skia_color(stroke_color), Style=skia.Paint.kStroke_Style,
                               PathEffect=skia.DashPathEffect.Make(list(stroke_dash_array), 0.0),
                               StrokeWidth=stroke_width, AntiAlias=True)
            paint.setStrokeCap(skia.Paint.kRound_Cap)
            return paint
        else:
            paint = skia.Paint(Color=self._get_skia_color(stroke_color), Style=skia.Paint.kStroke_Style,
                               StrokeWidth=stroke_width, AntiAlias=True)
            paint.setStrokeCap(skia.Paint.kRound_Cap)
            return paint

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
                                                  radius=0.01 * width * gradient['features']['radius']['abs'] + 0.01 * height * gradient['features']['radius']['rel'],
                                                  colors=stop_colors,
                                                  positions=stop_positions)

    def _get_skia_color(self, color_name):
        rgb_color = ImageColor.getcolor(self.graph_info.find_color_value(color_name, False), mode="RGBA")
        return skia.Color(rgb_color[0], rgb_color[1], rgb_color[2], rgb_color[3])

    def _export_as_pdf(self, file_name):
        stream = skia.FILEWStream(file_name)
        with skia.PDF.MakeDocument(stream) as document:
            with document.page(int(self.graph_info.extents['maxX'] - self.graph_info.extents['minX']) + + 2 * self.padding,
                               int(self.graph_info.extents['maxY'] - self.graph_info.extents['minY']) + + 2 * self.padding) as canvas:
                canvas.drawRect(self.background_canvas['rectangle'], self.background_canvas['fill'])
                self.sort_layers(self.layers)
                for layer in self.layers:
                    for sublayer in layer.sub_layers:
                        for simple_rectangle in sublayer.simple_rectangles:
                            if 'translate' in list(simple_rectangle.keys()):
                                canvas.translate(simple_rectangle['translate']['x'], simple_rectangle['translate']['y'])
                                canvas.rotate(simple_rectangle['rotate'])
                            canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["border"])
                            canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["fill"])
                            if 'translate' in list(simple_rectangle.keys()):
                                canvas.rotate(-simple_rectangle['rotate'])
                                canvas.translate(-simple_rectangle['translate']['x'], -simple_rectangle['translate']['y'])
                        for rounded_rectangle in sublayer.rounded_rectangles:
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
                        for ellipse in sublayer.ellipses:
                            if 'translate' in list(ellipse.keys()):
                                canvas.translate(ellipse['translate']['x'], ellipse['translate']['y'])
                                canvas.rotate(ellipse['rotate'])
                            canvas.drawOval(ellipse["rectangle"], ellipse["border"])
                            canvas.drawOval(ellipse["rectangle"], ellipse["fill"])
                            if 'translate' in list(ellipse.keys()):
                                canvas.rotate(-ellipse['rotate'])
                                canvas.translate(-ellipse['translate']['x'], -ellipse['translate']['y'])
                        for polygon in sublayer.polygons:
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
                        for curve in sublayer.curves:
                            if 'translate' in list(curve.keys()):
                                canvas.translate(curve['translate']['x'], curve['translate']['y'])
                                canvas.rotate(curve['rotate'])
                            for vertex in curve['vertices']:
                                path = skia.Path()
                                path.moveTo(vertex['startX'], vertex['startY'])
                                path.cubicTo(vertex['basePoint1X'], vertex['basePoint1Y'],
                                             vertex['basePoint2X'], vertex['basePoint2Y'],
                                             vertex['endX'], vertex['endY'])
                                canvas.drawPath(path, curve["border"])
                            if 'translate' in list(curve.keys()):
                                canvas.rotate(-curve['rotate'])
                                canvas.translate(-curve['translate']['x'], -curve['translate']['y'])
                        for text in sublayer.texts:
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
                for sublayer in layer.sub_layers:
                    for simple_rectangle in sublayer.simple_rectangles:
                        if 'translate' in list(simple_rectangle.keys()):
                            canvas.translate(simple_rectangle['translate']['x'], simple_rectangle['translate']['y'])
                            canvas.rotate(simple_rectangle['rotate'])
                        canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["border"])
                        canvas.drawRect(simple_rectangle["rectangle"], simple_rectangle["fill"])
                        if 'translate' in list(simple_rectangle.keys()):
                            canvas.rotate(-simple_rectangle['rotate'])
                            canvas.translate(-simple_rectangle['translate']['x'], -simple_rectangle['translate']['y'])
                    for rounded_rectangle in sublayer.rounded_rectangles:
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
                    for ellipse in sublayer.ellipses:
                        if 'translate' in list(ellipse.keys()):
                            canvas.translate(ellipse['translate']['x'], ellipse['translate']['y'])
                            canvas.rotate(ellipse['rotate'])
                        canvas.drawOval(ellipse["rectangle"], ellipse["border"])
                        canvas.drawOval(ellipse["rectangle"], ellipse["fill"])
                        if 'translate' in list(ellipse.keys()):
                            canvas.rotate(-ellipse['rotate'])
                            canvas.translate(-ellipse['translate']['x'], -ellipse['translate']['y'])
                    for polygon in sublayer.polygons:
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
                    for curve in sublayer.curves:
                        if 'translate' in list(curve.keys()):
                            canvas.translate(curve['translate']['x'], curve['translate']['y'])
                            canvas.rotate(curve['rotate'])
                        for vertex in curve['vertices']:
                            path = skia.Path()
                            path.moveTo(vertex['startX'], vertex['startY'])
                            path.cubicTo(vertex['basePoint1X'], vertex['basePoint1Y'],
                                         vertex['basePoint2X'], vertex['basePoint2Y'],
                                         vertex['endX'], vertex['endY'])
                            canvas.drawPath(path, curve["border"])
                        if 'translate' in list(curve.keys()):
                            canvas.rotate(-curve['rotate'])
                            canvas.translate(-curve['translate']['x'], -curve['translate']['y'])
                    for text in sublayer.texts:
                        canvas.drawTextBlob(text['text'], text['x'], text['y'], text['text-paint'])

        return surface.makeImageSnapshot()


class Layer:
    def __init__(self, layer_index):
        self.layer_index = layer_index
        self.sub_layers = []

class SubLayer:
    def __init__(self, sublayer_index):
        self.sublayer_index = sublayer_index
        self.simple_rectangles = []
        self.rounded_rectangles = []
        self.ellipses = []
        self.polygons = []
        self.curves = []
        self.texts = []