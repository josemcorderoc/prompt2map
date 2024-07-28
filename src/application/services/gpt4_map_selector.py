import json
import logging
from typing import Optional
from application.interfaces.map_selector import MapSelector
from application.interfaces.streamlit_map import StreamlitMap

import geopandas as gpd

from application.maps.bar_chart_map import BarChartMap
from application.maps.choropleth_map import ChoroplethMap
from infrastructure.gpt4 import GPT4

def get_available_tools(data: gpd.GeoDataFrame):
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
        {
            "type": "function",
            "function": {
                "name": "create_bar_chart_map",
                "description": "Create a bar chart map",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value_columns": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": list(data.select_dtypes(include='number').columns)
                            },
                            "description": "The columns that will turn bars in the map.",
                        }
                        
                    },
                    "required": ["value_columns"],
                },
            }
        },
    ]

def create_choropleth_map(data: gpd.GeoDataFrame, title: str, value_column: str) -> StreamlitMap:
    # TODO check if any processing is needed
    return ChoroplethMap(data=data, title=title, value_column=value_column)

def create_bar_chart_map(data: gpd.GeoDataFrame, value_columns: list[str]) -> StreamlitMap:
    return BarChartMap(data=data, value_columns=value_columns)

available_functions = {
    "create_choropleth_map": create_choropleth_map,
    "create_bar_chart_map": create_bar_chart_map,   
}
class GPT4MapSelector(MapSelector):
    def __init__(self, gpt4: GPT4) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gpt4 = gpt4
        
    def select_map(self, query: str, data: gpd.GeoDataFrame) -> Optional[StreamlitMap]:
        prompt = f"Create a map that answer the following question: {query}"
        tools = get_available_tools(data)
        tool_calls = self.gpt4.function_calling(prompt, system_prompt=None, tools=tools)
        if tool_calls is None or len(tool_calls) == 0:
            self.logger.error("No tool calls found")
            return None
        self.logger.info(f"Tool calls: {tool_calls}")
        
        tool_call = tool_calls[0]  # TODO: Select the best tool call 
        self.logger.info(f"Selected tool call: {tool_call}")
        
        function_name = tool_call.function.name
        tool_match = next((tool for tool in tools if tool["function"]["name"] == function_name), None)
        if tool_match is None:
            return None
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        self.logger.info(f"Function args: {function_args}")
        

        function_response = function_to_call(
            data=data,
            **{key: value for key, value in function_args.items() if key in tool_match["function"]["parameters"]["properties"].keys()}
        )
        self.logger.info(f"Function response: {function_response}")
        
        return function_response
