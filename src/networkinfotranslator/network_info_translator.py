from .imports.import_sbml import NetworkInfoImportFromSBMLModel
from .imports.import_network_editor import NetworkInfoImportFromNetworkEditor
from .exports.export_sbml import NetworkInfoExportToSBMLModel
from .exports.export_network_editor import NetworkInfoExportToNetworkEditor
from .exports.export_cytoscapejs import NetworkInfoExportToCytoscapeJs
from .exports.export_figure_matplotlib import NetworkInfoExportToMatPlotLib
from .exports.export_escher import NetworkInfoExportToEscher

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