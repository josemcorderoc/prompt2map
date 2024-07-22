import json
import geopandas as gpd
from matplotlib import pyplot as plt
import numpy as np
import streamlit as st

import plotly.express as px
from application.interfaces.streamlit_map import StreamlitMap


class ChoroplethMap(StreamlitMap):
    def __init__(self, data: gpd.GeoDataFrame, value_column: str, cmap='viridis', legend_title='Legend', title='Choropleth Map', height=500, width=500) -> None:       
        self.data = data
        self.value_column = value_column
        self.cmap = cmap
        self.legend_title = legend_title
        self.title = title
        
        bounds = self.data.total_bounds  # [minx, miny, maxx, maxy]
        center = {
            "lat": (bounds[1] + bounds[3]) / 2,
            "lon": (bounds[0] + bounds[2]) / 2
        }
        
        max_bound = max(abs(bounds[0]-bounds[2]), abs(bounds[1]-bounds[3])) * 111
        zoom = 11.5 - np.log(max_bound)

        self.fig = px.choropleth_mapbox(
            self.data,
            geojson=json.loads(self.data.to_json()),
            locations=self.data.index,
            color=self.value_column,
            color_continuous_scale=self.cmap,
            title=self.title,
            mapbox_style="open-street-map",
            center=center,
            zoom=zoom,
            height=height,
            width=width
        )

        # Fit the map bounds to the locations
        self.fig.update_geos(fitbounds="locations", visible=False)
        self.fig.update_layout(coloraxis_colorbar=dict(title=self.legend_title))
        self.fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))

        
    def show(self) -> None:
        self.fig.show()
    
    def add_to_streamlit(self) -> None:
        st.plotly_chart(self.fig)
        # st.pyplot(self.fig)
