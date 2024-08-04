from typing import Protocol

import geopandas as gpd

class GeoRetriever(Protocol):
    def retrieve(self, query: str) -> gpd.GeoDataFrame:
        ...