import streamlit as st
import cv2
import tempfile
import os
from database import *
from utils import set_app_theme
from gtts import gTTS
import wave
import threading
import ffmpeg
import pyaudio
import whisper
# Configuration de la page
st.set_page_config(
    page_title="GTP-Interview Vidéo",
    layout="wide",
    initial_sidebar_state="auto",
)

# Appliquer le thème
set_app_theme()

# Initialiser les variables de session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'mail' not in st.session_state:
    st.session_state.mail = ''
if 'profil' not in st.session_state:
    st.session_state.profil = ''
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0 
if 'responses' not in st.session_state:
    st.session_state.responses = []


# Fonction pour afficher la page de connexion
def login_page():
    st.markdown("<h1 style='text-align: center; color: #E1AD01;'>Bienvenue sur la page d'entretien de Gainde Talent Provider</h1>", unsafe_allow_html=True)

    placeholder = st.empty()
    with placeholder.form("login"):
        st.markdown("**Entrez votre email et le code envoyé par mail.**")
        email = st.text_input("Email", placeholder="Entrez votre email d'inscription")
        password = st.text_input("Code", placeholder="Entrez le code reçu", type="password")
        st.warning("ATTENTION : ce code est à usage unique.")
        submit = st.form_submit_button("Connexion")

    if submit:
        if check_candidat_connexion(email, password):
            use_code_once(email)
            st.session_state.logged_in = True
            st.session_state.mail = email
            st.session_state.profil = get_profil_from_candidate(email)
            placeholder.empty()
            st.success("Connexion réussie.")
            st.rerun()
        else:
            st.error("Échec de la connexion. Veuillez vérifier vos informations.")


# Fonction pour récupérer les questions liées au profil
def get_questions_for_profil(profil):
    result = get_profil_questions(profil)
    return result[0] if isinstance(result[0], list) else [] if result else []


