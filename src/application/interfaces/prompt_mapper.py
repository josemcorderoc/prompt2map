from typing import Protocol

import geopandas as gpd
from application.interfaces.streamlit_map import StreamlitMap


class PromptMapper(Protocol):
    def generate(self, question: str) -> tuple[StreamlitMap, gpd.GeoDataFrame, str]:
        ...