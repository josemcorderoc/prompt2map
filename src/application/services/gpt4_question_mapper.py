import logging
import folium
import geopandas as gpd
from application.interfaces.database import Database
from application.interfaces.map_selector import MapSelector
from application.interfaces.prompt_mapper import PromptMapper
from application.interfaces.prompt_to_sql_model import PromptToSQLModel
from application.interfaces.streamlit_map import StreamlitMap
from application.services.sql_utils import is_read_only_query, to_geospatial_query


class GPT4QuestionMapper(PromptMapper):
    def __init__(self, db: Database, prompt2sql: PromptToSQLModel, map_selector: MapSelector) -> None:
        self.prompt2sql = prompt2sql
        self.db = db
        self.map_selector = map_selector
        
    def generate(self, question: str) -> StreamlitMap:
        # generate SQL query
        prompt_sql_query = self.prompt2sql.to_sql(question)
   
        logging.info(f"SQL query generated:\n{prompt_sql_query}")
        # validate
        if not is_read_only_query(prompt_sql_query):
            raise ValueError(f"Query {prompt_sql_query} is not a read-only query.")
        
        # TODO replace literals
        
        # add spatial columns
        prompt_sql_query = to_geospatial_query(prompt_sql_query, {"comuna": "geom"})
        
        # TODO execute in test db
        
        # execute in real db
        logging.info(f"Executing SQL query: {prompt_sql_query}")
        gdf = self.db.run_gpd_query(prompt_sql_query)
        
        # TODO clean output data
        
        
        # select map
        map = self.map_selector.select_map(question, gdf)
        if map is None:
            raise ValueError(f"Could not generate map for question {question}")
        return map
        