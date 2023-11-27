from setuptools import setup
from setuptools import find_packages

MAJOR = 0
MINOR = 0
MICRO = 6

version = f'{MAJOR}.{MINOR}.{MICRO}'

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="networkinfotranslator",
    version=version,
    author="Adel Heydarabadipour",
    author_email="ad.heydarabadi@gmail.com",
    description="Visualize the network of SBML models",
    long_description_content_type = "text/x-rst",
    long_description = ("Network Info Translator is python tool that helps you render a static illustration of the biological network of the SBML model through matplotlib and generate a .json file containing the elements and styles information required to render a dynamic illustration of the biological network of the model through cytoscape.js."),
    url="https://github.com/adelhpour/NetworkInfoTranslator",
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
    python_requires=">=3.8"
)
