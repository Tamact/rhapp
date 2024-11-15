import re
from nltk.corpus import stopwords
from pdfminer.high_level import extract_text
import nltk
nltk.download('stopwords')
import streamlit as st
from email.mime.text import MIMEText
import smtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
#pour générer le code des candidats contacté
import random
import string
from database import generate_code


@st.cache_resource
def get_stop_words():
    return set(stopwords.words('french', 'english'))

stop_words = get_stop_words()

def preprocess_text(text):
    """Prétraitement du texte : minuscules, suppression des caractères spéciaux et des stopwords."""
    text = text.lower()
    text = re.sub(r'\W+', ' ', text)
    tokens = text.split()
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

def extract_text_from_pdf(pdf_file):
    """Extraction du texte d'un fichier PDF."""
    try:
        text = extract_text(pdf_file)
        return text
    except Exception as e:
        print("Erreur lors de l'extraction du texte du PDF:", e)
        return ""
    


def is_valid_email(email):
    """Vérifie si l'adresse e-mail a un format valide."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)


    # Définir la fonction pour le thème
def set_app_theme():
    st.markdown("""
        <style>
            .stApp {
                background-color: #ffffff;
                color: #191970;
            }
            /* Ajoutez d'autres styles ici si nécessaire */
        </style>
    """, unsafe_allow_html=True)


# Charger les variables d'environnement
load_dotenv()

#Fonction d'envoi de mails automatiques
def generate_random_code(length=6):
    """Génère un code aléatoire de 6 caractères."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
def send_email(recipient, subject, message_body ,profil):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    code = generate_random_code()
    message_body_with_code = f"{message_body}\n\nVoici votre code d'entretien : {code}"
    
    msg = MIMEMultipart()
    msg['Subject'] = subject 
    msg['From'] = sender
    msg['To'] = recipient
    msg.attach(MIMEText(message_body_with_code, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        st.success("E-mail envoyé avec succès!")
        generate_code(recipient, code, profil) # si le mail pass on enregistre lecode
    except smtplib.SMTPAuthenticationError:
        st.error("Erreur d'authentification SMTP : vérifiez les identifiants.")
    except smtplib.SMTPConnectError:
        st.error("Erreur de connexion SMTP : vérifiez la connexion au serveur SMTP.")
    except Exception as e:
        st.error(f"Erreur lors de l'envoi de l'e-mail : {str(e)}")

