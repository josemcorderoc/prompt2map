from typing import Optional, Protocol
import geopandas as gpd

from prompt2map.types import Map


class MapGenerator(Protocol):
    def generate(self, prompt: str, data: gpd.GeoDataFrame) -> Optional[Map]:
        ...