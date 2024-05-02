# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/) 
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


<!--
## Example template!!

## [version](https://github.com/asfadmin/Discovery-PytestAutomation/compare/vOLD...vNEW)

### Added:
-

### Changed:
-

### Fixed:
- 

### Removed:
-

-->
------
## [v7.1.1](https://github.com/asfadmin/Discovery-asf_search/compare/v7.1.0...v7.1.1)
### Changed
- Uses `ciso8601.parse_datetime()` in baseline calculations, speeds up calculations on larger stacks
### Added
- Adds `ASF_LOGGER` logging in `search_generator()` and related methods
### Fixed
- `ASFProduct.get_sort_keys()` will no longer returns `None` if missing sort key, defaults to empty string 

------
## [v7.1.0](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.9...v7.1.0)
### Added
- Improved logging in `ASFSession` authentication methods
### Changed
- Uses `ciso8601` module for parsing dates from CMR response, significant performance improvement post-query
- `ASFSession` now allows for authorized user access to hidden/restricted CMR datasets via `auth_with_creds()` or `auth_with_cookiejar()` authentication methods (previously only supported via `auth_with_token()` method)
- `ASFSession.auth_with_token()` now authenticates directly against EDL endpoint
- UMM Platform ShortName used as final fallback criteria for product subclass assignment

------
## [v7.0.9](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.8...v7.0.9)
### Changed
- collection "ARIA_S1_GUNW" added to `ARIA_S1_GUNW` dataset, V3 products now loaded as `ARIAS1GUNWProduct` subclass
- `ARIAS1GUNWProduct` now exposes `ariaVersion` and (for V3 products) `inputGranules` in `ARIAS1GUNWProduct.properties`

------
## [v7.0.8](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.7...v7.0.8)
### Added
- `s3Urls` property added to `S1Product`, `OPERAS1Product`, and `NISARProduct` types, exposing direct access S3 links

------
## [v7.0.7](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.6...v7.0.7)
### Added
- Adds `cmr_keywords` search keyword, enables passing CMR format strings in search directly
- Adds `shortName` keyword, for use with lists of collection short names
### Changed
- Allows using `dataset` and `platform` in same search

------
## [v7.0.6](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.5...v7.0.6)
### Changed
- timestamps while building queries and reading results from CMR now use UTC if no timezone is provided
- Changed what collections the `NISAR` dataset and platform collections lists are pointed at.

------
## [v7.0.5](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.4...v7.0.5)
### Added
- Adds basic NISAR dataset search and product functionality for test data

------
## [v7.0.4](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.3...v7.0.4)
### Changed
- `OPERA-S1-CALIBRATION` dataset is now the `OPERA-S1-CALVAL` dataset, uses the `OPERA_S1_CALVAL` constant

------
## [v7.0.3](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.2...v7.0.3)
### Fixed
- Fixes typo for constant variable name `constants.PRODUCT_TYPE.CSLC_STATIC`
- Normalizes concept-id lists for `OPERA-S1` dataset product types

### Changed
- Completely removes `CSLC-STATIC` Calval and `RTC-STATIC` Calval collections from concept-id lists

------
## [v7.0.2](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.1...v7.0.2)
### Added
- Adds `AUTH_COOKIES` to `constants.INTERNAL` and `auth_cookie_names` variable for `ASFSession`, used by `auth_with_creds()` and `auth_with_cookiejar()` to confirm login.

### Fixed
- Attempting to authorize `ASFSession` against CMR UAT using `auth_with_creds()` and `auth_with_cookiejar()` no longer raises an exception on valid login
- Fixes custom host in `ASFSearchOptions` raising type error while searching.

------
## [v7.0.1](https://github.com/asfadmin/Discovery-asf_search/compare/v7.0.0...v7.0.1)
### Fixed
- Fixed `OPERA-S1-CALIBRATION` dataset products raising error during search.

