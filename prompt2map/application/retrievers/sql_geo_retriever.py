import logging
from typing import Optional
import geopandas as gpd

from prompt2map.application.prompt2sql.llm_prompt2sql import LLMPrompt2SQL
from prompt2map.application.prompt2sql.sql_query_processor import SQLQueryProcessor
from prompt2map.application.prompt2sql.utils import is_read_only_query, to_geospatial_query
from prompt2map.interfaces.core.geo_retriever import GeoRetriever
from prompt2map.interfaces.sql.geo_database import GeoDatabase
from prompt2map.interfaces.sql.prompt2sql import Prompt2SQL
from prompt2map.providers.openai import OpenAIProvider


class SQLGeoRetriever(GeoRetriever):
    def __init__(self, db: GeoDatabase, prompt2sql: Optional[Prompt2SQL] = None,
                 sql_query_processor: Optional[SQLQueryProcessor] = None,
                 test_db: Optional[GeoDatabase] = None, db_schema: Optional[str] = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
        self.test_db = test_db
        self.sql_query_processor = sql_query_processor
        if prompt2sql is None:
            self.openai_provider = OpenAIProvider()
            self.db_schema = db_schema if db_schema else self.db.get_schema()
            prompt2sql = LLMPrompt2SQL(self.openai_provider, self.db_schema)
        self.prompt2sql = prompt2sql
        
    

    def retrieve(self, query: str) -> gpd.GeoDataFrame:
        # generate sql query
        sql_query = self.prompt2sql.to_sql(query)
        self.logger.info(f"Generated SQL query:\n{sql_query}")
        
        # validate read only
        if not is_read_only_query(sql_query):
            raise ValueError(f"Query {sql_query} is not a read-only query.")
        self.logger.info(f"Query {sql_query} is a read-only query.")
        
        # replace literals
        if self.sql_query_processor:
            sql_query = self.sql_query_processor.replace_literals(sql_query)
        self.logger.info(f"Replaced literals in query. New query:\n{sql_query}")
        
        # add spatial columns
        sql_query = to_geospatial_query(sql_query, {"comuna": "geom"})
        self.logger.info(f"Added spatial columns to query. New query:\n{sql_query}")
        

        # run in test database
        if self.test_db:
            self.test_db.get_geodata(sql_query)
        self.logger.info(f"Query {sql_query} ran in test database.")
        
        # run in production environment
        data = self.db.get_geodata(sql_query)
        self.logger.info(f"Query {sql_query} ran in production database.")
        
        self.sql_query = sql_query
        return data
