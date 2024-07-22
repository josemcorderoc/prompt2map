import json
from typing import Optional
from application.interfaces.map_selector import MapSelector
from application.interfaces.streamlit_map import StreamlitMap

import geopandas as gpd

from application.maps.choropleth_map import ChoroplethMapPlotly
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
                            "enum": list(data.columns),
                            "description": "The column to use for the choropleth map",
                        }
                        
                    },
                    "required": ["title", "value_column"],
                },
            }
        },
    ]

def create_choropleth_map(data: gpd.GeoDataFrame, title: str, value_column: str) -> StreamlitMap:
    return ChoroplethMapPlotly(data=data, title=title, value_column=value_column)

available_functions = {
    "create_choropleth_map": create_choropleth_map,}
class GPT4MapSelector(MapSelector):
    def __init__(self, gpt4: GPT4) -> None:
        self.gpt4 = gpt4
        
    def select_map(self, query: str, data: gpd.GeoDataFrame) -> Optional[StreamlitMap]:
        prompt = f"Create a map that answer the following question: {query}"
        tools = get_available_tools(data)
        tool_calls = self.gpt4.function_calling(prompt, system_prompt=None, tools=tools)
        if tool_calls is None or len(tool_calls) == 0:
            return None
        
        
        tool_call = tool_calls[0]
        function_name = tool_call.function.name
        tool_match = next((tool for tool in tools if tool["function"]["name"] == function_name), None)
        if tool_match is None:
            return None
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        
        

        function_response = function_to_call(
            data=data,
            **{key: value for key, value in function_args.items() if key in tool_match["function"]["parameters"]["properties"].keys()}
            # title=function_args.get("title"),
            # value_column=function_args.get("value_column"),
        )
        
        return function_response
        
        # tool_match = next((tool for tool in tools if tool["function"]["name"] == function_name), None)
        # if tool_match is None:
        #     return None
        
        # function_args = json.loads(tool_call.function.arguments)
        # function_response = function_to_call(
        #     data=data,
        #     **{key: value for key, value in function_args.items() if key in tool_match["function"]["parameters"]["properties"].keys()}
        # )
        
        # return function_response
        