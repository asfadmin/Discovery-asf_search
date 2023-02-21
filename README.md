# asf_search

[![PyPI version](https://img.shields.io/pypi/v/asf_search.svg)](https://pypi.python.org/pypi/asf_search/)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/asf_search)](https://anaconda.org/conda-forge/asf_search)

[![PyPI pyversions](https://img.shields.io/pypi/pyversions/asf_search.svg)](https://pypi.python.org/pypi/asf_search/)
[![PyPI license](https://img.shields.io/pypi/l/asf_search.svg)](https://pypi.python.org/pypi/asf_search/)

[![CodeFactor](https://www.codefactor.io/repository/github/asfadmin/discovery-asf_search/badge)](https://www.codefactor.io/repository/github/asfadmin/discovery-asf_search)
[![Github workflow](https://github.com/asfadmin/asf_search/actions/workflows/run-pytest.yml/badge.svg)](https://github.com/asfadmin/Discovery-asf_search/actions/workflows/run-pytest.yml)

![CodeCov](https://img.shields.io/codecov/c/github/asfadmin/Discovery-asf_search/master)

[![Documentation](https://img.shields.io/badge/docs-at_ASF-green)](https://docs.asf.alaska.edu/asf_search/basics/)
[![Join the chat at https://gitter.im/ASFDiscovery/asf_search](https://badges.gitter.im/ASFDiscovery/asf_search.svg)](https://gitter.im/ASFDiscovery/asf_search?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


Python wrapper for the ASF SearchAPI

```python
import asf_search as asf

results = asf.granule_search(['ALPSRS279162400', 'ALPSRS279162200'])
print(results)

wkt = 'POLYGON((-135.7 58.2,-136.6 58.1,-135.8 56.9,-134.6 56.1,-134.9 58.0,-135.7 58.2))'
results = asf.geo_search(platform=[asf.PLATFORM.SENTINEL1], intersectsWith=wkt, maxResults=10)
print(results)
```

## Install

In order to easily manage dependencies, we recommend using dedicated project environments
via [Anaconda/Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
or [Python virtual environments](https://docs.python.org/3/tutorial/venv.html).

asf_search can be installed into a conda environment with

```bash
conda install -c conda-forge asf_search
```

or into a virtual environment with

```bash
python3 -m pip install asf_search
```

To install pytest/cov packages for testing, along with the minimal packages:

```bash
python3 -m pip install asf_search[test]
```

## Usage

_Full documentation is available at https://docs.asf.alaska.edu/asf_search/basics/_

Programmatically searching for ASF data is made simple with asf_search. Several search functions are provided:
- `geo_search()` Find product info over an area of interest using a WKT string
- `granule_search()` Find product info using a list of scenes
- `product_search()` Find product info using a list of products
- `search()` Find product info using any combination combination of search parameters
- `stack()` Find a baseline stack of products using a reference scene
- Additionally, numerous constants are provided to ease the search process

Additionally, asf_search support downloading data, both from search results as provided by the above search functions, and directly on product URLs. An authenticated session is generally required. This is provided by the `ASFSession` class, and use of one of its three authentication methods:
- `auth_with_creds('user', 'pass)`
- `auth_with_token('EDL token')`
- `auth_with_cookiejar(http.cookiejar)`

That session should be passed to whichever download method is being called, can be re-used, and is thread safe. Examples:
```python
results = asf_search.granule_search([...])
session = asf_search.ASFSession()
session.auth_with_creds('user', 'pass')
results.download(path='/Users/SARGuru/data', session=session)
```
Alternately, downloading a list of URLs contained in `urls` and creating the session inline:
```python
urls = [...]
asf_search.download_urls(urls=urls, path='/Users/SARGuru/data', session=ASFSession().auth_with_token('EDL token'))
```

Also note that `ASFSearchResults.download()` and the generic `download_urls()` function both accept a `processes` parameter which allows for parallel downloads.

Further examples of all of the above can be found in `examples/`


## Development

### Branching

<table>
  <thead>
    <tr>
      <th>Instance</th>
      <th>Branch</th>
      <th>Description, Instructions, Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Stable</td>
      <td>stable</td>
      <td>Accepts merges from Working and Hotfixes</td>
    </tr>
    <tr>
      <td>Working</td>
      <td>master</td>
      <td>Accepts merges from Features/Issues and Hotfixes</td>
    </tr>
    <tr>
      <td>Features/Issues</td>
      <td>topic-*</td>
      <td>Always branch off HEAD of Working</td>
    </tr>
    <tr>
      <td>Hotfix</td>
      <td>hotfix-*</td>
      <td>Always branch off Stable</td>
    </tr>
  </tbody>
</table>

For an extended description of our workflow, see https://gist.github.com/digitaljhelms/4287848

### Enable Logging

We use standard the standard `logging` in our package for output.

Heres a basic example for hooking into it with your application:

```python
import asf_search as asf
import logging
ASF_LOGGER = logging.getLogger("asf_search")
formatter = logging.Formatter('[ %(asctime)s (%(name)s) %(filename)s:%(lineno)d ] %(levelname)s - %(message)s')

# Get output to the console:
stream_handle = logging.StreamHandler()
stream_handle.setFormatter(formatter)
ASF_LOGGER.addHandler(stream_handle)
# If you want it write to a file too:
file_handle = logging.FileHandler('MyCustomApp.log')
file_handle.setFormatter(formatter)
ASF_LOGGER.addHandler(file_handle)
# Only see messages that might affect you
ASF_LOGGER.setLevel(logging.WARNING)
# Test if the logger throws an error, you see it as expected:
ASF_LOGGER.error("This is only a drill. Please do not panic.")
# Should output this:
# [ 2023-01-17 10:04:53,780 (asf_search) main.py:42 ] ERROR - This is only a drill. Please do not panic.
```

For more configure options on `logging`, please visit [their howto page](https://docs.python.org/3/howto/logging.html).
