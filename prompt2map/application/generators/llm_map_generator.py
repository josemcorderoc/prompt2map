import logging
from typing import Any, Callable, Optional
import geopandas as gpd

from prompt2map.application.maps.choropleth_map import choropleth_map
from prompt2map.interfaces.core.map_generator import MapGenerator
from prompt2map.interfaces.nlp.llm import LLM
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
    ]


def create_choropleth_map(data: gpd.GeoDataFrame, title: str, value_column: str) -> Map:
    return choropleth_map(data, value_column, title, "folium")

available_functions: dict[str, Callable[..., Map]] = {
    "create_choropleth_map": create_choropleth_map,
    # "create_bar_chart_map": create_bar_chart_map,   
}

class LLMMapGenerator(MapGenerator):
    def __init__(self, llm: LLM, tools: Optional[Callable[[gpd.GeoDataFrame], list[dict[str, Any]]]] = None, functions: Optional[dict[str, Callable[..., Map]]] = None) -> None:
        if functions is None:
            functions = available_functions
        if tools is None:
            tools = get_available_tools
            
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm = llm
        self.tools = tools
        self.functions = functions
    
    def generate(self, prompt: str, data: gpd.GeoDataFrame) -> Optional[Map]:
        prompt = f"Create a map that answer the following question: {prompt}"
        return self.llm.function_calling(prompt, system_prompt=None, functions=self.functions, tools=self.tools(data), data=data)
