from typing import Any, Optional, Protocol

import geopandas as gpd

class GeoDatabase(Protocol):
    def get_schema(self) -> str:
        ...
    
    def get_geodata(self, query: str) -> gpd.GeoDataFrame:
        ...
    
    def get_literals(self, table: str, column: str) -> list[Any]:
        ...
        
    def get_most_similar_cosine(self, table: str, column: str, text_embedding: list[float], embedding_suffix: str) -> str:
        ...
        
    def get_most_similar_levenshtein(self, table: str, column: str, text: str) -> str:
        ...

    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        ...