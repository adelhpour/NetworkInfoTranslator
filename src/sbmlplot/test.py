import sbmlplot
import json

sbml_graph_info_from_sbml_model = sbmlplot.SBMLGraphInfoImportFromSBMLModel()
sbml_graph_info_from_sbml_model.extract_info("/Users/home/Downloads/example.xml")

"""

Imports
    * an SBML model using its .xml file

Parameters
----------

the directory where the SBML model file is located

"""

sbml_graph_info_to_matplotlib_draw = sbmlplot.SBMLGraphInfoExportToMatPlotLib()
sbml_graph_info_to_matplotlib_draw.extract_graph_info(sbml_graph_info_from_sbml_model)
sbml_graph_info_to_matplotlib_draw.export("/Users/home/Downloads/example.xml")

"""

Exports
    * a static illustration of the biological network of the SBML model

Parameters
----------

the directory to which the output figure is saved

"""

sbml_graph_info_to_cytoscape_json = sbmlplot.SBMLGraphInfoExportToCytoscapeJs()
sbml_graph_info_to_cytoscape_json.extract_graph_info(sbml_graph_info_from_sbml_model)
sbml_graph_info_to_cytoscape_json.export("/Users/home/Downloads/example.xml")

"""

Exports
    * a .json file containing the information required to render a dynamic illustration of the graph of the SBML model through cytoscape.js.

Parameters
----------

the directory to which the output json file is saved

"""
