import streamlit as st
import app 

st.set_page_config(
    page_title="GTP",
    page_icon=app.img,
    layout="wide",
    initial_sidebar_state="auto",
)

app.set_app_theme()
st.header(
    "Page d\'entretien"
)

st.markdown("<h1 style='text-align: center; color: #E1AD01;'>Bienvenue sur la page d'entretien</h1>", unsafe_allow_html=True)

