import sbmlplot

sbml_graph_info_from_sbml_model = sbmlplot.SBMLGraphInfoImportFromSBMLModel()
sbml_graph_info_from_sbml_model.extract_info("exampleSBMLModelFile.xml")

"""

Imports
    * an SBML model using its .xml file

Parameters
----------

the directory where the SBML model file is located

"""

sbml_graph_info_from_network_editor = sbmlplot.SBMLGraphInfoImportFromNetworkEditor()
f = open("exampleJsonFile.json")
sbml_graph_info_from_network_editor.extract_info(json.load(f))

"""

Imports
    * an json file contating the graph information exported by networkeditorGUI

Parameters
----------

the directory where the json file is located

"""

sbml_graph_info_to_matplotlib_draw = sbmlplot.SBMLGraphInfoExportToMatPlotLib()
sbml_graph_info_to_matplotlib_draw.extract_graph_info(sbml_graph_info)
sbml_graph_info_to_matplotlib_draw.export("exampleDirectory")

"""

Exports
    * a static illustration of the biological network of the SBML model

Parameters
----------

the directory to which the output figure is saved

"""

sbml_graph_info_to_cytoscape_json = sbmlplot.SBMLGraphInfoExportToCytoscapeJs()
sbml_graph_info_to_cytoscape_json.extract_graph_info(sbml_graph_info)
sbml_graph_info_to_cytoscape_json.export("exampleDirectory")

"""

Exports
    * a .json file containing the information required to render a dynamic illustration of the graph of the SBML model through cytoscape.js.

Parameters
----------

the directory to which the output json file is saved

"""

sbml_graph_info_to_network_editor_json = sbmlplot.SBMLGraphInfoExportToCytoscapeJs()
sbml_graph_info_to_network_editor_json.extract_graph_info(sbml_graph_info)
sbml_graph_info_to_network_editor_json.export("exampleDirectory")

"""

Exports
    * a .json file containing the information required to render a dynamic illustration of the graph of the SBML model through networkeditorGUI.

Parameters
----------

the directory to which the output json file is saved

"""
