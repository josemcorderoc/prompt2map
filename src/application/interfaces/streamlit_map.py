from typing import Protocol

import geopandas as gpd

class StreamlitMap(Protocol):
    def show(self) -> None:
        ...
    def add_to_streamlit(self) -> None:
        ...