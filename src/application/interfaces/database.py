from typing import Any, Optional, Protocol

import geopandas as gpd

class Database(Protocol):
    def run_query(self, query: str) -> list[dict]:
        ...
        
    def get_schema(self) -> str:
        ...
    
    def run_gpd_query(self, query: str) -> gpd.GeoDataFrame:
        ...
    
    def get_literals(self, table: str, column: str) -> list[Any]:
        ...
        
    def get_literals_multi(self, tables_columns: list[tuple[str, str]]) -> dict[tuple[str, str], list[Any]]:
        ...
        
    def get_most_similar_cosine(self, table: str, column: str, text_embedding: list[float], embedding_suffix: str) -> str:
        ...
        
    def get_most_similar_levenshtein(self, table: str, column: str, text: str) -> str:
        ...

    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        ...