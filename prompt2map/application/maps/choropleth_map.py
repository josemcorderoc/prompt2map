import geopandas as gpd

from prompt2map.interfaces.core.map import Map

class ChoroplethMap(Map):
    def __init__(self, data: gpd.GeoDataFrame, value_column: str, cmap='viridis', legend_title='Legend', title='Choropleth Map', height=500, width=500) -> None:       
        self.data = data
        self.value_column = value_column
        
        self.fig = self.data.explore(value_column, cmap=cmap)
      
    def show(self) -> None:
        self.fig.show_in_browser()
    
    def _repr_html_(self):
        return self.fig._repr_html_()