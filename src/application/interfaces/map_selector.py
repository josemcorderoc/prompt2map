
from typing import Optional, Protocol

from application.interfaces.streamlit_map import StreamlitMap
import geopandas as gpd

class MapSelector(Protocol):
    def select_map(self, query: str, data: gpd.GeoDataFrame) -> Optional[StreamlitMap]:
        ...