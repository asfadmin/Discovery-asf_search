# Changelog

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