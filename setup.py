"""asf_search setuptools configuration"""
from setuptools import find_packages, setup

requirements = [
    "requests",
    "shapely",
    "python-dateutil",
    "pytz",
    "importlib_metadata",
    "numpy",
    "dateparser",
    "markupsafe<=2.0.1", # jinja2 requires this version for soft_unicode
    "jinja2",
    "remotezip >= 0.10.0"
]

test_requirements = [
    "pytest < 7.2.0",
    "pytest-automation",
    "pytest-cov",
    "pytest-xdist",
    "coverage",
    "requests-mock",
    "nbformat",
    "nbconvert",
    "ipykernel", 
]

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="asf_search",
    # version=Declared in pyproject.toml, through "[tool.setuptools_scm]"
    author="Alaska Satellite Facility Discovery Team",
    author_email="uaf-asf-discovery@alaska.edu",
    description="Python wrapper for ASF's SearchAPI",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/asfadmin/Discovery-asf_search.git",
    project_urls={
        'Documentation': 'https://docs.asf.alaska.edu/asf_search/basics/'
    },
    packages=find_packages(exclude=["tests.*", "tests", "examples.*", "examples"]),
    package_dir={'asf_search': 'asf_search'},
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=requirements,
    extras_require={ "test": test_requirements },
    license='BSD',
    license_files=('LICENSE',),
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
)