def enregistrer_video_avec_audio(chemin_video, question_index):
    """
    Enregistre une vidéo avec audio après avoir cliqué sur un bouton.
    La capture s'arrête automatiquement après 1 minute.
    """
    st.info(f"Question {question_index + 1}: Cliquez sur 'Commencer l'enregistrement' pour démarrer la vidéo et l'audio.")
    
    if st.button("Commencer l'enregistrement", key=f"start_{question_index}"):
        # Configuration Audio
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 44100
        chunk = 1024
        audio_file = chemin_video.replace(".mp4", ".wav")

        # Initialisation de l'audio
        audio = pyaudio.PyAudio()
        stream = audio.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
        audio_frames = []

        # Initialisation de la vidéo
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Erreur : Impossible d'accéder à la caméra.")
            return

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(chemin_video, fourcc, 20.0, (640, 480))

        stframe = st.empty()
        st.info("Enregistrement en cours... L'enregistrement s'arrêtera automatiquement après 1 minute.")

        # Démarrer l'enregistrement dans des threads parallèles
        def record_audio():
            while recording:
                data = stream.read(chunk)
                audio_frames.append(data)

        recording = True
        audio_thread = threading.Thread(target=record_audio)
        audio_thread.start()

        # Enregistrement vidéo
        start_time = cv2.getTickCount()
        fps = cv2.getTickFrequency()
        recording_duration = 15 * fps  # 15 secondes

        while (cv2.getTickCount() - start_time) < recording_duration:
            ret, frame = cap.read()
            if not ret:
                st.error("Erreur : Impossible de lire le flux de la caméra.")
                break

            out.write(frame)

            # Afficher l'aperçu de la vidéo dans Streamlit
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            stframe.image(frame, channels="RGB", use_container_width=True)

        # Terminer l'enregistrement
        recording = False
        audio_thread.join()

        # Libérer les ressources
        cap.release()
        out.release()
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Sauvegarder l'audio
        with wave.open(audio_file, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(audio.get_sample_size(audio_format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(audio_frames))

        st.success("Enregistrement terminé après 1 minute. Vidéo et audio sauvegardés.")

        # Fusionner la vidéo et l'audio avec FFmpeg
        output_file = chemin_video.replace(".mp4", "_final.mp4")
        try:
            # Charger la vidéo et l'audio en tant qu'entrées FFmpeg
            video_input = ffmpeg.input(chemin_video)  # Fichier vidéo
            audio_input = ffmpeg.input(audio_file)    # Fichier audio

            # Fusionner la vidéo et l'audio dans un fichier de sortie
            ffmpeg.output(video_input, audio_input, output_file, vcodec='copy', acodec='aac').run(overwrite_output=True)

            st.success("Vidéo et audio fusionnés avec succès.")

            # Télécharger la vidéo fusionnée
            with open(output_file, "rb") as file:
                video_bytes = file.read()
            st.download_button(
                label="Télécharger la vidéo fusionnée",
                data=video_bytes,
                file_name=os.path.basename(output_file),
                mime="video/mp4",
                key=f"download_{question_index}"
            )
        except Exception as e:
            st.error(f"Erreur lors de la fusion de la vidéo et de l'audio : {e}")

def extract_audio_from_video(video_path, audio_path):
    """
    Extrait l'audio d'une vidéo et le sauvegarde dans un fichier audio.
    :param video_path: Chemin de la vidéo d'entrée.
    :param audio_path: Chemin pour sauvegarder l'audio.
    """
    ffmpeg.input(video_path).output(audio_path, format="wav").run(overwrite_output=True)
    print(f"Audio extrait : {audio_path}")



def transcribe_audio_with_whisper(audio_path):
    """
    Transcrit l'audio en texte à l'aide de Whisper.
    :param audio_path: Chemin vers le fichier audio.
    :return: Texte transcrit.
    """
    model = whisper.load_model("medium")  # Choisissez un modèle : tiny, base, small, medium, large
    result = model.transcribe(audio_path,language='fr')
    return result["text"]

def charte_confidentialite():
    """
    Affiche la charte de confidentialité et les dispositions avant de commencer l'entretien.
    L'utilisateur doit accepter les conditions pour accéder à l'entretien.
    """
    st.markdown("<h2 style='text-align: center; color: #E1AD01;'>Charte de Confidentialité</h2>", unsafe_allow_html=True)
    st.write("""
    En participant à cet entretien, vous acceptez les conditions suivantes :
    
    - Vos données personnelles (y compris les enregistrements vidéo) seront utilisées uniquement pour le traitement de votre candidature.
    - Ces données ne seront pas partagées avec des tiers non autorisés.
    - Une fois le traitement terminé, toutes vos données personnelles seront définitivement supprimées.

    ### Dispositions à prendre avant de commencer l'entretien :
    1. Assurez-vous d'être dans un endroit calme et bien éclairé.
    2. Vérifiez que votre caméra et microphone fonctionnent correctement.
    3. Lisez attentivement les questions avant d'y répondre.
    4. Parlez de manière claire et concise.
    """)

    # Bouton pour accepter les conditions
    if st.checkbox("Je reconnais avoir lu et accepté les conditions mentionnées ci-dessus."):
        st.session_state.confidentiality_accepted = True
        st.success("Merci d'avoir accepté les conditions. Vous pouvez maintenant commencer l'entretien.")
    
    # Bouton pour passer à l'entretien
    if st.session_state.get("confidentiality_accepted"):
        if st.button("Passer à l'entretien"):
            st.session_state.ready_for_interview = True

# Fonction pour convertir une question en fichier audio
def generate_audio(question_text):
    """
    Génère un fichier audio pour une question donnée.
    """
    tts = gTTS(text=question_text, lang="fr")  
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio_file.name)
    return temp_audio_file.name
# test
def enregistrer_video_avec_audio_et_transcription(chemin_video, question_index):
    """
    Enregistre une vidéo avec audio, fusionne les flux, et effectue la transcription de l'audio.
    """
    # Appeler la logique d'enregistrement de la vidéo et de l'audio existante
    enregistrer_video_avec_audio(chemin_video, question_index)

    # Transcription de l'audio
    audio_file = chemin_video.replace(".mp4", ".wav")  # Fichier audio généré précédemment
    if os.path.exists(audio_file):
        st.info("Transcription en cours...")
        transcription = transcribe_audio_with_whisper(audio_file)
        st.text_area("Transcription de l'entretien :", transcription, height=300)
    else:
        st.error("Erreur : le fichier audio est introuvable pour la transcription.")

def main_page():
    # Initialiser les variables de session si elles n'existent pas
    if 'confidentiality_accepted' not in st.session_state:
        st.session_state.confidentiality_accepted = False
    if 'ready_for_interview' not in st.session_state:
        st.session_state.ready_for_interview = False

    # Si la charte n'est pas encore acceptée, afficher la charte
    if not st.session_state.ready_for_interview:
        charte_confidentialite()
        return

    # Afficher les questions si la charte est acceptée
    st.markdown(f"<h1 style='text-align: center; color: #E1AD01;'>Bienvenue sur la page d'entretien de Gainde Talent Provider, Profil : {st.session_state.profil}</h1>", unsafe_allow_html=True)

    # Récupérer les questions
    questions = get_questions_for_profil(st.session_state.profil)
    if not questions:
        st.warning("Aucune question trouvée pour ce profil.")
        return

    current_question = st.session_state.current_question
    if current_question < len(questions):
        question = questions[current_question]
        st.write(f"### Question {current_question + 1}: {question}")


        # Générer le fichier audio pour la question
        audio_file_path = generate_audio(question)

        # Ajouter un lecteur audio pour la question
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")


        # Fichier temporaire unique pour la vidéo
        video_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

        # Démarrer l'enregistrement vidéo avec l'index de la question
        enregistrer_video_avec_audio_et_transcription(video_temp_file, question_index=current_question)

        # Passer à la question suivante
        if st.button("Question Suivante", key=f"next_{current_question}"):
            st.session_state.responses.append({
                "question": question,
                "video": video_temp_file
            })
            st.session_state.current_question += 1
            st.rerun()
    else:
        st.success("Vous avez répondu à toutes les questions.")
        st.write("Merci pour votre participation !")# Logout button
        if st.button("Déconnexion"):
            st.session_state.pop("logged_in")  # Remove the logged_in session variable
            st.session_state.pop("mail")
            st.session_state.pop("profil")
            st.session_state.pop("responses")
            st.session_state.pop("current_question")
            st.rerun() 
        # st.stop()


# Affichage de la page selon l'état de connexion
if st.session_state.logged_in:
    main_page()
else:
    login_page()
