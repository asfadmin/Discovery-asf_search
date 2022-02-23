# SAR Data in Python: Getting to Know asf_search

***
## About the Alaska Satellite Facility

__ASF is part of the Geophysical Institute of the University of Alaska Fairbanks.__

- ASF downlinks, processes, archives, and distributes remote-sensing data to scientific users around the world.
- ASF promotes, facilitates, and participates in the advancement of remote sensing to support national and international Earth science research, field operations, and commercial applications.
- ASF commits to provide the highest quality data and services in a timely manner.

__Distributed Active Archive Center (DAAC):__ ASF operates the NASA archive of synthetic aperture radar (SAR) data from a variety of satellites and aircraft, providing these data and associated specialty support services to researchers in support of NASA’s Earth Science Data and Information System (ESDIS) project.

[ASF Website](https://asf.alaska.edu)

[Contact ASF](https://asf.alaska.edu/contact/)

***
## ASF Discovery Team

__The ASF Discovery team's focus is to provide tools that help users find and acquire the data they want as quickly and smoothly as possible.__

Some tools provided by ASF's Discovery team include:
- [Vertex](https://search.asf.alaska.edu): web application for searching the ASF archive, as well as performing meta-analysis and custom On Demand processing
- [ASF Search API](https://docs.asf.alaska.edu/api/basics/): Public REST API for searching the ASF archive
- [ASF Python Search Module](https://docs.asf.alaska.edu/asf_search/basics/) (asf_search): Python module for programmatically finding and acquiring data from the ASF archive

***
## Working in Python: asf_search
__asf_search is a Python module created to simplify the process of finding and acquiring data programmatically.__
- Search API is very technical: we saw a need to reduce the technical overhead required when using Search API.
- Vertex is very interactive: sometimes, an automated or semi-automated process is required, and we wanted to make the power of Vertex available in that context.
- Downloading data can be difficult: there are many ways to acquire data, and knowing how to use them effectively can be difficult.

***
## Today's Topic
__We will explore some basic usage of asf_search, with a focus on search functionality.__
  
Specific features to be covered include:
- Classes for working with ASF data
- Search functions
- Authentication methods
- Download functionality
  
This session is targeted largely at users who have a passing familiarity with Python, but `asf_search` is designed to be easily used by everyone from novice to expert.

***
Next: [Basic Overview](./1-Basic_Overview.ipynb)