import logging
from typing import Optional
import geopandas as gpd

from prompt2map.application.prompt2sql.sql_query_processor import SQLQueryProcessor
from prompt2map.application.prompt2sql.utils import is_read_only_query, to_geospatial_query
from prompt2map.interfaces.core.geo_retriever import GeoRetriever
from prompt2map.interfaces.sql.geo_database import GeoDatabase
from prompt2map.interfaces.sql.prompt2sql import Prompt2SQL


class SQLGeoRetriever(GeoRetriever):
    def __init__(self, db: GeoDatabase, prompt2sql: Prompt2SQL,
                 sql_query_processor: Optional[SQLQueryProcessor] = None,
                 test_db: Optional[GeoDatabase] = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
        self.test_db = test_db
        self.sql_query_processor = sql_query_processor
        self.prompt2sql = prompt2sql

    def retrieve(self, query: str) -> gpd.GeoDataFrame:
        # generate sql query
        sql_query = self.prompt2sql.to_sql(query)
        self.logger.info(f"Generated SQL query:\n{sql_query}")
        
        # validate read only
        if not is_read_only_query(sql_query):
            raise ValueError(f"Query is not a read-only query.")
        self.logger.info(f"Query is a read-only query.")
        
        # replace literals
        if self.sql_query_processor:
            sql_query = self.sql_query_processor.replace_literals(sql_query)
            self.logger.info(f"Replaced literals in query. New query:\n{sql_query}")
        
        # add spatial columns
        geotable_name, geocolumn_name = self.db.get_geo_column()
        sql_query = to_geospatial_query(sql_query, geotable_name, geocolumn_name, self.db.get_geo_agg_function())
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
