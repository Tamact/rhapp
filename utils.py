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

#Fonction d'envoi de mails automatiques

def send_email(recipient, subject, message_body):
    sender = "ibrahimasorysane986@gmail.com"  
    password = "SidietRamavontal'écolechaquemardia8h."  

    # Création du message de recommandation
   #msg = MIMEText(f"Cher candidat,\n\nVous avez été recommandé pour une opportunité.\n\nCordialement,\nL'équipe de recrutement GTP")
    #msg = MIMEText(message_body ,_charset="utf-8")
    msg = MIMEMultipart()
    msg['Subject'] = subject 
    msg['From'] = sender
    msg['To'] = recipient
    msg.attach(MIMEText(message_body, 'plain', 'utf-8'))

    try:
        # Initialisation du serveur SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  
            server.starttls()  
            server.login(sender, password) 
            server.send_message(msg)  
        st.success("E-mail envoyé avec succès!")
    except Exception as e:
        st.error(f"Erreur lors de l'envoi de l'e-mail: {str(e)}")

def calculer_similarite(competences_utilisateur):
    poids_kano = {
        "Must-be": 2,        # Poids élevé
        "One-dimensional": 1, # Poids normal
        "Attractive": 1,      # Poids normal
        "Indifferent": 0,     # Pas de poids
        "Reverse": -1         # Peut réduire la similarité
    }

