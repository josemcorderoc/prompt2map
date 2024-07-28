
import re
from typing import Any, Optional
from geopandas.geodataframe import GeoDataFrame
import geopandas as gpd
import numpy as np
import pandas as pd
import psycopg2
from application.interfaces.database import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import text
import json

class PostgresDB(Database):
    def __init__(self, db_name: str, db_user: str, db_password: str, db_host: str = "localhost", db_port: int = 5432) -> None:
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        
        # Create an engine to be reused for database connections
        self.engine = create_engine(f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}')

    def run_query(self, query: str) -> list[dict]:
        with self.engine.connect() as connection:
            
            result = connection.execute(text(query))
            rows = [dict(row) for row in result]
        return rows

    def get_schema(self) -> str:
        with self.conn.cursor() as cursor:
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

    def run_gpd_query(self, query: str) -> GeoDataFrame:
        return gpd.read_postgis(query, self.conn)  # type: ignore

    def get_literals_multi(self, tables_columns: list[tuple[str, str]]) -> dict[tuple[str, str], list[Any]]:
        return { (table, column): self.get_literals(table, column) for table, column in tables_columns }

    def get_literals(self, table: str, column: str) -> list[Any]:
        return pd.read_sql(f"SELECT DISTINCT {column} FROM {table}", con=self.engine)[column].to_list()

    def get_most_similar(self, table: str, column: str, text_embedding: list[float], embedding_suffix: Optional[str]) -> Any:
        # TODO: Implement this method
        embedding_str = json.dumps(text_embedding)
        order_by = column if embedding_suffix is None else column + embedding_suffix
        
        query = f"""SELECT {column} 
        FROM {table} 
        ORDER BY {order_by} <=> '{embedding_str}' LIMIT 1;"""
        result = pd.read_sql(query, con=self.engine)[column].iloc[0]
        if len(result) == 0:
            raise ValueError(f"No similar value found in {table}.{column}")
        return result
    
    def get_most_similar_levenshtein(self, table: str, column: str, text: str) -> str:
        query = f"""SELECT {column} 
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
        with self.conn.cursor() as cursor:
            cursor.execute(query, (table_name, column_name))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None

       