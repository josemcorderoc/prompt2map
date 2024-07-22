
from geopandas.geodataframe import GeoDataFrame
import geopandas as gpd
import psycopg2
from application.interfaces.database import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import text

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
        return gpd.read_postgis(query, self.conn) # type: ignore
       