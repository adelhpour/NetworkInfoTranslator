import sbmlplotlib as sbmlplt

sbmlplt.SBMLRenderer(inputfile="exampleSBMLModelFile.xml", outputfile="outputFile.pdf")

"""

Exports a rendered figure of the SBML model

Parameters
----------

inputfile : the directory of the SBML model (xml file)

outputfile : the directory where the rendered figure is saved.
    The export format can be determined using .pdf, .svg, .png, and etc. at the end of the outputfile name
    
"""
