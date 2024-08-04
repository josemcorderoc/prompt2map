from email import generator
from typing import Literal, Optional, Self
import geopandas as gpd

from application.generators.openai_map_generator import OpenAIMapGenerator
from application.prompt2sql.sql_query_processor import SQLQueryProcessor
from application.retrievers.sql_geo_retriever import SQLGeoRetriever
from interfaces.core.geo_retriever import GeoRetriever
from interfaces.core.map import Map
from interfaces.core.map_generator import MapGenerator
from providers.openai import OpenAIProvider
from providers.postgres_db import PostgresDB

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
    def from_postgis(cls, db_name: str, db_user: str, db_password: str, db_host: str = "localhost", db_port: int = 5432, provider: Literal["openai"] = "openai") -> Self:
        db = PostgresDB(db_name, db_user, db_password, db_host, db_port)
        openai_provider = OpenAIProvider()
        query_processor = SQLQueryProcessor(db, openai_provider)
        sql_retrievier = SQLGeoRetriever(db, sql_query_processor=query_processor)
        openai_generator = OpenAIMapGenerator(openai_provider)
        return cls(retriever=sql_retrievier, generator=openai_generator)
    