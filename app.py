import logging
import os
from pathlib import Path
from re import I

import pyproj
import streamlit as st
from dotenv import load_dotenv
from streamlit import session_state as ss

from application.interfaces.prompt_mapper import PromptMapper
from application.services.gpt4_map_selector import GPT4MapSelector
from application.services.gpt4_question_mapper import GPT4QuestionMapper
from application.services.llm_to_sql import LLMToSQL
from application.services.sql_query_processor import SQLQueryProcessor, prettify_sql
from infrastructure.gpt4 import GPT4
from infrastructure.postgres_db import PostgresDB

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')

for attribute in ["map", "data", "query"]:
    if attribute not in ss:
        ss[attribute] = None

        
def main(question_mapper: PromptMapper):
    st.set_page_config(
        page_title="MapGPT",
    )
    st.title("Map generation using LLMs")
    
    def create_map(prompt_input: str):
        logging.info(f"Creating map for: {prompt_input}")
        
        ss["map"], ss["data"], ss["query"] = question_mapper.generate(prompt_input)   
        logging.info(ss["map"], ss["data"], ss["query"])

    user_input = st.text_area("Ask me a question", key="user_input")

    if ss.user_input:
        st.button("Create map 🗺️", on_click=create_map, key='classification', args=(user_input,))
        
    if ss.map:
        map_tab, data_tab, sql_tab = st.tabs(["Map", "Data", "SQL"])
        with map_tab:
            ss.map.add_to_streamlit()
            
        with data_tab:
            st.dataframe(ss["data"])
            
        with sql_tab:
            st.code(prettify_sql(ss["query"]), language="sql")
        
        
if __name__ == "__main__":
    load_dotenv()
    proj_lib = os.environ.get("PROJ_LIB")
    if proj_lib:
        pyproj.datadir.set_data_dir(proj_lib)
    
    db_name = os.environ.get("DB_NAME")
    test_db_name = os.environ.get("TEST_DB_NAME")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")

    if db_name is None or db_user is None or db_password is None or test_db_name is None:
        raise ValueError("Please set the DB_NAME, DB_USER, DB_PASSWORD, TEST_DB_NAME environment variables.")
    
    db = PostgresDB(db_name=db_name, db_user=db_user, db_password=db_password)
    test_db = PostgresDB(db_name=test_db_name, db_user=db_user, db_password=db_password)
    db_schema = Path("data", "db", "schema.sql").read_text()
    
    gpt4 = GPT4()
    gpt2sql = LLMToSQL(llm=gpt4, db_schema=db_schema)
    gpt4_mapselector = GPT4MapSelector(gpt4=gpt4)
    sql_query_processor = SQLQueryProcessor(db=db, embedding=gpt4)
    gpt4_question_mapper = GPT4QuestionMapper(db=db, prompt2sql=gpt2sql, map_selector=gpt4_mapselector, sql_query_processor=sql_query_processor ,test_db=test_db)
    main(gpt4_question_mapper)
