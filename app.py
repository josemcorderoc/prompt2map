import logging
from re import I
import sys
import folium
import pandas as pd
import streamlit as st
from streamlit import session_state as ss
from streamlit_folium import st_folium

from application.interfaces.question_mapper import QuestionMapper
from application.services.gpt4_question_mapper import GPT4QuestionMapper

logging.basicConfig(level=logging.INFO)
sys.path.append("../src")

for attribute in ["plotly_map"]:
    if attribute not in ss:
        ss[attribute] = None

        
def main(question_mapper: QuestionMapper):
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
    gpt4_question_mapper = GPT4QuestionMapper()
    main(gpt4_question_mapper)
