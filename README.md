# sbmlplot

Sbmlplot is a python tool built on <a href="https://github.com/adelhpour/SBNE">libSBNE</a>, an API which can read or automatically generate, manipulate, and write SBML Layout and Redner information. Using either the already-included or auto-generated information about Layout and Render extensions of an SBML model, sbmlplot helps you:

    - render a static illustration of the biological network of the SBML model through <a href="https://matplotlib.org/">matplotlib</a>
    
    - generate a `.json` file containing the *elements* and *styles* information required to render a dynamic illustration of the biological network of the model through <a href="https://js.cytoscape.org/">cytoscape.js</a>.

## How to Use

sbmplot can be installed using pip as:
`pip install sbmlplot`

Once it is done, it is possible to `import sbmlplot` in your script and make use of its methods. 


## A simple script
A simple script which shows how to read an SBML (xml) file, export a static illustration of its network in `.pdf` format, and generate the `.json` file that can be used by cytoscape.js to render the network of the model is contained in `testcases` directory.

## Dependences
<a href="https://github.com/adelhpour/SBNE">libsbne</a>, matplotlib, numPy, 


