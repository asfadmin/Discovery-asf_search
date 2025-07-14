from collections import deque
import requests
from typing import Any, List, Dict

from .exceptions import (
    InvalidMultiBurstCountError,
    MultipleOrbitError,
    InvalidMultiBurstTopologyError,
    AntimeridianError
)
import numpy as np


class MultiBurst:
    """
    MultiBurst is a helper class that geographically validates collections of Sentinel-1 bursts in 
    preparation of ordering multi-burst interferograms from HyP3
    """

    def __init__(self, multiburst_dict):
        """
        multiburst_dict: 
            keys: string burst ID
            values: tuple of included string subswaths
            e.g. {"burst_ID_1": ("IW1",), "burst_ID_2": ("IW1", "IW2", "IW3")}
        """
        self.multiburst_dict = multiburst_dict
        self.burst_ids = [f"{burst}_{swath}" for 
                          burst, swaths in self.multiburst_dict.items()
                          for swath in swaths]
        self.burst_metadata = self._get_burst_metadata()
        self._validate_multi_burst_dict()
        self.extent_wkt = self._get_extent_wkt()

    def _validate_multi_burst_dict(self):
        """
        Geographically validates a collection of bursts to ensure that
        they will be suitable for processing with HyP3.

        Raises an Exception upon encountering any issues.

        Based on these considerations for selecting multiple bursts:
        https://hyp3-docs.asf.alaska.edu/guides/burst_insar_product_guide/#considerations-for-selecting-input-bursts

        - Sets of bursts must contain 1-15 bursts
        - Burst collection must be contiguous
        - Bursts collections cannot contain holes
        - Bursts crossing the Antimeridian are not supported
        """
        if not 0 < len(self.burst_ids) <= 15:
            msg = (
                "HyP3 supports multiburst jobs of size 1-15.\n"
                f"multiburst_dict contains {len(self.burst_ids)} bursts"
            )
            raise InvalidMultiBurstCountError(msg)

        orbital_paths = set([id.split("_")[0] for id in self.multiburst_dict.keys()])
        if len(orbital_paths) > 1:
            msg = (
                "All bursts must belong to the same orbital path.\n"
                f"multiburst_dict contains burst with the following paths: {orbital_paths}"
            )
            raise MultipleOrbitError(msg)

        component_count, hole_count = self.count_components_and_holes()
        if component_count > 1 or hole_count > 0:
            msg = (
                "Multiburst collections must be comprised of a single connected component and have no holes.\n"
                f"Connected Components: {component_count}, Holes: {hole_count}"
            )
            raise InvalidMultiBurstTopologyError(msg)

        if self._intersects_antimeridan():
            raise AntimeridianError("No bursts can intersect the Antimeridian")

    def _build_grid(self):
        """
        Builds a burst-swath mask indicating which are included in the collection of bursts
        """
        grid = []
        for burst_id, swaths in sorted(self.multiburst_dict.items()):
            include_list = []
            for swath in ["IW1", "IW2", "IW3"]:
                if swath in swaths:
                    include_list.append(True)
                else:
                    include_list.append(False)
            grid.append(include_list)
        return grid
    
    def count_components_and_holes(self):
        """
        Performs a BFS search to count connected components and holes
        
        This could be simplified by using scipy or Networkxx for BFS,
        but doing it without avoids adding either as a required dependency
        """
        grid = np.array(self._build_grid(), dtype=bool)
        visited = np.zeros_like(grid, dtype=bool)
        nrows, ncols = grid.shape

        component_count = 0
        hole_count = 0

        # 8-connectivity
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1)
            ]
        
        # # 4-connectivity
        # directions = [
        #              (-1, 0),
        #     (0, -1),         (0, 1),
        #              (1, 0)
        #     ]

        for r in range(nrows):
            for c in range(ncols):
                if visited[r, c]:
                    continue

                queue = deque([(r, c)])
                visited[r, c] = True
                value = grid[r, c]

                if value:  # on pixel → part of a component
                    component_count += 1
                    while queue:
                        y, x = queue.popleft()
                        for dy, dx in directions:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < nrows and 0 <= nx < ncols:
                                if grid[ny, nx] and not visited[ny, nx]:
                                    visited[ny, nx] = True
                                    queue.append((ny, nx))
                else:  # off pixel → possible hole
                    touches_border = (r == 0 or r == nrows-1 or c == 0 or c == ncols-1)
                    region = [(r, c)]
                    while queue:
                        y, x = queue.popleft()
                        for dy, dx in directions:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < nrows and 0 <= nx < ncols:
                                if not grid[ny, nx] and not visited[ny, nx]:
                                    visited[ny, nx] = True
                                    queue.append((ny, nx))
                                    region.append((ny, nx))
                                    if ny == 0 or ny == nrows-1 or nx == 0 or nx == ncols-1:
                                        touches_border = True
                    if not touches_border:
                        hole_count += 1

        return component_count, hole_count
    
    def get_burst_ids(self) -> List[str]:
        """
        Returns a list of full burst IDs (burst+swath) for every included burst
        """
        return [f"{burst}_{swath}" for burst, swaths in self.multiburst_dict.items() for swath in swaths]

    def _get_burst_metadata(self) -> List[Dict[str, Any]]:
        """
        Collects BURSTMAP metadata from CMR for each included burst

        Returns a list of metadata for each incuded burst
        """
        s1_burst_map_collection_id = "C2450786986-ASF"

        burst_metadata = []
        for burst_id in self.burst_ids:
            burstmap_id = f"S1_{burst_id}-BURSTMAP"

            response = requests.get(
                "https://cmr.earthdata.nasa.gov/search/granules.umm_json",
                params={
                    "collection_concept_id": s1_burst_map_collection_id,
                    "granule_ur": burstmap_id,
                    "page_size": 1
                }
            )
            response.raise_for_status()
            burst_metadata.append(response.json())
        return burst_metadata

    def _intersects_antimeridan(self) -> bool:
        """
        Examines all burst metadata and determines if any inersect the Antimeridian

        Returns False if no bursts intersect Antimeridian else True
        """
        for data in self.burst_metadata:
            if len(data['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons']) == 2:
                for point in (data['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']
                              ['Geometry']['GPolygons'][0]['Boundary']['Points']):
                    if point['Longitude'] == 180.0:
                        return True
                for point in (data['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']
                              ['Geometry']['GPolygons'][1]['Boundary']['Points']):
                    if point['Longitude'] == -180.0:
                        return True
        return False

    def _get_extent_wkt(self) -> str:
        """
        Returns a Well-Known-Text (WKT) string polygon of the
        maximum extents (rectangular) for the collection of muti-bursts 
        """
        burst_extents = [
            data['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']
                ['GPolygons'][0]['Boundary']['Points']
            for data in self.burst_metadata
            ]

        min_lat = min([p['Latitude'] for extent in burst_extents for p in extent])
        max_lat = max([p['Latitude'] for extent in burst_extents for p in extent])
        min_lon = min([p['Longitude'] for extent in burst_extents for p in extent])
        max_lon = max([p['Longitude'] for extent in burst_extents for p in extent])

        return (
            f"POLYGON(({min_lon} {min_lat},"
            f"{max_lon} {min_lat},"
            f"{max_lon} {max_lat},"
            f"{min_lon} {max_lat},"
            f"{min_lon} {min_lat}))"
        )
