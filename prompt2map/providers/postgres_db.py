
from typing import Any, Optional
from geopandas.geodataframe import GeoDataFrame
import geopandas as gpd
import numpy as np
import pandas as pd
import psycopg
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import json

from prompt2map.interfaces.sql.geo_database import GeoDatabase

class PostgresDB(GeoDatabase):
    def __init__(self, geo_table: str, geo_column: str, db_name: str, db_user: str, 
                 db_password: str, db_host: str = "localhost", db_port: int = 5432,
                 geo_agg_function: str = "ST_Union") -> None:
        self.geo_table = geo_table
        self.geo_column = geo_column
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.geo_agg_function = geo_agg_function
        # self.conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        self.create_connection()
        # Create an engine to be reused for database connections
        self.engine = create_engine(f'postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}')

    def create_connection(self):
        return psycopg.connect(dbname=self.db_name, user=self.db_user, password=self.db_password, host=self.db_host, port=self.db_port)
        

    def get_schema(self) -> str:
        with self.create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """)
                
                tables = cursor.fetchall()
                
                create_statements = []
                
                # For each table, construct the CREATE TABLE statement
                for table in tables:
                    table_name = table[0]
                    
                    # Get columns and their types
                    cursor.execute(f"""
                    SELECT column_name, data_type, character_maximum_length, column_default, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    """)
                    
                    columns = cursor.fetchall()
                    
                    create_statement = f"CREATE TABLE {table_name} (\n"
                    column_definitions = []
                    
                    for column in columns:
                        column_name = column[0]
                        data_type = column[1]
                        char_length = column[2]
                        column_default = column[3]
                        is_nullable = column[4]
                        
                        column_def = f"  {column_name} {data_type}"
                        if char_length:
                            column_def += f"({char_length})"
                        # if column_default:
                        #     column_def += f" DEFAULT {column_default}"
                        if is_nullable == 'NO':
                            column_def += " NOT NULL"
                        
                        column_definitions.append(column_def)
                    
                    create_statement += ",\n".join(column_definitions)
                    create_statement += "\n);"
                    
                    create_statements.append(create_statement)
                return "\n".join(create_statements)

    def get_geodata(self, query: str) -> GeoDataFrame:
        with self.create_connection() as conn:
            return gpd.read_postgis(query, conn)  # type: ignore

    def get_literals(self, table: str, column: str) -> list[Any]:
        return pd.read_sql(f"SELECT DISTINCT {column} FROM {table}", con=self.engine)[column].to_list()

    def get_most_similar_cosine(self, table: str, column: str, text_embedding: list[float], embedding_suffix: str) -> str:
        embedding_str = json.dumps(text_embedding,  separators=(',', ':'))

        query = f"""
            SELECT {column} 
            FROM {table} 
            ORDER BY {column}__{embedding_suffix} <=> '{embedding_str}' 
            LIMIT 1;"""
            
        result = pd.read_sql(query, con=self.engine)[column].iloc[0]
        if len(result) == 0:
            raise ValueError(f"No similar value found in {table}.{column}")
        
        return result
    
    def get_most_similar_levenshtein(self, table: str, column: str, text: str) -> str:
        query = f"""
            SELECT {column} 
            FROM {table} 
            ORDER BY levenshtein({column}, %s) 
            LIMIT 1;"""
        result = pd.read_sql(query, con=self.engine, params=(text,))
        result_value = result[column].iloc[0]
        
        if len(result) == 0 or result_value is None:
            raise ValueError(f"No similar value found in {table}.{column}")
        
        return result_value

    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        query = """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s;
        """
        with self.create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (table_name, column_name))
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None

    def get_geo_column(self) -> tuple[str, str]:
        return self.geo_table, self.geo_column

    def get_geo_agg_function(self) -> str:
        return self.geo_agg_function

    def value_in_column(self, table: str, column: str, value: str) -> bool:
        return len(pd.read_sql(f"SELECT 1 FROM {table} WHERE {column} = %s LIMIT 1;", 
                           con=self.engine, params=(value,))) > 0