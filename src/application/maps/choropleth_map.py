import geopandas as gpd
from streamlit_folium import st_folium

from application.interfaces.streamlit_map import StreamlitMap


class ChoroplethMap(StreamlitMap):
    def __init__(self, data: gpd.GeoDataFrame, value_column: str, cmap='viridis', legend_title='Legend', title='Choropleth Map', height=500, width=500) -> None:       
        self.data = data
        self.value_column = value_column
        
        self.fig = self.data.explore(value_column, cmap=cmap)
      
    def show(self) -> None:
        self.fig.show_in_browser()
    
    def add_to_streamlit(self) -> None:
        st_data = st_folium(self.fig)
