from .imports.import_sbml import NetworkInfoImportFromSBMLModel
from .imports.import_network_editor import NetworkInfoImportFromNetworkEditor
from .exports.export_sbml import NetworkInfoExportToSBMLModel
from .exports.export_network_editor import NetworkInfoExportToNetworkEditor
from .exports.export_cytoscapejs import NetworkInfoExportToCytoscapeJs
from .exports.export_figure_matplotlib import NetworkInfoExportToMatPlotLib
from .exports.export_figure_skia import NetworkInfoExportToSkia
from .exports.export_escher import NetworkInfoExportToEscher

def import_sbml_export_figure(import_file, export_file_directory="", export_file_name="", export_file_format=""):
    import_from_sbml = NetworkInfoImportFromSBMLModel()
    import_from_sbml.extract_info(import_file)
    export_to_figure = NetworkInfoExportToSkia()
    export_to_figure.extract_graph_info(import_from_sbml)
    export_to_figure.export(export_file_directory, export_file_name, export_file_format)


def import_sbml_export_pil_image(import_file):
    import_from_sbml = NetworkInfoImportFromSBMLModel()
    import_from_sbml.extract_info(import_file)
    export_to_figure = NetworkInfoExportToSkia()
    export_to_figure.extract_graph_info(import_from_sbml)
    return export_to_figure.export_as_pil_image()

"""
sbml_graph_info = NetworkInfoImportFromNetworkEditor()
sbml_graph_info.extract_info("/Users/home/Downloads/Model.json")
sbml_export = NetworkInfoExportToMatPlotLib()
sbml_export.extract_graph_info(sbml_graph_info)
sbml_export.export("/Users/home/Downloads/Model.json")

sbml_graph_info = NetworkInfoImportFromNetworkEditor()
f = open("/Users/home/Downloads/network7.json")
sbml_graph_info.extract_info(json.load(f))
sbml_export = NetworkInfoExportToSBMLModel()
sbml_export.extract_graph_info(sbml_graph_info)
sbml_export.export("/Users/home/Downloads/Model.xml")
"""