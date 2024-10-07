from typing import TypeVar
import folium
import matplotlib.axes
import matplotlib.figure
import plotly.graph_objects as go

Map = folium.Map | go.Figure | matplotlib.axes.Axes | matplotlib.figure.Figure

T = TypeVar('T')


__all__ = ['Map']
