# SBMLplotlib

SBMLplotlib is a python tool built on libsbnw, a C/C++ library which can read, manipulate, and write SBML layout and redner information. Through matplotlib, SBMLplotlib renders the biological network of an SBML model using either its already included or auto-generated layout and render information.

## How to Use
The SBMLplotlib and its built dependencies for macOs and Windows are in `src/SBMLplotlib` directory. To become able to `import sbmlplotlib`, you need to add this directory to your `PYTHONPATH` and make sure you are making use of Python 3.6 and matplotlib 3.1.0 or newer.

## A simple script
A simple script named  `quickrenderer`, which exports a rendered figure of the imported SBML model, is contained in `tests` direcotory.

## Dependences
Matplotlib, numPy, _libsbnw