------
## [v7.0.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.7.3...v7.0.0)
### Added
- `ASFProduct` now has 13 sublcasses for different sub-products that correspond to datasets:
  - `S1Product`, `S1BurstProduct`, `OPERAS1Product`, `ARIAS1GUNWProduct`, `ALOSProduct`, `RADARSATProduct`, `AIRSARProduct`, `ERSProduct`, `JERSProduct`, `UAVSARProduct`, `SIRCProduct`, `SEASATProduct`, `SMAPProduct`
  - Each subclass defines relevant keys to pull from `umm` response, reducing the amount of irrelevant values in `properties` dict for certain product types 
- Adds `collectionAlias` to `ASFSearchOptions` validator map as config param. Set to `False` to disable concept-id aliasing behaviour for `processingLevel` and `platform`.
- Adds warning when scenes in stack are missing state vectors, and logs baseline warnings with `ASF_LOGGER`
- Adds `OPERA-S1-CALIBRATION` entry to `dataset_collections` and corresponding `OPERA_S1_CALIBRATION` constant to `DATASET.py`, used to search for OPERA-S1 `CSLC` and `RTC` calibration data.

### Changed
- `remotezip` is now an optional dependency of asf-search's pip and conda installs, (pip install example: `python3 -m pip install asf-search[extras]`).
- Constants are no longer top level import, are now accessible through respective modules
- `processingLevel` and `platform` are now aliased by collection concept-ids, (lists of concept ids by their processing levels/platforms viewable in `dataset.py`), improving search performance and dodging subquery system
- Baseline stacking no longer excludes products with missing state vectors from final stack, like SearchAPI
- `OPERA-S1` dataset no longer includes calibration data (moved to new dataset)
- Adds optional `ASFSession` constructor keyword arguments for new class variables:
   - `edl_host`
   - `edl_client_id`
   - `asf_auth_host`
   - `cmr_host`
   - `cmr_collections`
   - `auth_domains`
- `ASFSession` imports `asf_search.constants.INTERNAL` in constructor call
- `ASFSession` methods `auth_with_creds()`, `auth_with_token()`, and `rebuild_auth()` use new class variables instead of constants

------
## [v6.7.3](https://github.com/asfadmin/Discovery-asf_search/compare/v6.7.2...v6.7.3)
### Added
- Adds OPERA-S1 constants `RTC`, `RTC_STATIC` (RTC-STATIC), `CSLC`, `CSLC_STATIC` (CSLC-STATIC) to `PRODUCT_TYPE.py`

### Fixed
- Harmonizes `search()`, `geo_search()`, and `search_count()` parameters
- Updates python version requirement in `setup.py` to 3.8+

### Changed
- search method params with `Iterable` type hinting now changed to `Sequence`
- search method param validators updated to support `Sequence` type

------
## [v6.7.2](https://github.com/asfadmin/Discovery-asf_search/compare/v6.7.1...v6.7.2)
### Added
- Adds constants for `dataset` keyword, under `asf_search.DATASET`
- Adds CALVAL concept-ids to 'OPERA-S1' dataset
- Adds `validityStartDate` for applicable OPERA-S1 products

### Fixed
- Fixes OPERA-S1 dataset `RTC-STATIC` and `CSLC-STATIC` breaking returned results, sorts by `validityStartDate` in place of `stopTime`

------
## [v6.7.1](https://github.com/asfadmin/Discovery-asf_search/compare/v6.7.0...v6.7.1)
### Fixed
- Fixes issue with certain S1 products not stacking properly in certain environments, which caused null `perpendicularBaseline` values

------
## [v6.7.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.6.3...v6.7.0)
### Added
- Adds new `dataset` keyword to `search()` as an alternative to `platform`. Allows users to get results from multiple platforms at once in a single page
- Adds `operaBurstID` keyword to `search()`
- Adds OPERA-S1 param `operaBurstID` to `ASFProduct.properties`, and adds Opera product urls to `additionalUrls`
- OPERA-S1 RTC product `polarization` now shows both polarizations as list
- adds `frameNumber` properties support for new `Sentinel-1 Interferogram` products
- added `CMR_TIMEOUT` constant. This is the amount of time in seconds to wait without seeing *any* data. (Default=30)

### Changed
- Changes `CMR_FORMAT_EXT` constant from `umm_json_v1_4` to `umm_json`, umm returned from CMR will now be in latest umm format by default

