# NetworkInfoTranslator

NetworkInfoTranslator is a python tool. Using either the already-included or auto-generated information about Layout and Render extensions of an SBML model, NetworkInfoTranslator helps you:

* render a static illustration of the biological network of the SBML model through <a href="https://matplotlib.org/">matplotlib</a>,
    
* generate a `.json` file containing the *elements* and *styles* information required to render a dynamic illustration of the biological network of the model through <a href="https://js.cytoscape.org/">cytoscape.js</a>.

## How to Use

NetworkInfoTranslator can be installed from <a href="https://test.pypi.org/">TestPyPI</a> using pip as:

`pip install -i https://test.pypi.org/simple/ NetworkInfoTranslator`

Once that is done, it is possible to `import NetworkInfoTranslator` in your script and make use of its methods. 


## A simple script
A simple script which shows how to read an SBML (xml) file, export a static illustration of its network in `.pdf` format, and generate the `.json` file that can be used by cytoscape.js to render the network of the model is contained in `testcases` directory.

******NOTE******: You can follow <a href="https://blog.js.cytoscape.org/2016/05/24/getting-started/">this tutorial</a>  to see how to visualize the network of your model using the generated `.json` file.

## Dependences
<a href="https://github.com/adelhpour/SBNE">libsbne</a>, matplotlib, numPy, 


