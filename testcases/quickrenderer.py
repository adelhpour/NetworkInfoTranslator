import sbmlplot

sbmlplot.SBMLRenderer(inputfilename="exampleSBMLModelFile.xml", export_graph_info=True, export_figure_format=".pdf")

"""

Exports
    * a static illustration of the biological network of the SBML model
    * a .json file containing the elements and styles information required to render a dynamic illustration of the biological network of the model through cytoscape.js.

Parameters
----------

inputfilename : the directory of the SBML model (xml file)

export_graph_info : a boolean indicating whether to export the .json file or not

export_figure_format : a string indicating the format of the exported figure, including .pdf, .svg, and .png. No figure is exported if it is not set.

"""
