from collections import deque
import requests

import numpy as np


class MultiBurst:

    def __init__(self, multiburst_dict):
        self.multiburst_dict = multiburst_dict
        self._validate_multi_burst_dict()

    def _validate_multi_burst_dict(self):
        """
        Based on these considerations for selecting multiple bursts:
        https://hyp3-docs.asf.alaska.edu/guides/burst_insar_product_guide/#considerations-for-selecting-input-bursts

        - Sets of bursts can contain 1-15 bursts
        - Burst collection must be contiguous
        - Bursts collections should not contain holes
        - Bursts crossing the Antimeridian are not supported
        """
        if not 0 < len(self.multiburst_dict) <= 15:
            raise Exception((
                "HyP3 supports multiburst jobs of size 1-15.\n"
                f"multiburst_dict contains {len(self.multiburst_dict)} bursts"
                ))

        orbital_paths = set([id.split("_")[0] for id in self.multiburst_dict.keys()])
        if len(orbital_paths) > 1:
            raise Exception((
                "All bursts must belong to the same orbital path.\n"
                f"multiburst_dict contains burst with the following paths: {orbital_paths}"
            ))

        component_count, hole_count = self.count_components_and_holes()
        if component_count > 1 or hole_count > 0:
            raise Exception((
                "Multiburst collections must be comprised of a single connected component and have no holes.\n"
                f"Connected Components: {component_count}, Holes: {hole_count}"
            ))

        if self._intersects_antimeridan():
            raise Exception("No bursts can intersect the Antimeridian")

    def _build_grid(self):
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
        Performs BFS searches to count connected components and holes
        
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
    
    def _intersects_antimeridan(self):
        s1_burst_map_collection_id = "C2450786986-ASF"

        burst_ids = [f"{burst}_{swath}" for
                     burst, swaths in self.multiburst_dict.items()
                     for swath in swaths]
        
        for burst_id in burst_ids:
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
            data = response.json()

            if len(data['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons']) == 2:
                for point in data['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][0]['Boundary']['Points']:
                    if point['Longitude'] == 180.0:
                        return True
                for point in data['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][1]['Boundary']['Points']:
                    if point['Longitude'] == -180.0:
                        return True
        return False
