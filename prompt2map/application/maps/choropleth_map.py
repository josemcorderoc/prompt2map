
from typing import Literal, overload
import folium
import geopandas as gpd
import numpy as np
import plotly.graph_objects as go
import matplotlib.figure
import matplotlib.axes

from prompt2map.types import Map

@overload
def choropleth_map(data: gpd.GeoDataFrame, value_column: str, title: str, provider: Literal["folium"]) -> folium.Map: ...

@overload
def choropleth_map(data: gpd.GeoDataFrame, value_column: str, title: str, provider: Literal["plotly"]) -> go.Figure: ...

@overload
def choropleth_map(data: gpd.GeoDataFrame, value_column: str, title: str, provider: Literal["matplotlib"]) -> matplotlib.axes.Axes | matplotlib.figure.Figure: ...

def choropleth_map(data: gpd.GeoDataFrame, value_column: str, title: str, provider: Literal["folium", "plotly", "matplotlib"], cmap='viridis') -> Map:
    if provider == "folium":
        fig = data.explore(value_column, cmap=cmap, title=title, scheme="NaturalBreaks")
    elif provider == "plotly":
        import plotly.express as px
        geom_all = data.geometry.union_all()
        minx, miny, maxx, maxy = geom_all.bounds
        max_bound = max(abs(maxx-minx), abs(maxy-miny)) * 111
        zoom = 13 - np.log(max_bound)
        fig = px.choropleth_mapbox(data, 
                                geojson=data.to_geo_dict(), 
                                locations=data.index,
                                color="N_INDIVIDUOS", 
                                mapbox_style="carto-positron", 
                                center={"lat": geom_all.centroid.y, "lon": geom_all.centroid.x},
                                zoom=zoom,
                                opacity=0.8,
                                title=title
                                )
        fig.update_geos(fitbounds="locations")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        return fig
    elif provider == "matplotlib":
        fig = data.plot(column=value_column, legend=True, title=title)
        return fig
    else:
        raise ValueError("Invalid provider")
    return fig
