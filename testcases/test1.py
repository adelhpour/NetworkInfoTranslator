import networkinfotranslator

sbml_graph_info_from_sbml_model = networkinfotranslator.NetworkInfoImportFromSBMLModel()
sbml_graph_info_from_sbml_model.extract_info("exampleSBMLModelFile.xml")

"""

Imports
    * an SBML model using its .xml file

Parameters
----------

the directory where the SBML model file is located

"""

sbml_graph_info_from_network_editor = networkinfotranslator.NetworkInfoImportFromNetworkEditor()
f = open("exampleJsonFile.json")
sbml_graph_info_from_network_editor.extract_info(json.load(f))

"""

Imports
    * an json file contating the graph information exported by networkeditorGUI

Parameters
----------

the directory where the json file is located

"""

sbml_graph_info_to_matplotlib_draw = networkinfotranslator.NetworkInfoExportToMatPlotLib()
sbml_graph_info_to_matplotlib_draw.extract_graph_info(sbml_graph_info)
sbml_graph_info_to_matplotlib_draw.export("exampleDirectory")

"""

Exports
    * a static illustration of the a network

Parameters
----------

the directory to which the output figure is saved

"""

sbml_graph_info_to_cytoscape_json = networkinfotranslator.NetworkInfoExportToCytoscapeJs()
sbml_graph_info_to_cytoscape_json.extract_graph_info(sbml_graph_info)
sbml_graph_info_to_cytoscape_json.export("exampleDirectory")

"""

Exports
    * a .json file containing the information required to render a dynamic illustration of a graph through cytoscape.js.

Parameters
----------

the directory to which the output json file is saved

"""

sbml_graph_info_to_network_editor_json = networkinfotranslator.NetworkInfoExportToCytoscapeJs()
sbml_graph_info_to_network_editor_json.extract_graph_info(sbml_graph_info)
sbml_graph_info_to_network_editor_json.export("exampleDirectory")

"""

Exports
    * a .json file containing the information required to render a dynamic illustration of a graph through networkeditorGUI.

Parameters
----------

the directory to which the output json file is saved

"""
