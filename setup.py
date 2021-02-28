#!/usr/bin/env python
"""asf_search distutils configuration"""
from setuptools import setup

# Loads version number into __version__
exec(open('asf_search/version.py').read())

requirements = [
        "requests==2.25.1"
    ]

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="asf_search",
    version=__version__,
    author="Alaska Satellite Facility Discovery Team",
    author_email="uaf-asf-discovery@alaska.edu",
    description="Python wrapper for ASF's SearchAPI",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/asfadmin/Discovery-asf_search.git",
    packages=['asf_search'],
    package_dir={'asf_search': 'asf_search'},
    python_requires='>=3.6',
    install_requires=requirements,
    license='BSD',
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Hydrology",
        "Topic :: Utilities"
    ],
    #test_suite='???',
    #tests_require=['???'],
)