### Fixed
- ERS-1, ERS-2, JERS-1, and RADARSAT-1 now assign `FRAME_NUMBER` to the `frameNumber` properties field

------
## [v6.6.3](https://github.com/asfadmin/Discovery-asf_search/compare/v6.6.2...v6.6.3)
### Fixed
- Fixes type hinting compatibility break introduced in v6.6.2 in `search_generator.py` for Python versions < v3.9

------
## [v6.6.2](https://github.com/asfadmin/Discovery-asf_search/compare/v6.6.1...v6.6.2)
### Added
- Adds new `CMRIncompleteError` exception, raised by search methods when CMR returns an incomplete page
### Fixed
- Fixes bug in `search_generator()` causing results to sometimes wrongly be marked as incomplete
### Changed
- `stack_from_id()` now raises if results are incomplete, before checking if reference was found

------
## [v6.6.1](https://github.com/asfadmin/Discovery-asf_search/compare/v6.6.0...v6.6.1)
### Added
- Adds automated release notes
### Fixed
- `filename` can be used again with `ASFProduct.Download()` method (ignored if multiple files are to be downloaded)

------
## [v6.6.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.5.0...v6.6.0)
### Added
- Adds `fileType` param to `ASFProduct` and `ASFSearchResults` download method. Let's users download burst .xml and/or .tiff from the burst extractor with `FileDownloadType` enum (`DEFAULT_FILE`, `ADDITIONAL_FILES`, `ALL_FILES`)
### Fixed
- Fixes typo in convex hull warning message

------
## [v6.5.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.4.0...v6.5.0)
### Added
- Adds `collections` search keyword, letting results be limited to the provided concept-ids
- Adds `temporalBaselineDays` search keyword, allows searching `Sentinel-1 Interferogram (BETA)` products by their temporal baseline
### Changed
- `search_generator()` now uses tenacity library to poll CMR
- moves/re-organizes certain constant url fields to `INTERNAL.py`
### Fixed
- TimeoutErrors now properly caught and logged

------
## [v6.4.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.3.1...v6.4.0)
### Added
- Burst product downloads now supported
- `IPFVersion` field added to `ASFProduct` properties
### Fixed
- `BURST` product `url`, `fileName`, and `bytes` properties populated again
- `search_count()` now uses `ASFSearchOptions.host` when building query url
### Changed:
- `BURST` product baseline stackng now uses `fullBurstID` and `polarization` for getting initial stack
- Changed order of entries in `ASFSession`'s `User-Agent` header
- `BURST` `filename` field uses "`sceneName`.`extension`" format

------
## [v6.3.1](https://github.com/asfadmin/Discovery-asf_search/compare/v6.3.0...v6.3.1)
### Changed
- Changed `CMR_PAGE_SIZE` constant from 500 to 250

------
## [v6.3.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.2.0...v6.3.0)
### Added
- `BURST` product temporal/perpendicular baseline stacking now supported
- Added searchable burst keyword params, `relativeBurstID`, `absoluteBurstID`, and `fullBurstID`
### Changed
- `validate_wkt()` now returns both wrapped and unwrapped wkts along with repair reports. 
- asf-search now sends the wrapped wkt to CMR when using the `intersectsWith` keyword
- Removed `burstAnxTime`, `timeFromAnxSeconds` 
- Added `azimuthAnxTime`, `azimuthTime`

------
## [v6.2.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.1.0...v6.2.0)
### Added
- `search_generator()` returns a generator, which returns results from CMR page-by-page, yielding each page as an `ASFSearchResults` object. See /examples/1-Basic_Overview.ipynb for an example.
  - The generator can be passed to different output formats via `results_to_[format]()` methods, allowing users to stream results to different format strings as they're received from CMR
### Changed
- Removed Jinja2 as a dependency for metalink, kml, and csv output formats.

------
## [v6.1.0](https://github.com/asfadmin/Discovery-asf_search/compare/v6.0.2...v6.1.0)
### Added
- Burst metadata available in `ASFProduct.properties['burst']`, also available in `csv`, `kml`, `jsonlite`, and `jsonlite2` output formats.
- Added `BURST` to `PRODUCT_TYPE.py` constants
- Added python `logging` support, for easier debugging and reporting when using asf_search inside an application.

