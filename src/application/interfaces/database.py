from typing import Protocol

import geopandas as gpd

class Database(Protocol):
    def run_query(self, query: str) -> list[dict]:
        ...
        
    def get_schema(self) -> str:
        ...
    
    def run_gpd_query(self, query: str) -> gpd.GeoDataFrame:
        ...