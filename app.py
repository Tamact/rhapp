import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from utils import preprocess_text, extract_text_from_pdf, is_valid_email, set_app_theme, send_email, generate_questions
from data_processing import store_vectors_in_qdrant, compute_cosine_similarity, store_offer_vector_in_qdrant, load_models, highlight_best_candidates
from visualization import plot_results, plot_pie_chart
from filtre import filter_cvs_by_skills, filter_cvs_by_results
import base64
from io import StringIO
import numpy as np
from database import *
import time


# Définir le thème
st.set_page_config(
    page_title="GTP",
    page_icon="",
    layout="wide",
    initial_sidebar_state="auto",
)


poids_kano = {
    "Indispensable": 1,
    "Attractive": 2,
    "Proportionnelle": 3,
    "Indifferent": 0,
    "Double-tranchant": -1
}

def main():

    set_app_theme()
    

    cvs_texts = []
    cv_files = []

    

    st.image("logo.png", width=300)
    st.caption("GTP: Force intérieure, succés extérieur")   
        
    # Barre de navigation
    selected = option_menu( 
        menu_title="M E N U", 
        options=["Accueil", "Importer CV", "Importer Offre", "Calculer Similarité", "Gestion de la base de données", "Gestion de suivi des candidats", "Génération de questions d'entretien"],
        icons=["house", "upload", "file-earmark-text", "calculator", "database", "stars", "chat"],
        menu_icon="cast",  
        default_index=0,  
        orientation="horizontal", 
        styles={
            "container": {"padding": "0!important", "background-color": "#F0F2D6"},  # Couleur de fond du menu
            "icon": {"color": "#191970", "font-size": "20px"},  # Style des icônes
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#E1AD01"},
            "nav-link-selected": {"background-color": "#E1AD01"},  # Couleur de l'option sélectionnée
                    },
        ) 
    session_state = st.session_state
    

    if selected == "Accueil":
        st.markdown("<h1 style='text-align: center; color: #E1AD01;'>Analyse intelligente de CVs et d'offres d'emploi</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #191970;'>""Simplifiez vos recrutements, optimisez votre sélection de candidats"".</h3>", unsafe_allow_html=True)

        st.write("### Bienvenue dans l'application d'analyse de similarité entre CVs et offre d'emploi.")
        st.write("### Fonctionnalités principales :")
        st.write("""
        - **Importez** vos CVs et l'offre d'emploi rapidement.
        - **Analysez** la similarité entre chaque CV et l'offre grâce à la **similarité cosinus**.
        - **Visualisez** les résultats avec un tableau de bord interactif.
        - **Filtrez** les CVs par compétences.
        - **Suivez** et recommandez des candidats via l'application.
        """)

        st.write("### Guide rapide :")
        st.write("""
        1. **Importer CV** : Ajoutez les CVs des candidats.
        2. **Importer Offre** : Ajoutez une offre d'emploi.
        3. **Résultats** : Voyez le taux de similarité entre CVs et l'offre.
        4. **Filtrer** : Affinez votre sélection par compétences.
        5. **Tableau de bord** : Aperçu global des résultats.
        """)

        st.markdown("<h3 style='text-align: center; color: #191970;'>Prêt à trouver le bon talent ? Commencez maintenant !</h3>", unsafe_allow_html=True)
   
    if selected =="Importer CV":
        st.header("Importer les CVs")
        cv_files = st.file_uploader("Téléchargez vos CVs (PDF ou TXT ou docx)", type=["pdf", "txt", "docx"], accept_multiple_files=True)

        # Initialiser une liste pour stocker le texte des CVs
        cvs_texts = []
    
        if cv_files:
            # Ajouter les noms des fichiers CVs dans une liste pour la sélection
            cv_names = [cv_file.name for cv_file in cv_files]

            # Utiliser une liste déroulante pour sélectionner un CV
            selected_cv_name = st.selectbox("Sélectionnez un CV à visualiser", cv_names)

            # Afficher le contenu du CV sélectionné
            cv_text=""
            for cv_file in cv_files:
                if cv_file.name == selected_cv_name:
                    st.subheader(cv_file.name)
                    if cv_file.type == "application/pdf":
                        pdf_data = cv_file.getvalue()

                        st.markdown(f'<iframe src="data:application/pdf;base64,{base64.b64encode(pdf_data).decode()}" width="700" height="500"></iframe>', unsafe_allow_html=True)
                        cv_text = extract_text_from_pdf(cv_file)
            # Enregistrer CVs
            nom = st.text_input("Nom *", placeholder="Entrez votre nom", key="nom", help="Nom du candidat") 
            prenom = st.text_input("Prénom *", placeholder="Entrez votre prénom", key="prenom", help="Prénom du candidat")
            mail = st.text_input("Adresse Mail", placeholder="Entrez votre adresse mail ", key="mail", help="Adresse e-mail valide")
            numero_tlfn= st.text_input("Numéro de téléphone", placeholder="Entrez votre numéro de téléphone", key="numero tlfn", help="Numéro de téléphone du candidat")
            competences = st.text_area("Compétences *", placeholder="Entrez les compétences séparées par des virgules", key="competences", help="Liste des compétences du candidat")
            
            cv_text = extract_text_from_pdf(cv_file)
        
            if st.button("Enregistrer CV"):
                if not nom or not prenom:
                    st.error("Veuillez renseigner les informations du propriétaire.")
                elif not is_valid_email(mail):
                    st.error("Veuillez entrer une adresse e-mail valide.")
                else:
                    try:
                        preprocessed_cv_text = preprocess_text(cv_text)
                        # Enregistrement des informations de l'utilisateur
                        user_id = save_to_user(nom, prenom, mail, numero_tlfn)

                        if user_id:  
                            competences_list = [competence.strip() for competence in competences.split(",")]
                            cv_id = save_to_cv(user_id, preprocessed_cv_text, competences_list)
                
                            if cv_id:
                                st.success("CV enregistré avec succès.")
                            else:
                                st.error("Erreur lors de l'enregistrement du CV.")
                        else:
                            st.error("Erreur lors de l'enregistrement du candidat.")
                    except Exception as e:
                        st.error(f"Une erreur s'est produite : {e}")
        

    if selected =="Importer Offre":
    #Importer offre
        st.header("Importer l'Offre d'Emploi")
        offer_type = st.radio("Comment souhaitez-vous fournir l'offre d'emploi ?", ("Texte", "Fichier"))

        if offer_type == "Texte":
            titre = st.text_input("Titre *", placeholder="Entrez le titre", key="titre", help="Titre de l'offre")
            offre_societe = st.text_input("Nom de la société *", placeholder="Entrez le nom de la sociéte", key="societe", help="Nom de la sociéte qui a fait l'offre")
            text_offre = st.text_area("Collez le texte de l'offre d'emploi ici", height=300)
            
        else:
            titre = st.text_input("Nom de l'offre")
            offre_societe = st.text_input("Nom de la société")
            offer_file = st.file_uploader("Téléchargez l'offre d'emploi (PDF ou TXT)", type=["pdf", "txt"])
            text_offre = ""
            if offer_file is not None:
                if offer_file.type == "application/pdf":
                    text_offre = extract_text_from_pdf(offer_file)
                elif offer_file.type == "text/plain":
                    stringio = StringIO(offer_file.getvalue().decode("utf-8"))
                    text_offre = stringio.read()
                else:
                    st.error("Format de fichier non supporté pour l'offre d'emploi.")

        #Enregistrer offre dans la bd
        if st.button("Enregistrer l'offre"):
            
            if not titre or not offre_societe:
                st.error("Veuillez renseigner tous les champs")
            else:
                try:
                    preprocess_offre_text = preprocess_text(text_offre)

                    offre_id = save_to_offre(preprocess_offre_text, offre_societe, titre)
                    if offre_id:  
                        st.success("Offre enregistré avec succés.")
                    else:
                        st.error("Erreur lors de l'enregistrement de loffre.")

                except Exception as e:
                    st.erro(f"Une erreur s'est produite : {e}")

    if selected =="Calculer Similarité":

        cvs_texts = []

        st.header("Calcul de similarité entre CVs et offre")
        # Récupérer les CVs et offres d'emploi
        cvs = get_all_cvs()  
        for cv in cvs:
            if cv['competences'] is None:  # Vérifie si competences est None
                cv['competences'] = []  # Initialise comme une liste vide
        offres = get_all_offres() 
        cv_options = {(cv["nom"], cv["prenom"]): cv["cv_id"] for cv in cvs}

        # Vérifier s'il y a des CVs et des offres
        if not cvs:
            st.error("Aucun CV trouvé dans la base de données.")
            return
        if not offres:
            st.error("Aucune offre d'emploi trouvée dans la base de données.")
            return

        # Sélectionner plusieurs CVs et une seule offre
        selected_cvs = st.multiselect(
            "Sélectionnez un ou plusieurs candidats",
            options=[(cv['nom'], cv['prenom']) for cv in cvs],
            help="Sélectionnez les cvs des candidats pour calculer la similarité"  
        )

        
        selected_offer = st.selectbox("Sélectionnez une Offre d'emploi", [offre['titre'] for offre in offres],
                                      help="Sélectionnez une offre d'emploi pour évaluer la similarités avec les CVs")
        
                # Ajouter la saisie des compétences avec le modèle de Kano
        competences_utilisateur = []
        st.write("### Saisir les Compétences")
        competence_counter = 0

        while True:
            competence = st.text_input(f"Entrez une compétence {competence_counter + 1} (ou laissez vide pour terminer) :", key=f"competence_{competence_counter}")
            if competence:
                kano_category = st.selectbox(f"Sélectionnez la catégorie Kano pour '{competence}':", 
                    options=["Indispensable", "Attractive", "Proportionnelle", "Indifferent", "Double-tranchant"], key=f"kano_category_{competence_counter}")
                competences_utilisateur.append((competence.strip(), kano_category))
                competence_counter += 1 
            else:
                break

        #calculer_similarite(competences_utilisateur)

        # Bouton pour calculer la similarité
        if st.button("Calculer la Similarité"):
            # Vérifier si au moins un CV et une offre ont été sélectionnés
            if not selected_cvs:
                st.error("Veuillez sélectionner au moins un CV.")
                return
            if not selected_offer:
                st.error("Veuillez sélectionner une offre d'emploi.")
                return

            # Récupérer les textes correspondants (déjà prétraités)
            offer_text = next(offre['text_offre'] for offre in offres if offre['titre'] == selected_offer)
            
            # Charger les modèles une seule fois
            model1, model2, model3, model4 = load_models()

            # Calculer les vecteurs de l'offre
            offer_vector = np.concatenate([model1.encode([offer_text]), model2.encode([offer_text]), model3.encode([offer_text]), model4.encode([offer_text])], axis=1)

            results = []

            # Calculer la similarité pour chaque CV sélectionné
            for cv_id in selected_cvs:
                cv = next(cv for cv in cvs if cv['nom'] == cv_id[0] and cv['prenom'] == cv_id[1])
                score_similarite = 0

                for competence, kano_category in competences_utilisateur:
                    if competence in cv['competences']:  # Vérifiez si la compétence est présente dans le CV
                        score_similarite += poids_kano[kano_category]  # Ajoutez le poids selon la catégorie Kano
                score_similarite = min(score_similarite, 1)  

                # Calculer les vecteurs des CVs 
                cv_vectors = np.concatenate([model1.encode([cv['cv_text']]), model2.encode([cv['cv_text']]), model3.encode([cv['cv_text']]), model4.encode([cv['cv_text']])], axis=1)

                # Calculer la similarité cosinus
                similarity = compute_cosine_similarity(cv_vectors[0], offer_vector[0]) + score_similarite/25

                # Stocker le résultat dans une liste pour affichage
                results.append({
                    "Nom du CV": cv_id,
                    "Similarité Cosinus": similarity
                })
                # Tri des résultats par score de similarité
            results.sort(key=lambda x: x["Similarité Cosinus"], reverse=True)
            #return results
            #Stocker vecteur dans la bd qdrant

                #offer_vector = np.concatenate([model1.encode([offer_text]), model2.encode([offer_text]), model3.encode([offer_text])], axis=1).flatten()
                #cv_vectors = np.concatenate([model1.encode([cv_text]), model2.encode([cv_text]), model3.encode([cv_text])], axis=1).flatten()

                #store_vectors_in_qdrant(cv_vectors, [cv_file.name for cv_file in cv_files])# Enregistrer les vecteurs dans Qdrant
                #store_vectors_in_qdrant(cv_vectors, [f"{cv_id[0]}_{cv_id[1]}"])
                #store_offer_vector_in_qdrant(offer_vector, selected_offer)
                #store_offer_vector_in_qdrant(offer_vector, [selected_offer])

            for i, cv_file in enumerate(cv_files):
                similarity = compute_cosine_similarity(cv_vectors[i], offer_vector)
                results.append({"Nom du CV": cv_file.name, "Similarité Cosinus": similarity})

            progress_bar = st.progress(0)
            for perc_completed in range(1, 101):
                time.sleep(0.01)  
                progress_bar.progress(perc_completed)

                # Afficher les résultats
            df_results = pd.DataFrame(results)
            st.dataframe(df_results.style.apply(highlight_best_candidates, axis=1))

            # Afficher le meilleur candidat
            if results:
                best_candidate = results[0]
                st.success(f"Le meilleur candidat est {best_candidate['Nom du CV']} avec une similarité de {best_candidate['Similarité Cosinus']:.4f}")

            # Stocker les résultats dans le session state pour communication
            session_state['df_results'] = df_results
            session_state['cvs_texts'] = cvs_texts
            
            

            # Stocker les résultats dans le session state pour communication
            session_state['df_results'] = df_results
            session_state['cvs_texts'] = cvs_texts

            #st.dataframe(df_results)
            #pyg.walk(df_results)
            
            best_candidate = df_results.iloc[0]
            st.success(f"Le meilleur candidat est {best_candidate['Nom du CV']} avec une similarité de {best_candidate['Similarité Cosinus']:.4f}")

            if 'df_results' in session_state:
            
                st.write("### Tableau de Bord")

        # Calcul des métriques
            total_cvs = len(session_state['df_results'])
            max_similarity = session_state['df_results']['Similarité Cosinus'].max()
            best_candidates_percentage = (len(session_state['df_results'][session_state['df_results']['Similarité Cosinus'] > 0.7]) / total_cvs) * 100 if total_cvs > 0 else 0

            col1, col2, col3 = st.columns(3)
        
            with col1:
                st.markdown(f"<div style='border: 2px solid #E1AD01; padding: 10px; border-radius: 5px;'>"
                            f"<h3>Total CVs Importés</h3><h2>{total_cvs}</h2></div>", unsafe_allow_html=True)
        
            with col2:
                st.markdown(f"<div style='border: 2px solid #E1AD01; padding: 10px; border-radius: 5px;'>"
                        f"<h3>Plus Grande Similarité</h3><h2>{max_similarity:.4f}</h2></div>", unsafe_allow_html=True)
        
            with col3:
                st.markdown(f"<div style='border: 2px solid #E1AD01; padding: 10px; border-radius: 5px;'>"
                        f"<h3>Pourcentage des meilleurs candidats </h3><h2>{best_candidates_percentage:.2f}%</h2></div>", unsafe_allow_html=True)

            plot_results(df_results)

            plot_pie_chart(df_results)

        # Filtrage par compétences ou résultats 
        
        if 'df_results' in session_state:
            st.write("### Filtrer les CVs")
            with st.expander("Options de Filtrage Avancé"):
                filter_type = st.selectbox("Choisissez le type de filtrage", ("Compétences", "Résultats"))

                if filter_type == "Compétences":
                    skills_input = st.text_area("Entrez les compétences à rechercher (séparées par une virgule)", help="Exemple : Python, analyse de données")
                    skills = [skill.strip() for skill in skills_input.split(",")]

                    if st.button("Filtrer par Compétences"):
                        if not skills_input.strip():
                            st.error("Veuillez entrer au moins une compétence.")
                        else:
                            df_results = session_state['df_results']
                            cvs_texts = session_state['cvs_texts']

                            filtered_df = filter_cvs_by_skills(df_results, skills, cvs_texts)

                            if not filtered_df.empty:
                                st.dataframe(filtered_df)
                                plot_results(filtered_df)

                elif filter_type == "Résultats":
                    st.write("Définissez les seuils de filtrage")
                    cosine_threshold = st.slider("Seuil de Similarité Cosinus", 0.0, 1.0, 0.5)
                    num_cvs_to_show = st.slider("Nombre de CVs à afficher", 1, len(session_state['df_results']), 5)

                    if st.button("Filtrer par Résultats"):
                        df_results = session_state['df_results']
                        filtered_df = filter_cvs_by_results(df_results, cosine_threshold, num_cvs_to_show)

                        if not filtered_df.empty:
                            st.dataframe(filtered_df)
                            plot_results(filtered_df)

    elif selected == "Gestion de la base de données":
        st.header("Gestion de la base de données")
        st.write("""Cette page permet d'avoir une vue sur les stockages effectués dans la base de données et d'y apporter des modifications si on le souhaite. 
                    Vous pouvez sélectionner une table à visualiser dans la barre de navigation à gauche""")
        with st.sidebar:
            selected1 = option_menu(
            menu_title="Gestion de la base de données", 
            options=["Gestion des candidats", "Gestion des offres", "Gestion des résultats", "Gestion des cvs"],
            icons=["person", "briefcase", "clipboard-data", "files"],
            menu_icon="database",  
            default_index=0,  
            styles={
                "container": {"padding": "0!important", "background-color": "#F0F2D6"},  
                "icon": {"color": "#191970", "font-size": "20px"}, 
                "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#E1AD01"},
                "nav-link-selected": {"background-color": "#E1AD01"}, 
                        },
            ) 
    
        if selected1 == "Gestion des candidats":   
            st.header("Liste des candidats")

            # Récupérer tous les candidats
            st.session_state.candidat = get_all_candidates()

            # Vérifier si la liste des candidats est vide
            if not session_state.candidat:
                st.write("Aucun candidat trouvé dans la base de données.")
                return

            session_state.candidats_df = pd.DataFrame(session_state.candidat, columns=["user_id", "nom", "prenom", "mail", "numero_tlfn"])
            st.dataframe(session_state.candidats_df)
    
            # Utiliser session_state pour garder en mémoire le candidat sélectionné
            if "selected_candidate" not in st.session_state:
                st.session_state.selected_candidate = None

            # Afficher les candidats dans une liste déroulante pour en sélectionner un
            st.session_state.candidat_selection = st.selectbox(
                "Sélectionnez un candidat à modifier", 
                [f"{c['nom']} {c['prenom']}" for c in session_state.candidat], 
                key="candidate_selectbox"
            )
        
            # Trouver l'enregistrement correspondant au candidat sélectionné
            candidat_selected = next((c for c in session_state.candidat if f"{c['nom']} {c['prenom']}" == session_state.candidat_selection), None)

            # Stocker le candidat sélectionné dans session_state pour éviter de perdre l'état
            st.session_state.selected_candidate = candidat_selected

            if st.session_state.selected_candidate:
                # Afficher les informations actuelles du candidat
                st.write("### Informations actuelles du candidat :")
                st.write(f"**Nom :** {st.session_state.selected_candidate['nom']}")
                st.write(f"**Prénom :** {st.session_state.selected_candidate['prenom']}")
                st.write(f"**Adresse Mail :** {st.session_state.selected_candidate['mail']}")
                st.write(f"**Numéro de téléphone :** {st.session_state.selected_candidate['numero_tlfn']}")

                st.write("### Modifier les informations du candidat :")
                # Champs de texte pré-remplis avec les informations actuelles
                nom = st.text_input("Nom", st.session_state.selected_candidate["nom"], key="nom_input")
                prenom = st.text_input("Prénom", st.session_state.selected_candidate["prenom"], key="prenom_input")
                mail = st.text_input("Adresse Mail", st.session_state.selected_candidate["mail"], key="mail_input")
                numero_tlfn = st.text_input("Numéro de téléphone", st.session_state.selected_candidate["numero_tlfn"], key="phone_input")

                # Bouton pour enregistrer les modifications
                if st.button("Enregistrer les modifications"):
                    updated_data = {
                        "nom": nom,
                        "prenom": prenom,
                        "mail": mail,
                        "numero_tlfn": numero_tlfn,
                    }

                    # Valider les champs avant de mettre à jour
                    if not nom or not prenom:
                        st.error("Veuillez remplir tous les champs.")
                    else:
                        # Mettre à jour l'enregistrement dans la base de données
                        if update_candidate(st.session_state.selected_candidate["user_id"], updated_data):
                            st.success("Informations mises à jour avec succès.")
                            #st.rerun()  
                        else:
                            st.error("Erreur lors de la mise à jour des informations.")
            else:
                st.error("Le candidat sélectionné n'existe pas.")
            
        if selected1 == "Gestion des offres":
            st.header("Liste des offres")

            #Récuper les offres
            st.session_state.offre = get_all_offres()
            if not session_state.offre:
                st.write("Aucune offre trouvée dans la base de données.")
                return

            session_state.offre_df = pd.DataFrame(session_state.offre, columns=["offre_id", "text_offre", "offre_societe", "titre"])
            st.dataframe(session_state.offre_df)
    
            # Utiliser session_state pour garder en mémoire le candidat sélectionné
            if "selected_offre" not in st.session_state:
                st.session_state.selected_offre = None

            # Afficher les candidats dans une liste déroulante pour en sélectionner un
            st.session_state.offre_selection = st.selectbox(
                "Sélectionnez une offre à modifier", 
                [f"{o['titre']} {o['offre_societe']}" for o in session_state.offre], 
                key="offre_selectbox"
            )
        
            # Trouver l'enregistrement correspondant au candidat sélectionné
            offre_selected = next((o for o in session_state.offre if f"{o['titre']} {o['offre_societe']}" == session_state.offre_selection), None)

            # Stocker le candidat sélectionné dans session_state pour éviter de perdre l'état
            st.session_state.selected_offre = offre_selected

            if st.session_state.selected_offre:
                # Afficher les informations actuelles du candidat
                st.write("### Informations actuelles de l'offre :")
                st.write(f"**Nom de l'offre :** {st.session_state.selected_offre['titre']}")
                st.write(f"**Nom de la société:** {st.session_state.selected_offre['offre_societe']}")
                st.write(f"**Text_offre:** {st.session_state.selected_offre['text_offre']}")

                st.write("### Modifier les informations du candidat :")
                # Champs de texte pré-remplis avec les informations actuelles
                titre = st.text_input("Titre", st.session_state.selected_offre["titre"], key="titre_input")
                offre_societe = st.text_input("offre_societe", st.session_state.selected_offre["offre_societe"], key="offreSociete_input")
                text_offre = st.text_area("text_offre", st.session_state.selected_offre["text_offre"], key="textOffre_input", height=300)
                
                # Bouton pour enregistrer les modifications
    
                if st.button("Enregistrer les modifications"):
                    updated_data = {
                        "titre": titre,
                        "offre_societe": offre_societe,
                        "text_offre": text_offre,
                        
                    }

                    # Valider les champs avant de mettre à jour
                    if not titre or not offre_societe:
                        st.error("Veuillez remplir tous les champs.")
                    else:
                        # Mettre à jour l'enregistrement dans la base de données
                        if update_offre(st.session_state.selected_offre["offre_id"], updated_data):
                            st.success("Informations mises à jour avec succès.")
                            #st.rerun()  
                        else:
                            st.error("Erreur lors de la mise à jour des informations.")
            else:
                st.error("""L'offre sélectionnée n'existe pas.""")
        
        if selected1 =="Gestion des résultats":
            st.header("Gestion des résultats")
            st.write("""Cette page est dédiée à la visualisation des résultats""")

            #Récupérer les résultats
            st.session_state.resultat = get_all_resultats()
            if not session_state.resultat:
                st.write("Aucun résultat trouvé dans la base de données.")
                return
    
            session_state.resultat_df = pd.DataFrame(session_state.resultat, columns=["resultat_id", "cv_id", "offre_id", "cosine_similarity"])
            st.dataframe(session_state.resultat_df)

        if selected1 == "Gestion des cvs":
            st.header("Gestion des cvs")
            st.write("""Cette page est dédiée à la visualistion des cvs""")
            
            st.session_state.cv = get_all_cvs()
            if not session_state.cv:
                st.write("Aucun cv trouvé dans la base de données.")
                return
            session_state.cv_df=pd.DataFrame(session_state.cv, columns=["cv_id", "user_id", "date_insertion", "cv_text","competences"])
            st.dataframe(session_state.cv_df)
    
    if selected == "Gestion de suivi des candidats":
        st.header("Gestion de suivi des candidats")

        # Récupérer la liste des candidats
        candidates = get_all_candidates()

        if "selected_candidate" not in  st.session_state:
            # Sélectionner un candidat
            st.session_state.selected_candidate = None
            #selected_candidate = st.session_state.selected_candidate
            selected_candidate = st.selectbox("Choisissez un candidat à évaluer :", candidates)

            # Notation par étoiles
            sentiment_mapping = ["1 étoile", "2 étoiles", "3 étoiles", "4 étoiles", "5 étoiles"]
            selected_rating = st.feedback("stars")

            # Saisie du message de recommandation
            message_body = st.text_area("Message de recommandation")

            
            email = "fabricejordan2001@gmail.com"
            # !test pour avoir le mail du candidat
            # st.write(st.session_state.selected_candidate['mail'])

            if st.button("Envoyer la recommandation"):
                if not selected_rating:
                    st.warning("notez d'abord le candidat")
                elif message_body:
                    # Message d'email
                    email = "fabricejordan2001@gmail.com"
                    email_subject = f"Recommandation pour {selected_candidate}"
                    email_message = f"Vous avez été recommandé avec une note de {sentiment_mapping[selected_rating]}.\n\n{message_body}"
                
                    # Envoi de l'email
                    if send_email(email, email_subject, email_message):
                        st.success("La recommandation a été envoyée avec succès.")
                else:
                    st.warning("Veuillez saisir un message avant d'envoyer la recommandation.")

    if selected == "Génération de questions d'entretien":
        st.header("Génération de Questions d'Entretien")
        profile = st.text_area("Entrez le profil du candidat (ex: Data scientist avec 3 ans d'expérience en Machine Learning)")

        if st.button("Générer des questions d'entretien"):
            if profile:
                questions = generate_questions(profile, num_questions=10)
                st.subheader("Questions générées :")
                for i, question in enumerate(questions, 1):
                    st.write(f"{i}. {question}")
            else:
                st.warning("Veuillez entrer le profil du candidat pour générer les questions.")



if __name__ == "__main__":
    main()