### Changed
- Decreased the scope of tested platforms used in platform test cases

### Fixed
- Adds markupsafe<=2.0.1 as package requirement (Jinja2 requires this version)
- CMR url will now actually use the `host` property in `ASFSearchOptions` object

------
## [v6.0.2](https://github.com/asfadmin/Discovery-asf_search/compare/v6.0.1...v6.0.2)
### Fixed
- Fixed Setuptools not including csv, kml, and metalink export templates

------
## [v6.0.1](https://github.com/asfadmin/Discovery-asf_search/compare/v6.0.0...v6.0.1)
### Fixed
- `csv()`, `metalink()`, and `kml()` output formats should now work properly when installed from pip

------
## [v6.0.0](https://github.com/asfadmin/Discovery-asf_search/compare/v5.1.2...v6.0.0)
### Added
- Search errors are now automatically reported to ASF, users can opt out by changing `asf_search.REPORT_ERRORS` after import
  - Example and information available in "Usage" section of /examples/1-Basic_Overview.ipynb
- `ASFSearchResults` now has `raise_if_incomplete()` method, raises `ASFSearchError()` if a search encountered an error and was unable to return all results from CMR
- `ASFProduct` now has a `remotezip()` method, which takes a user's pre-authenticated `ASFSession` and returns a `RemoteZip` object. This can be used to list and download specific files from a product's zip archive, rather than the whole zip file. 
  - Example available in /examples/5-Download.ipynb
  - see https://github.com/gtsystem/python-remotezip for further details on how to use the `RemoteZip` class.
- Adds `GRD_FD`, `PROJECTED_ML3X3`, `THREEFP` product type constants.

### Changed
- While returning results, `search()` will no longer throw. Instead, `search()` will retry the request 3 times. If all 3 attempts fail:
  -  `search()` will return the results it found before the search error
  -  An error will be logged warning the user, and the returned results will be marked as incomplete. Use `raise_if_incomplete()` to raise an error when the returned `ASFSearchResults` are incomplete.

------
## [5.1.2](https://github.com/asfadmin/Discovery-asf_search/compare/v5.1.0...v5.1.2)
### Changed
- `CMR_PAGE_SIZE` reduced from 2000 to 500

------
## [5.1.0](https://github.com/asfadmin/Discovery-asf_search/compare/v5.0.2...v5.1.0)
### Added
- Adds export support to ASFSearchResults for `csv`, `jsonlite`, `jsonlite2`, `kml`, `metalink`
  - example availabe in "Output" section of /examples/1-Basic_Overview.ipynb
- Adds `beamSwath` as a searchable parameter

### Fixed
- `count()` type hinting changed to `int`

### Changed
- Improved testing coverage of `ASFSearchResults`

------
## [5.0.2](https://github.com/asfadmin/Discovery-asf_search/compare/v5.0.1...v5.0.2)
### Fixed
- non-rectangular polygons are now sent to CMR instead of their bounding boxes

------
## [5.0.1](https://github.com/asfadmin/Discovery-asf_search/compare/v5.0.0...v5.0.1)
### Changed
- `ASFProduct` is now aware of the session used during search (if available) and will use that by default to download. A session can still be explicitly provided as before.
- `ASFProduct.stack()` now uses the session provided via the opts argument. If none is provided, it will use the session referenced by `ASFProduct.session`.
- `ASFProduct` more gracefully handles missing or malformed metadata during instantiation.

------
## [5.0.0](https://github.com/asfadmin/Discovery-asf_search/compare/v4.0.3...v5.0.0)
### Changed
- `asf_search` now searches CMR directly, no longer relying on ASF's SearchAPI
  - This should significantly improve reliability and performance
  - With this change, ALL metadata fields provided by CMR's UMM JSON format are now available through `ASFProduct`.
    -  All metadata fields previously available through `ASFProduct.properties` remain where they are
      - For those and any other fields, the full CMR `umm` and `meta` records are available through `ASFProduct.umm` and `ASFProduct.meta` respectively
