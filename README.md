# asf_search

[![PyPI version](https://img.shields.io/pypi/v/asf_search.svg)](https://pypi.python.org/pypi/asf_search/)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/asf_search)](https://anaconda.org/conda-forge/asf_search)

[![PyPI pyversions](https://img.shields.io/pypi/pyversions/asf_search.svg)](https://pypi.python.org/pypi/asf_search/)
[![PyPI license](https://img.shields.io/pypi/l/asf_search.svg)](https://pypi.python.org/pypi/asf_search/)

[![CodeFactor](https://www.codefactor.io/repository/github/asfadmin/discovery-asf_search/badge)](https://www.codefactor.io/repository/github/asfadmin/discovery-asf_search)
[![Github workflow](https://github.com/asfadmin/asf_search/actions/workflows/run-pytest.yml/badge.svg)](https://github.com/asfadmin/Discovery-asf_search/actions/workflows/run-pytest.yml) [![Join the chat at https://gitter.im/ASFDiscovery/asf_search](https://badges.gitter.im/ASFDiscovery/asf_search.svg)](https://gitter.im/ASFDiscovery/asf_search?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

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

```
conda install -c conda-forge asf_search
```

or into a virtual environment with

```
python -m pip install asf_search
```
## Usage

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
