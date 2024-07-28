import logging
import folium
import geopandas as gpd
from application.interfaces.database import Database
from application.interfaces.map_selector import MapSelector
from application.interfaces.prompt_mapper import PromptMapper
from application.interfaces.prompt_to_sql_model import PromptToSQLModel
from application.interfaces.streamlit_map import StreamlitMap
from application.interfaces.text_similarity import TextSimilarity
from application.services.sql_query_processor import SQLQueryProcessor, prettify_sql
from application.services.sql_utils import is_read_only_query, to_geospatial_query


class GPT4QuestionMapper(PromptMapper):
    def __init__(self, db: Database, prompt2sql: PromptToSQLModel, map_selector: MapSelector, sql_query_processor: SQLQueryProcessor,
                 test_db: Database) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.prompt2sql = prompt2sql
        self.db = db
        self.map_selector = map_selector
        self.sql_query_processor = sql_query_processor
        self.test_db = test_db
        
    def generate(self, question: str) -> StreamlitMap:
        # generate SQL query
        prompt_sql_query = self.prompt2sql.to_sql(question)
   
        self.logger.info(f"SQL query generated:\n{prettify_sql(prompt_sql_query)}")
        # validate
        if not is_read_only_query(prompt_sql_query):
            raise ValueError(f"Query {prompt_sql_query} is not a read-only query.")
        
        # replace literals
        prompt_sql_query = self.sql_query_processor.replace_literals(prompt_sql_query)
        
        
        self.logger.debug(f"SQL query with literals replaced:\n{prettify_sql(prompt_sql_query)}")
        # add spatial columns
        prompt_sql_query = to_geospatial_query(prompt_sql_query, {"comuna": "geom"})
        
        self.logger.debug(f"SQL query with spatial columns added:\n{prettify_sql(prompt_sql_query)}")
        
        # execute in test db
        self.logger.debug(f"Executing SQL query in test db...")
        self.test_db.run_query(prompt_sql_query)
        self.logger.debug(f"Query executed successfully in test db.")
        
        # execute in real db
        self.logger.debug(f"Executing SQL query...")
        gdf = self.db.run_gpd_query(prompt_sql_query)
        if len(gdf) == 0:
            raise ValueError(f"Query returned no data")
        
        self.logger.info(f"Dataframe generated.\nSize: {len(gdf)}\nColumns: {gdf.columns}")
        
        # TODO clean output data
        
        
        # select map
        map = self.map_selector.select_map(question, gdf)
        if map is None:
            raise ValueError(f"Could not generate map for question {question}")
        return map
        