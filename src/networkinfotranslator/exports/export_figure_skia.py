from .export_figure_base import NetworkInfoExportToFigureBase
import skia


class NetworkInfoExportToSkia(NetworkInfoExportToFigureBase):
    def __init__(self):
        super().__init__()
        self.surface = skia.Surface(1000, 1000)

    def reset(self):
        super().reset()

    def draw_simple_rectangle(self, x, y, width, height,
                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                              offset_x, offset_y, slope, z_order):


        with self.surface as canvas:
            rectangle = skia.Rect(abs(self.graph_info.extents['minX']) + x,
                                  abs(self.graph_info.extents['minY']) + y,
                                  abs(self.graph_info.extents['minX']) + x + width,
                                  abs(self.graph_info.extents['minY']) + y + height)
            paint = self.create_fill_paint(fill_color)
            canvas.drawRoundRect(rectangle, paint)
            paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            canvas.drawRoundRect(rectangle, paint)

    def draw_rounded_rectangle(self, x, y, width, height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               corner_radius_x, corner_radius_y,
                               offset_x, offset_y, slope, z_order):
        with self.surface as canvas:
            rectangle = skia.Rect(abs(self.graph_info.extents['minX']) + x,
                                  abs(self.graph_info.extents['minY']) + y,
                                  abs(self.graph_info.extents['minX']) + x + width,
                                  abs(self.graph_info.extents['minY']) + y + height)
            paint = self.create_fill_paint(fill_color)
            canvas.drawRoundRect(rectangle, corner_radius_x, corner_radius_y, paint)
            paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            canvas.drawRoundRect(rectangle, corner_radius_x, corner_radius_y, paint)

    def draw_polygon(self, vertices, width, height,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, z_order):
        #if offset_x or offset_y:
            #vertices[:, 0] += offset_x - width
            #vertices[:, 1] += offset_y - 0.5 * height

        with self.surface as canvas:
            path = skia.Path()
            path.moveTo(abs(self.graph_info.extents['minX']) + vertices[0][0],
                        abs(self.graph_info.extents['minY']) + vertices[0][1])
            for i in range(1, len(vertices)):
                path.lineTo(abs(self.graph_info.extents['minX']) + vertices[i][0],
                            abs(self.graph_info.extents['minY']) + vertices[i][1])
            path.close()
            paint = self.create_fill_paint(fill_color)
            canvas.translate(offset_x - width, offset_y - 0.5 * height)
            canvas.rotate(slope * 180.0 / 3.1415, offset_x - width, offset_y - 0.5 * height)
            canvas.drawPath(path, paint)
            paint = self.create_border_paint(stroke_color, stroke_width, stroke_dash_array)
            canvas.drawPath(path, paint)
            canvas.rotate(-(slope * 180.0 / 3.1415), offset_x - width, offset_y - 0.5 * height)
            canvas.translate(-(offset_x - width), -(offset_y - 0.5 * height))

    def draw_text(self, x, y, width, height,
                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                   v_text_anchor, h_text_anchor, zorder):
        with self.surface as canvas:
            paint = self.create_text_paint(font_color)
            text = skia.TextBlob(plain_text, skia.Font(None, 0.8 * font_size))
            canvas.drawTextBlob(text, abs(self.graph_info.extents['minX']) + x,
                                abs(self.graph_info.extents['minY']) + y, paint)

    def create_fill_paint(self, fill_color):
        if fill_color == "black":
            return skia.Paint(Color=skia.ColorBLACK, Style=skia.Paint.kFill_Style, AntiAlias=True)
        else:
            return skia.Paint(Color=skia.ColorWHITE, Style=skia.Paint.kFill_Style, AntiAlias=True)

    def create_border_paint(self, stroke_color, stroke_width, stroke_dash_array):
        if len(stroke_dash_array) and len(stroke_dash_array) % 2 == 0:
            return skia.Paint(Color=skia.ColorBLACK, Style=skia.Paint.kStroke_Style,
                               PathEffect=skia.DashPathEffect.Make(list(stroke_dash_array), 0.0),
                               StrokeWidth=stroke_width, AntiAlias=True)
        else:
            return skia.Paint(Color=skia.ColorBLACK, Style=skia.Paint.kStroke_Style,
                               StrokeWidth=stroke_width, AntiAlias=True)

    def create_text_paint(self, font_color):
        return skia.Paint(Color=skia.ColorBLACK, AntiAlias=True)

    def export(self, file_directory="", file_name="", file_format=""):
        image = self.surface.makeImageSnapshot()
        image.save('output.jpg', skia.kJPEG)