from .imports.import_sbml import NetworkInfoImportFromSBMLModel
from .imports.import_network_editor import NetworkInfoImportFromNetworkEditor
from .exports.export_sbml import NetworkInfoExportToSBMLModel
from .exports.export_network_editor import NetworkInfoExportToNetworkEditor
from .exports.export_cytoscapejs import NetworkInfoExportToCytoscapeJs
from .exports.export_figure_skia import NetworkInfoExportToSkia
from .exports.export_escher import NetworkInfoExportToEscher


def import_sbml_export_figure(import_file, file_name=""):
    import_from_sbml = NetworkInfoImportFromSBMLModel()
    import_from_sbml.extract_info(import_file)
    export_to_figure = NetworkInfoExportToSkia()
    export_to_figure.extract_graph_info(import_from_sbml)
    export_to_figure.export(file_name)


def import_sbml_export_pil_image(import_file):
    import_from_sbml = NetworkInfoImportFromSBMLModel()
    import_from_sbml.extract_info(import_file)
    export_to_figure = NetworkInfoExportToSkia()
    export_to_figure.extract_graph_info(import_from_sbml)
    return export_to_figure.export_as_pil_image()