- Some geojson fields were previously presented as strings, they are now more appropriate types such as `int` or `float`:
  - `bytes`, `centerLat`, `centerLon`, `frame`, `offNadirAngle`, `orbit`, `pathNumber`
- Timestamps in geojson fields now include an explicit `Z` time zone indicator.
- `ASFSearchOptions.reset()` has been renamed to `reset_search()` for clarity of purpose and to make room for future similar functionality regarding search opts configuration.
- `search()` (and related functions) now return results pre-sorted, most recent first

------
## [4.0.3](https://github.com/asfadmin/Discovery-asf_search/compare/v4.0.2...v4.0.3)
### Fixed
- `product_search()` now assigns `product_list` parameter to `ASFSearchOptions.product_list` instead of `ASFSearchOptions.granule_list` 

------
## [4.0.2](https://github.com/asfadmin/Discovery-asf_search/compare/v4.0.1...v4.0.2)
### Changed
- Removed `scikit-learn` module as a dependency, greatly reducing install footprint
- Simplified AOI refinement:
  - AOIs are iteratively simplified with an increasing threshold, that threshold now starts at 0.004
  - AOIs with an MBR <= 0.004 in lat/lon are collapsed to a single point
  - AOIs with an MBR <= 0.004 in either lat or lon are collapsed to a line along the center of the rectangle

------
## [4.0.1](https://github.com/asfadmin/Discovery-asf_search/compare/v4.0.0...v4.0.1)
### Changed
- Removed WKTUtils module as a dependency, that functionality is now directly included

------
## [4.0.0](https://github.com/asfadmin/Discovery-asf_search/compare/v3.0.4...v4.0.0)
### Added
- `ASFSearchOptions`: This class provides a number of useful ways to build search results
  - Search parameters are immediately validated upon object creation/edit instead of at search time, which should lead to fewer errors at search time
  - All search functions allow both the previous style of keyword arguments, as well as simply passing in an ASFSearchOptions object using the `opts` keyword arg. `opts` is always optional.
    - If both approaches are used, the two are merged, with specific keyword args superseding the options in the object
    - Most search functions now expect only their specific parameters, and an optional `opts` parameter. This allows simple usage in most cases, while the `opts` parameter provides access to advanced behavior or alternate workflows.
  - Internally, all search functions work by passing ASFSearchOptions objects. This allows consistency when working with differently-configured search environments, such as in development.
  - `ASFSearchResults` objects now include a `searchOptions` property, which describes the search used to create those results. This object can be copied, altered, used for subsequent searches, etc.
    - When downloading, `ASFSearchResults` and `ASFProduct` default to use the session inside `searchOptions`, so you don't have to pass the same session in for both fetching and downloading results.
- Exposed `get_stack_opts()` to support more approaches for building insar stacks.
  - `get_stack_opts()` accepts an `ASFProduct` as a stack reference and returns the ASFSearchOptions object that would be used to build a corresponding insar stack
    - A matching convenience method has been added to `ASFProduct`
  - Supports the new `opts` argument described above.

### Changed
- All search functions now accepts the optional `opts=` argument, see `ASFSearchOptions` notes above.
- Replaced all `cmr_token` key arguments with `session`, which takes a `Session`-compatible object. See https://docs.asf.alaska.edu/asf_search/ASFSession/ for more details.
- Removed old GitHub actions

### Fixed
- `season` filter in `asf.search()` now doesn't throw when used.

------
## [3.2.2](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v3.2.1...v3.2.2)
### Fixed
- netrc authentication works again, affects `ASFProduct.download()`, `ASFSearchResults.download()`, `download_urls()`, `download_url()`

------
## [3.2.1](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v3.2.0...v3.2.1)
### Fixed
- `ASFProduct.stack()` and `asf_search.baseline_search.stack_from_id()` now return ASFSearchResults instead of a list

------
## [3.2.0](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v3.1.3...v3.2.0)
### Changed
- `ASFProduct.stack()` and `asf_search.baseline_search.stack_from_id()` now calculate `temporalBaseline` and `perpendicularBaseline` values of stacked products locally
- `search()` now internally uses a custom format when communicating with ASF's SearchAPI. This should have no apparent impact on current usage of asf_search. 

