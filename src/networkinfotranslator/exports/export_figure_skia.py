from .export_figure_base import NetworkInfoExportToFigureBase
import skia


class NetworkInfoExportToSkia(NetworkInfoExportToFigureBase):
    def __init__(self):
        surface = skia.Surface(max(1.0, (self.graph_info.extents['maxX'] - self.graph_info.extents['minX']) / 72.0),
                                         max(1.0, (self.graph_info.extents['maxY'] - self.graph_info.extents['minY']) / 72.0))
        super().__init__()

    def reset(self):
        super().reset()
        self.surface.clear()
        self.surface.set_size(1.0, 1.0)
