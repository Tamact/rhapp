import streamlit as st
from utils import is_valid_email, set_app_theme
from PIL import Image
from database import *

img = Image.open("favicon.png")

st.set_page_config(
    page_title="GTP-Interview",
    page_icon=img,
    layout="wide",
    initial_sidebar_state="auto",
)

set_app_theme()


# Initialize session state for login status
# ! si la session existe pas on affiche que le formulaire
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
# ? session state pour récuperer les info du candidat
if 'mail' not in st.session_state:
    st.session_state.mail = ''
# ? session state pour recuperer le profil et afficher les questions correspondantes
if 'profil' not in st.session_state:
    st.session_state.profil = ''
# Function to render login page
def login_page():

    title = st.markdown("<h1 style='text-align: center; color: #E1AD01;'>Bienvenue sur la page d'entretien de Gainde Talent Provider</h1>", unsafe_allow_html=True)
    
    placeholder = st.empty()  # Placeholder for the form

    # Insert a form in the container
    with placeholder.form("login"):
        st.markdown("Entrez Votre mail et le code qui vous a été envoyés",help="ATTENTION CE CODE EST A USAGE UNIQUE")
        email = st.text_input("Email", placeholder="Type Email lors de votre inscription")
        password = st.text_input("Password", placeholder="Code envoyé par mail", type="password")
        submit = st.form_submit_button("Login")

    # Login validation
    if submit:
        if check_candidat_connexion(email, password):
            # Set session state to logged in and clear form
            use_code_once(email)
            st.session_state.logged_in = True
            st.session_state.mail= email
            st.session_state.profil = get_profil_from_candidate(st.session_state.mail)
            print("session profil:",st.session_state.profil)
            
            placeholder.empty()
            # print("varuable session:",email)
            st.success("Login successful")
            st.rerun()  # Force page reload
        else:
            st.error("Login failed")

# Function to render the main content after login
def main_page():
    st.markdown("<h1 style='text-align: center; color: #E1AD01;'>Veuillez répondre au question d'entretien technique pour un profil de: </h1>" , unsafe_allow_html=True)  # Example content
    st.header(st.session_state.profil)
    # Add other functionalities here
     # Logout button
    if st.button("Déconnexion"):
        st.session_state.pop("logged_in")  # Remove the logged_in session variable
        st.session_state.pop("mail")
        st.rerun()  # Reload the page to go back to login page

# Check login status and display appropriate page
if st.session_state.logged_in:
    main_page()
else:
    login_page()
