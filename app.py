import logging
import os

import pyproj
import sqlparse
import streamlit as st
from dotenv import load_dotenv
from prompt2map import Prompt2Map
from streamlit import session_state as ss
from streamlit_folium import folium_static

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')

for attribute in ["map", "data", "query"]:
    if attribute not in ss:
        ss[attribute] = None

        
def main(question_mapper: Prompt2Map):
    st.set_page_config(
        page_title="MapGPT",
    )
    st.title("Map generation using LLMs")
    
    def create_map():
        prompt_input = ss["user_input"]
        logging.info(f"Creating map for: {prompt_input}")
        
        ss["map"] = question_mapper.to_map(prompt_input)
        ss["query"] = question_mapper.retriever.sql_query # type: ignore
        ss["data"] = question_mapper.data
        
    with st.form('form', clear_on_submit=False):
        st.text_area("""Olá! Sou um modelo de inteligência artificial especializado no Censo 2021 de Portugal. 
            Posso gerar mapas com base nas suas perguntas sobre os dados do censo. Faça uma pergunta e veja o que posso descobrir!""",
            key="user_input", placeholder="Exemplo: Qual é a percentagem de mulheres nas freguesias de Lisboa?")
        st.form_submit_button("Criar mapa 🗺️", on_click=create_map)
        
    if ss.map:
        map_tab, data_tab, sql_tab = st.tabs(["Map", "Data", "SQL"])
        with map_tab:
            st_data = folium_static(ss.map)
            
        with data_tab:
            st.dataframe(ss["data"].select_dtypes(exclude=['geometry']))
            
        with sql_tab:
            st.code(sqlparse.format(ss["query"], reindent=True, keyword_case='upper'), language="sql")
        
        
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

    mapper = Prompt2Map.from_postgis("comuna", "geom", db_name=db_name, db_user=db_user, db_password=db_password)
    main(mapper)
