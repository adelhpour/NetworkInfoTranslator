# SBMLplotlib

SBMLplotlib is a python tool built on <a href="https://github.com/adelhpour/SBNE">SBNE</a>, an API which can read, manipulate, and write SBML layout and redner information. Through matplotlib, SBMLplotlib renders the biological network of an SBML model using either its already-included or auto-generated inforamation about layout and render extensions of SBML.

## How to Use

To use SBMLplotlib, you first need to:
* Build SBNE from its <a href="https://github.com/adelhpour/SBNE">source</a> (follow the instructions in "Use Python bindings" section)

* Add the directory of the SBNE built Python library to your `PYTHONPATH`

* Add `<root directory of SBMLplotlib>/src/sbmlplotlib` to your `PYTHONPATH`

And then you are able to `import sbmlplotlib` into your script, but make sure you are using Python 3.6 and matplotlib 3.1.0 or newer.

## A simple script
A simple script, which reads an SBML (xml) file and exports the rendered figure of its network, is contained in `testcases` direcotory.

## Dependences
Matplotlib, numPy, <a href="https://github.com/adelhpour/SBNE">SBNE</a>


