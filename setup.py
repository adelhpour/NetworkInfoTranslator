from setuptools import setup
from setuptools import find_packages
  

MAJOR = 0
MINOR = 0
MICRO = 4

version = f'{MAJOR}.{MINOR}.{MICRO}'

setup(
    name="sbmlplot",
    version=version,
    author="Adel Heydarabadipour",
    author_email="ad.heydarabadi@gmail.com",
    description="Visualize the network of SBML models",
    long_description_content_type = "text/x-rst",
    long_description = ("Sbmlplot is a python tool built on libSBNE, an API which can read or automatically generate, manipulate, and write SBML Layout and Redner information. Using either the already-included or auto-generated information about Layout and Render extensions of an SBML model, sbmlplot helps you render a static illustration of the biological network of the SBML model through matplotlib and generate a .json file containing the elements and styles information required to render a dynamic illustration of the biological network of the model through cytoscape.js."),
    url="https://github.com/adelhpour/sbmlplot",
    license = "MIT License",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=["testcases/test1.py"],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=open('requirements.txt').readlines(),
    python_requires=">=3.7"
)
