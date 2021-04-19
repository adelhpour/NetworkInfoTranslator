from setuptools import setup
from setuptools import find_packages
  

MAJOR = 1
MINOR = 0
MICRO = 0

version = f'{MAJOR}.{MINOR}.{MICRO}'

setup(
    name="sbmlplotlib",
    version=version,
    author="Adel Heydarabadipour",
    author_email="ad.heydarabadi@gmail.com",
    description="SBML network visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adelhpour/sbmlplotlib",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=["tests/quickrenderer.py"]
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"sbmlplotlib": ["*.dll", '*.so', '*.dylib']},
    python_requires=">=3.6"
)
