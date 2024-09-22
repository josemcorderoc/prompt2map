from typing import Optional
from typing_extensions import Self
import geopandas as gpd

from prompt2map.application.generators.openai_map_generator import OpenAIMapGenerator
from prompt2map.application.prompt2sql.llm_prompt2sql import LLMPrompt2SQL
from prompt2map.application.prompt2sql.sql_query_processor import SQLQueryProcessor
from prompt2map.application.retrievers.sql_geo_retriever import SQLGeoRetriever
from prompt2map.interfaces.core.geo_retriever import GeoRetriever
from prompt2map.interfaces.core.map_generator import MapGenerator
from prompt2map.providers.geoduckdb import GeoDuckDB
from prompt2map.providers.openai import OpenAIProvider
from prompt2map.providers.postgres_db import PostgresDB
from prompt2map.types import Map

class Prompt2Map:
    def __init__(self, retriever: GeoRetriever, generator: MapGenerator) -> None:
        self.retriever = retriever
        self.generator = generator
        self.data: Optional[gpd.GeoDataFrame] = None
        self.map: Optional[Map] = None
    
    def to_map(self, prompt: str) -> Map:
        self.data = self.retriever.retrieve(prompt)
        if len(self.data) == 0:
            raise ValueError(f"Could not retrieve data for prompt: {prompt}. The query result was empty.")
        
        self.map = self.generator.generate(prompt, self.data)
        if self.map is None:
            raise ValueError(f"Could not generate map for prompt: {prompt}")
        return self.map

    @classmethod
    def from_postgis(cls, geo_table: str, geo_column: str, db_name: str, db_user: str, db_password: str, db_host: str = "localhost", db_port: int = 5432) -> Self:
        db = PostgresDB(geo_table, geo_column, db_name, db_user, db_password, db_host, db_port)
        openai_provider = OpenAIProvider()
        query_processor = SQLQueryProcessor(db, openai_provider)
        prompt2sql = LLMPrompt2SQL(openai_provider, db.get_schema())
        sql_retrievier = SQLGeoRetriever(db, prompt2sql=prompt2sql, sql_query_processor=query_processor)
        openai_generator = OpenAIMapGenerator(openai_provider)
        return cls(retriever=sql_retrievier, generator=openai_generator)
    
    @classmethod
    def from_file(cls, table_name: str, file_path: str, embeddings_path: str, descriptions_path: str) -> Self:
        db = GeoDuckDB(table_name, file_path, embeddings_path, descriptions_path)
        openai_provider = OpenAIProvider()
        query_processor = SQLQueryProcessor(db, openai_provider)
        prompt2sql = LLMPrompt2SQL(openai_provider, db.get_schema())
        sql_retrievier = SQLGeoRetriever(db, prompt2sql=prompt2sql, sql_query_processor=query_processor)
        openai_generator = OpenAIMapGenerator(openai_provider)
        return cls(retriever=sql_retrievier, generator=openai_generator)
