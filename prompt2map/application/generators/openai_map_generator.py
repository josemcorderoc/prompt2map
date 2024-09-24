import logging
from typing import Any, Callable, Optional
import geopandas as gpd

from prompt2map.application.maps.choropleth_map import choropleth_map
from prompt2map.interfaces.core.map_generator import MapGenerator
from prompt2map.providers.openai import OpenAIProvider
from prompt2map.types import Map

def get_available_tools(data: gpd.GeoDataFrame) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "create_choropleth_map",
                "description": "Create a choropleth map",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the map",
                        },
                        "value_column": {
                            "type": "string",
                            "enum": list(data.select_dtypes(include='number').columns),
                            "description": "The column to use for the choropleth map",
                        }
                        
                    },
                    "required": ["title", "value_column"],
                },
            }
        },
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "create_bar_chart_map",
        #         "description": "Create a bar chart map",
        #         "parameters": {
        #             "type": "object",
        #             "properties": {
        #                 "value_columns": {
        #                     "type": "array",
        #                     "items": {
        #                         "type": "string",
        #                         "enum": list(data.select_dtypes(include='number').columns)
        #                     },
        #                     "description": "The columns that will turn bars in the map.",
        #                 }
                        
        #             },
        #             "required": ["value_columns"],
        #         },
        #     }
        # },
    ]


def create_choropleth_map(data: gpd.GeoDataFrame, title: str, value_column: str) -> Map:
    # TODO check if any processing is needed
    return choropleth_map(data, value_column, title, "folium")

# def create_bar_chart_map(data: gpd.GeoDataFrame, value_columns: list[str]) -> Map:
#     return BarChartMap(data=data, value_columns=value_columns)

available_functions: dict[str, Callable[..., Map]] = {
    "create_choropleth_map": create_choropleth_map,
    # "create_bar_chart_map": create_bar_chart_map,   
}

class OpenAIMapGenerator(MapGenerator):
    def __init__(self, openai: Optional[OpenAIProvider] = None, tools: Optional[Callable[[gpd.GeoDataFrame], list[dict[str, Any]]]] = None, functions: Optional[dict[str, Callable[..., Map]]] = None) -> None:
        if functions is None:
            functions = available_functions
        if openai is None:
            openai = OpenAIProvider()
        if tools is None:
            tools = get_available_tools
            
        self.logger = logging.getLogger(self.__class__.__name__)
        self.openai = openai
        self.tools = tools
        self.functions = functions
    
    def generate(self, prompt: str, data: gpd.GeoDataFrame) -> Optional[Map]:
        prompt = f"Create a map that answer the following question: {prompt}"
        return self.openai.function_calling_python(prompt, system_prompt=None, functions=self.functions, tools=self.tools(data), data=data)
