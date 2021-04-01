# Changelog

## [0.2.2](https://github.com/asfadmin/Discovery-asf_search/compare/v0.2.1...v0.2.2)

### Fixed
- Pushing null change to test builds

## [0.2.1](https://github.com/asfadmin/Discovery-asf_search/compare/v0.0.1...v0.2.1)

### Added
- product_search(): search using a list of Product IDs (CMR's GranuleUR)
- granule_search(): search using a list of Granule names (aka Scene names)
- geo_search(): search using a WKT string, as well as other parameters
- search(): a generic search function, allowing any combination of the above search features
- stack(): provides basic Baseline stacking functionality (does not yet provide perpendicular/temporal baseline values)
- Numerous constants available, covering common BEAMMODE, DATASET, FLIGHT_DIRECTION, PLATFORM, POLARIZATION, and PRODUCT_TYPE values

### Changed
- Improved packaging/build process

### Fixed
- None