------
## [3.1.3](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v3.1.2...v3.1.3)
### Fixed
- Centroid calculation fixed for scenes spanning the antimeridian

------
## [3.1.2](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v3.1.1...v3.1.2)
### Changed
- `ASFSession` methods `auth_with_cookiejar()` and `auth_with_token()` now raise an error if the passed cookiejar/token is invalid or expired
- `ASFAuthenticationError` raised when encountering a 400 level error while downloading files
### Fixed
- Downloading files with sessions authenticated by `auth_with_token()` method works again

------
## [3.1.1](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v3.1.0...v3.1.1)
### Fixed:
- Fixes missing CMR module import

------
## [3.1.0](https://github.com/asfadmin/Discovery-asf_search/compare/v3.0.6...v3.1.0)
### Added
- Added walkthrough in the form of several jupyter notebooks in /examples
- Added `campaigns()` in `Campaigns` module, returns a list of campaigns for `UAV, AIRSAR, SENTINEL-1 INTERFEROGRAM (BETA)` platforms

### Changed
- Re-enable run-pytest workflow
  - Add tests for `ASFSearch, ASFSession, ASFProduct` as well as baseline, geographic, and search modules
  - Add Pytest-Automation Plugin integration
  - Add automated CodeCov badge to readme
- "collectionName" parameter in `geo_search()` and `search()` is deprecated and raises a warning. Will be removed in a future release, use "campaign" instead

### Fixed
- Fix error while raising ASFBaselineError in `baseline_search.get_stack_params()`

------
## [3.0.6](https://github.com/asfadmin/Discovery-asf_search/compare/v3.0.5...v3.0.6)
### Changed
- Skip download if file already exists
  - In the future we will apply file size and/or checksum checks to ensure the existing file is correct

------
## [3.0.5](https://github.com/asfadmin/Discovery-asf_search/compare/v3.0.4...v3.0.5)
### Added
- Add documentation URL to setup.py
- Add Gitter badge/link to readme
### Fixed
- Change hyphens to underscores in some product type constants

------
## [3.0.4](https://github.com/asfadmin/Discovery-asf_search/compare/v3.0.3...v3.0.4)
### Changed
- When working with source, package **must** be installed directly:
  - `python3 -m pip install -e .`
### Fixed
- In-region S3 downloads should now function without issue

------
## [3.0.3](https://github.com/asfadmin/Discovery-asf_search/compare/v3.0.2...v3.0.3)
### Fixed
- Replace `ASFProduct.centroid()` calculation with shapely-based calculation
  - See: https://github.com/asfadmin/Discovery-asf_search/pull/53
  - Removes numpy requirement
  - Adds shapely requirement

------
## [3.0.2](https://github.com/asfadmin/Discovery-asf_search/compare/v3.0.0...v3.0.2)
### Added
- Feature and Bug Report github issue templates

### Fixed
- Fix download authentication header issue during direct-to-S3 redirects
- Fix Sentinel-1 stacking to include both A and B in stacks

