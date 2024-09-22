from typing import Optional
import folium
from matplotlib import pyplot as plt
import pandas as pd
from shapely import MultiPolygon, Polygon
import geopandas as gpd
import plotly.express as px

from prompt2map.types import Map


def average_bounding_boxes(s: gpd.GeoSeries) -> tuple[float, float]:
    miny, minx, maxy, maxx = s.bounds.mean()
    width = maxx - minx
    height = maxy - miny
    return width, height

def bar_chart(df: gpd.GeoDataFrame, values_cols: list[str], **kwargs) -> gpd.GeoSeries:
    
    charts = df.apply(lambda row: draw_bar_polygon(row["geom"], [row[col] for col in values_cols], float(df[values_cols].max(axis=None)), scale=average_bounding_boxes(df.geom), **kwargs), axis=1)
    return gpd.GeoSeries(charts, crs=df.crs)


def bar_chart_gdf(df: gpd.GeoDataFrame, values_cols: list[str], **kwargs) -> gpd.GeoDataFrame:
    bar_chart_s = bar_chart(df, values_cols, **kwargs)
    bars = pd.DataFrame(bar_chart_s.apply(lambda poly: poly.geoms).to_list(), columns=values_cols, index=bar_chart_s.index).rename_axis("category", axis=1).unstack()
    bar_values = df[values_cols].rename_axis("category", axis=1).unstack()
    gdf = gpd.GeoDataFrame(bar_values.rename("value"), geometry=bars, crs=df.crs).reset_index()
    return gdf

def draw_bar_polygon(polygon: Polygon, bar_values: list[float], max_value: float, scale: tuple[float, float] = (1, 1), offset: tuple[float, float] = (0, 0)) -> MultiPolygon:
    """Receives a polyhon and values for bars and returns a MultiPolygon with the bar for a bar chart.
    The bar chart should be draw in the received order and should be centered in the polygon centroid.

    Args:
        polygon (Polygon): polygon where the bar chart will be drawn
        bar_values (list[float]): values for the bars in the bar chart. 
        scale (tuple[float, float]): scale factor for the bar chart. The first value is the bar width
            and the second value is the height scale.
        offset (tuple[float, float]): x,y centering offset

    Returns:
        MultiPolygon: len(bar_values) bar chart polygons
    """
    

    # Unpack the scale tuple
    width, height = scale
 
    height = height/2   
    width = width/2   
    # cx, cy = centroid.x, centroid.y
    cx, cy = polygon.centroid.x + offset[0], polygon.centroid.y + offset[1] - height/2
    
    bar_width = width / len(bar_values)
    height_scale = height / max_value
    # Calculate the total width of the bar chart
    # total_width = len(bar_values) * bar_width

    # Calculate the starting x position for the first bar (centered)
    start_x = cx - width/2

    # Create a list to hold the bar polygons
    bar_polygons = []

    for i, value in enumerate(bar_values):
        # Calculate the height of the bar
        bar_height = value * height_scale

        # Create the bar polygon (a rectangle)
        bar = Polygon([
            (start_x + i * bar_width, cy),
            (start_x + (i + 1) * bar_width, cy),
            (start_x + (i + 1) * bar_width, cy + bar_height),
            (start_x + i * bar_width, cy + bar_height),
            (start_x + i * bar_width, cy)
        ])

        # Append the bar polygon to the list
        bar_polygons.append(bar)

    # Create and return the MultiPolygon
    return MultiPolygon(bar_polygons)

def plot_polygons(polygons):
    fig, ax = plt.subplots()
    
    for polygon in polygons:
        if isinstance(polygon, Polygon):
            x, y = polygon.exterior.xy
            ax.plot(x, y)
        else:
            for interior in polygon.interiors:
                x, y = interior.xy
                ax.plot(x, y)
    
    ax.set_aspect('equal')
    plt.show()
    
class BarChartMap:
    def __init__(self, data: gpd.GeoDataFrame, value_columns: list[str], height=500, width=500, colors: Optional[list[str]] = None) -> None:
        self.data = data
        self.value_columns = value_columns
        self.height = height
        self.width = width
        
        self.fig = folium.Map()
        self.raw_bars = bar_chart(data, value_columns)
        self.bars = bar_chart_gdf(data, value_columns)
        
        if colors is None:
            colors = px.colors.qualitative.Plotly[:len(value_columns)]
        colors_cols = dict(zip(value_columns, colors))
        
        def style(feature):
            return {
                'fillColor': colors_cols.get(feature['properties']['category']),
                'fillOpacity': 0.8,
                'color': 'black',
                'opacity': 1
            }

        folium.GeoJson(data, tooltip=folium.GeoJsonTooltip(fields=["nombre"], aliases=["Nombre"], localize=True)).add_to(self.fig)
        folium.GeoJson(self.bars, style_function=style, tooltip=folium.GeoJsonTooltip(
            fields=["category", "value"],
            aliases=["Candidato", "Valor"],
            localize=True)
        ).add_to(self.fig)
        
        self.fig.fit_bounds(self.fig.get_bounds())
            
    def show(self) -> None:
        self.fig.show_in_browser()
