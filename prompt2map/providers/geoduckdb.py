
import logging
import os
from typing import Any
import duckdb
import geopandas as gpd
import pandas as pd
from prompt2map.interfaces.sql.geo_database import GeoDatabase

class GeoDuckDB(GeoDatabase):
    def __init__(self, table_name: str, file_path: str, embeddings_path: str, descriptions_path: str, 
                 geo_agg_function: str = "ST_Union_Agg") -> None:
        self.table_name = table_name
        self.file_path = file_path
        self.embeddings_path = embeddings_path
        self.descriptions_path = descriptions_path
        self.geo_agg_function = geo_agg_function
        
        self.embeddings_table_name = "embeddings"
        self.descriptions_table_name = "descriptions"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection = duckdb.connect()
        
        self.connection.install_extension("spatial")
        self.connection.install_extension("httpfs")
        self.connection.load_extension("httpfs")
        self.connection.load_extension("spatial")
        
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        if access_key and secret_key:
            self.connection.execute(f"""
                                CREATE SECRET secret1 (
                                    TYPE S3,
                                    KEY_ID '{access_key}',
                                    SECRET '{secret_key}',
                                    REGION 'us-east-2'
                                );""")
        
        self.connection.execute(f"CREATE TABLE {self.table_name} AS SELECT * FROM '{self.file_path}'")
        self.connection.execute(f"CREATE TABLE {self.embeddings_table_name} AS SELECT * FROM '{self.embeddings_path}'")
        self.connection.execute(f"CREATE TABLE {self.descriptions_table_name} AS SELECT * FROM '{self.descriptions_path}'")
        
        # validate that the main table has a geometry column
        geometry_columns = self.connection.sql(
            f"SELECT name FROM pragma_table_info('{table_name}') WHERE type = 'GEOMETRY';" 
        ).fetchall()
        
        if len(geometry_columns) == 0:
            raise ValueError(f"No geometry columns found in table {self.table_name}")
        elif len(geometry_columns) > 1:
            raise ValueError(f"Multiple geometry columns found in table {self.table_name}")
        
        self.geometry_column = geometry_columns[0][0]
        self.crs = gpd.read_parquet(self.file_path).crs
        
        self.embedding_length = self.connection.sql(f"""SELECT len(values)
                            FROM {self.embeddings_table_name}
                            LIMIT 1;""").fetchall()[0][0]
        
        self.embedding_type = f"DOUBLE[{self.embedding_length}]"
        
    
    
    def get_schema(self) -> str:
        variables_block = self.connection.sql("""
            SELECT string_agg(
                CASE
                    WHEN description IS NULL OR description = '' THEN format('\t{} {}', ti.name, ti.type)
                    ELSE format('\t{} {}, -- {}', ti.name, ti.type, d.description)
                END, '\n')""" + f"""
            FROM pragma_table_info('{self.table_name}') ti
            LEFT JOIN {self.descriptions_table_name} d ON d.column = ti.name
            """).fetchall()[0][0]
        
        create_table_statement = f"""CREATE TABLE {self.table_name} (\n{variables_block}\n);"""
        return create_table_statement

    def get_geodata(self, query: str) -> gpd.GeoDataFrame:
        result = self.connection.sql(query)
        df = self.connection.sql(f"""SELECT  
                            * EXCLUDE ({self.geometry_column}),
                            ST_AsText({self.geometry_column}) AS wkt_geom
                        FROM result""").df()
        
        geometry = gpd.GeoSeries.from_wkt(df['wkt_geom'], crs=self.crs)
        gdf = gpd.GeoDataFrame(df.drop(columns=["wkt_geom"]), geometry=geometry)
        return gdf

    def get_literals(self, table: str, column: str) -> list[Any]:
        return [value for (value), in self.connection.sql(f"SELECT DISTINCT {column} FROM {table}").fetchall()]

    def get_most_similar_cosine(self, table: str, column: str, text_embedding: list[float], embedding_suffix: str) -> str:
        self.logger.info(f"table: {table}, column: {column}")
        query = f"""
            SELECT t.{column}
            FROM {table} t
            LEFT JOIN {self.embeddings_table_name} e ON t.{column} = e.text
            ORDER BY array_distance(e.values::{self.embedding_type}, {text_embedding}::{self.embedding_type})
            LIMIT 1;"""
        self.logger.info(f"Executing query: {query}")
        result = self.connection.sql(query).fetchall()
        if len(result) == 0:
            raise ValueError(f"No similar value found in {table}.{column}")
        return result[0][0]
    

    def get_most_similar_levenshtein(self, table: str, column: str, text: str) -> str:
        raise NotImplementedError

    def get_column_type(self, table_name: str, column_name: str) -> str | None:
        field = self.connection.sql(
            f"SELECT type FROM pragma_table_info('{table_name}') WHERE name = '{column_name}' LIMIT 1;" 
        ).fetchall()
        if len(field) == 0:
            return None
        return field[0][0]

    def get_geo_column(self) -> tuple[str, str]:
        return self.table_name, self.geometry_column

    def get_geo_agg_function(self) -> str:
        return self.geo_agg_function