------
## [3.0.0](https://github.com/asfadmin/Discovery-asf_search/compare/v2.0.2...v3.0.0)
### Added
- Auth support for username/password and cookiejars, in addition to the previously available token-based approach. Create a session, authenticate it with the method of choice, then pass the session to whichever download method is being used.
    - Sessions can be created using the `ASFSession` class, a subclass of `requests.Session`
    - Once a session is created, call one of its authentication methods:
      - `auth_with_creds('user', 'pass)`
      - `auth_with_token(`EDL token`)
      - `auth_with_cookiejar(http.cookiejar)`
    - If you were previously using the `token` argument, such as:
      - `results.download(path='...', token='EDL token')`
    - Updating can be as simple as:
      - `results.download(path='...', session=ASFSession().auth_with_token('EDL token'))`
    - Sessions can be re-used and are thread-safe

### Changed
- `download_url()`, `download_urls()`, `ASFProduct.download()` and `ASFSearchResults.download()` now expect a `session` argument instead of `token`
- Send auth headers to every step along a download redirect chain (including final AWS S3 buckets)

------
## [2.0.2](https://github.com/asfadmin/Discovery-asf_search/compare/v2.0.1...v2.0.2)
### Added
- INSTRUMENT constants for C-SAR, PALSAR, and ANVIR-2

------
## [2.0.1](https://github.com/asfadmin/Discovery-asf_search/compare/v2.0.0...v2.0.1)
### Fixed
- Versioning workflow corrected for proper versioning, stop bumping major instead of patch!

------
## [2.0.0](https://github.com/asfadmin/Discovery-asf_search/compare/v1.1.0...v2.0.0)
### Fixed
- Fixed import order of operations bug
- Updated ASFProduct and ASFSearchResults to use path arg in download methods

------
## [1.1.0](https://github.com/asfadmin/Discovery-asf_search/compare/v0.4.0...v1.1.0)
### Added
- Parallel downloads now supported by ASFSearchResults. Defaults to 1 (sequential download)
- For `search()`-based functions that take an argument as a list, single values are now also allowed

### Changed
- Import download functionality in asf_search (for `download_url()` and `download_urls()`)
- "parallel" is now "processes" in download functionality

### Fixed
- Fixed ASFProduct import in search.py
- importlib metadata fix for python <3.8

------
## [0.4.0](https://github.com/asfadmin/Discovery-asf_search/compare/v0.3.0...v0.4.0)
### Added
- ASFSearchResults now has a geojson() method which returns a data structure that matches the geojson specification
- ASFProduct now has a geojson() method that produces a data structure matching a geojson feature snippet
- ASFSearchResults and ASFProduct both have a __str__() methods that serializes the output of their geojson() methods
- Added CodeFactor shield to readme
- Now calculates temporal baselines when building a stack
- New search options: 
    - min/maxDoppler
    - min/MaxFaradayRotation
    - flightLine
    - offNadirAngle
    - season

### Changed
- ASFProduct is no longer a subclass of dict. Instead, metadata has been moved to .properties and .geometry
- ASFSearchResults is now a subclass of UserList, for list-type operations
- Newly-built stacks are sorted by temporal baselines, ascending

### Fixed
- Cleaned up cruft from various refactors

------
## [0.3.0](https://github.com/asfadmin/Discovery-asf_search/compare/v0.2.4...v0.3.0)

### Added
- Layed out framework for INSTRUMENT constants (needs to be populated)
- Support for baseline stacking of pre-calculated datasets
- Download support for single products or entire search result sets, token-based auth only
- ASFSearchResults and ASFProduct classes
- Lower-level ASFError exception class
- ASFDownloadError exception class
- ASFBaselineError exception class
- Better path/frame/platform/product example


### Changed
- No longer uses range type for parameters that accept lists of values and/or ranges. Now expects a 2-value tuple.
- Removed DATASET constants (not searchable, use platform+instrument to identify a dataset)
- Updated hello_world.py baseline example
- Removed output options across the board, geojson only until we no longer rely on SearchAPI calls
- insarStackID now a search option (needed for baseline stacking of pre-calculated datasets)
- Flatter structure for constants
- baseline functionality moved into search group (file restructuring)

### Fixed
- Corrected handling of version number in user agent string
- unused import cleanup
- better type hinting on centroid() function

------
## [0.2.4](https://github.com/asfadmin/Discovery-asf_search/compare/v0.0.0...v0.2.4)

### Added
- product_search(): search using a list of Product IDs (CMR's GranuleUR)
- granule_search(): search using a list of Granule names (aka Scene names)
- geo_search(): search using a WKT string, as well as other parameters
- search(): a generic search function, allowing any combination of the above search features
- stack(): provides basic Baseline stacking functionality (does not yet provide perpendicular/temporal baseline values)
- Numerous constants available, covering common BEAMMODE, DATASET, FLIGHT_DIRECTION, PLATFORM, POLARIZATION, and PRODUCT_TYPE values
- Basic exception classes and error handling for search parameter and server errors
- Populated readme with instructions, examples, and badges

### Changed
- Improved packaging/build process
- Restructured branch layout according to https://gist.github.com/digitaljhelms/4287848

### Fixed
- Removed hard-coded version string
- Install setuptools_scm in pypi publish action

------
