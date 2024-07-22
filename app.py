import logging
from re import I
import sys
from dotenv import load_dotenv
import folium
import pandas as pd
import streamlit as st
from streamlit import session_state as ss
from streamlit_folium import st_folium

from application.interfaces.prompt_mapper import PromptMapper
from application.services.llm_to_sql import LLMToSQL
from application.services.gpt4_map_selector import GPT4MapSelector
from application.services.gpt4_question_mapper import GPT4QuestionMapper
from infrastructure.gpt4 import GPT4
from infrastructure.postgres_db import PostgresDB
import os

logging.basicConfig(level=logging.INFO)
sys.path.append("../src")

for attribute in ["plotly_map"]:
    if attribute not in ss:
        ss[attribute] = None

        
def main(question_mapper: PromptMapper):
    st.set_page_config(
        page_title="MapGPT",
    )
    st.title("Map generation using LLMs")
    
    def create_map(prompt_input: str):
        logging.info(f"Creating map for: {prompt_input}")
        ss["plotly_map"] = question_mapper.generate(prompt_input)   

    user_input = st.text_area("Ask me a question", key="user_input")

    if ss.user_input:
        st.button("Create map 🗺️", on_click=create_map, key='classification', args=(user_input,))
        
    if ss.plotly_map:
        map_data = st_folium(ss.plotly_map, width=1000, height=500)

if __name__ == "__main__":
    load_dotenv()
    
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")

    if db_name is None or db_user is None or db_password is None:
        raise ValueError("Please set the DB_NAME, DB_USER, and DB_PASSWORD environment variables.")
    
    db = PostgresDB(db_name=db_name, db_user=db_user, db_password=db_password)
    db_schema = db.get_schema()
    # logging.info(f"Database schema:\n{db_schema}")
    gpt4 = GPT4()
    gpt2sql = LLMToSQL(llm=gpt4, db_schema=db_schema)
    gpt4_mapselector = GPT4MapSelector(gpt4=gpt4)
    gpt4_question_mapper = GPT4QuestionMapper(db=db, prompt2sql=gpt2sql, map_selector=gpt4_mapselector)
    main(gpt4_question_mapper)
