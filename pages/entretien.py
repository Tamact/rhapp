import streamlit as st
import app 
from utils import is_valid_email 
import streamlit.components.v1 as components
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

Title = st.markdown("<h1 style='text-align: center; color: #E1AD01;'>Bienvenue sur la page d'entretien</h1>", unsafe_allow_html=True)

# Create an empty container
MailForm = st.empty()
checkingCode = st.empty()
actual_email = "email"
actual_password = "password"
step=0

# Insert a form in the container
with MailForm.form("login"):
    st.markdown("Entrez Votre mail ")
    email = st.text_input("Email",placeholder="Type Email lors de votre inscriptions")
    # password = st.text_input("Password", placeholder="Code envoyé par mail",type="password")
    submit = st.form_submit_button("suivant")

if submit and email == actual_email :
    # If the form is submitted and the email and password are correct,
    # clear the form/container and display a success message
    MailForm.empty()
    st.success("Next step")
    step=1
        
            
elif submit and email != actual_email :
    st.error("Login failed")
    st.info("Please enter your email address")
else:
    pass

# le new formulaire
if step == 1:
    with checkingCode.form("code"):
        st.markdown("Entrez le code qui vous a été envoyés")
        password = st.text_input("Password", placeholder="Code envoyé par mail",type="password")
        submit2 = st.form_submit_button("Commencer l'entretien")
            
    if submit2 and password == actual_password:
                checkingCode.empty()
                MailForm.empty()
                st.success("l'entretien va demaré")
    elif submit2 and password != actual_password:
                st.toast("Mauvais code ou Pas d'entretien pour le moment")