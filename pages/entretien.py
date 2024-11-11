import streamlit as st
from utils import is_valid_email, set_app_theme
from PIL import Image

img = Image.open("favicon.png")

st.set_page_config(
    page_title="GTP-Interview",
    page_icon=img,
    layout="wide",
    initial_sidebar_state="auto",
)

set_app_theme()

# Define the actual login credentials
actual_email = "email"
actual_password = "password"

# Initialize session state for login status
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Function to render login page
def login_page():

    title = st.markdown("<h1 style='text-align: center; color: #E1AD01;'>Bienvenue sur la page d'entretien de Gainde Talent Provider</h1>", unsafe_allow_html=True)
    
    placeholder = st.empty()  # Placeholder for the form

    # Insert a form in the container
    with placeholder.form("login"):
        st.markdown("Entrez Votre mail et le code qui vous a été envoyés")
        email = st.text_input("Email", placeholder="Type Email lors de votre inscription")
        password = st.text_input("Password", placeholder="Code envoyé par mail", type="password")
        submit = st.form_submit_button("Login")

    # Login validation
    if submit:
        if email == actual_email and password == actual_password:
            # Set session state to logged in and clear form
            st.session_state.logged_in = True
            placeholder.empty()
            st.success("Login successful")
            st.rerun()  # Force page reload
        else:
            st.error("Login failed")

# Function to render the main content after login
def main_page():
    st.write("Welcome to the main content page!")  # Example content
    # Add other functionalities here
     # Logout button
    if st.button("Déconnexion"):
        st.session_state.pop("logged_in")  # Remove the logged_in session variable
        st.rerun()  # Reload the page to go back to login page

# Check login status and display appropriate page
if st.session_state.logged_in:
    main_page()
else:
    login_page()
