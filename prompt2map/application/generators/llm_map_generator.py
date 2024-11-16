import logging
from typing import Any, Callable, Optional
import folium
import geopandas as gpd

from prompt2map.interfaces.core.map_generator import MapGenerator
from prompt2map.interfaces.nlp.llm import LLM
from prompt2map.types import Map

def get_available_tools(data: gpd.GeoDataFrame) -> list[dict[str, str | dict]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "create_colored_map",
                "description": "Create a map with the selected column colored",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "color_column": {
                            "type": "string",
                            "enum": list(data.select_dtypes(include="number").columns),
                            "description": "This columns represents the variable that answers the user question. It will be used to color the map",
                        }
                    },
                    "required": ["color_column"],
                },
            }
        },
    ]


def colored_map(data: gpd.GeoDataFrame, value_column: str, is_categorical: bool = False) -> folium.Map:
    cmap = 'viridis'
    if is_categorical:
        data[value_column] = data[value_column].astype("category")
        possible_values = len(data[value_column].value_counts(dropna=False))
        if possible_values <= 10:
            cmap = 'tab10'
        elif possible_values <= 20:
            cmap = 'tab20'
        else:
            data[value_column] = data[value_column].apply(lambda x: x if x in data[value_column].value_counts().nlargest(19).index else 'Other')
            cmap = 'tab20'
        return data.explore(value_column, cmap=cmap)
    return data.explore(value_column, cmap=cmap, scheme="NaturalBreaks")

def create_colored_map(data: gpd.GeoDataFrame, color_column: str, is_categorical: bool = False) -> Map:
    return colored_map(data, color_column, is_categorical)

available_functions: dict[str, Callable[..., Map]] = {
    "create_colored_map": create_colored_map,
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
        self.function_args: Optional[dict] = None
        self.function_response: Optional[Map] = None
    
    def generate(self, prompt: str, data: gpd.GeoDataFrame) -> Optional[Map]:
        prompt = f"Create a map that answer the following question: {prompt}"
        result = self.llm.function_calling(prompt, system_prompt=None, functions=self.functions, tools=self.tools(data), data=data)
        if result is not None:
            self.function_response, self.function_args = result
            return self.function_response
        return None
        
