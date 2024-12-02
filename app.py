import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from utils import preprocess_text,is_valid_email, set_app_theme, send_email, generate_questionnaire_google, extract_text_from_pdf, categorize_skills_with_kano
from data_processing import store_vectors_in_qdrant, compute_cosine_similarity, store_offer_vector_in_qdrant, load_models, highlight_best_candidates, load_ai_detector, analyze_text_style, load_references, compare_with_references
from filtre import filter_cvs_by_skills, filter_cvs_by_results
import base64
from io import StringIO
import numpy as np
from database import *
from visualization import *
import time
import asyncio
from async_operations import process_cvs_async, add_candidate_async




# Définir le thème
st.set_page_config(
    page_title="GTP",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="auto",
)
poids_kano = {
    "Indispensable": 5,
    "Attractive": 3,
    "Proportionnelle": 2,
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
            "container": {"padding": "0!important", "background-color": "#F0F2F6"},  # Couleur de fond du menu
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
   
    ai_detector = load_ai_detector()
    reference_texts = load_references()

    if selected == "Importer CV":
        st.header("Importer les CVs")
        cv_files = st.file_uploader("Téléchargez vos CVs (PDF ou TXT ou DOCX)", type=["pdf", "txt", "docx"], accept_multiple_files=True)
        
        if cv_files:
            
            cv_names = [cv_file.name for cv_file in cv_files]

            
            selected_cv_name = st.selectbox("Sélectionnez un CV à visualiser", cv_names)
            
            
            cv_text = ""
            for cv_file in cv_files:
                if cv_file.name == selected_cv_name:
                    st.subheader(cv_file.name)
                    if cv_file.type == "application/pdf":
                        pdf_data = cv_file.getvalue()
                        st.markdown(
                            f'<iframe src="data:application/pdf;base64,{base64.b64encode(pdf_data).decode()}" width="700" height="500"></iframe>',
                            unsafe_allow_html=True
                        )
                        cv_text = extract_text_from_pdf(cv_file)
                    elif cv_file.type in ["text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                        cv_text = cv_file.read().decode("utf-8")
                        st.text_area("Contenu du CV :", cv_text, height=300)

            if cv_text.strip():
                
                st.markdown(
                    """
                    <style>
                    .encadre {
                        border: 2px solid #E1AD01;
                        padding: 15px;
                        border-radius: 10px;
                        margin: 10px;
                        background-color: #f9f9f9;
                    }
                    .titre-analyse {
                        font-size: 20px;
                        font-weight: bold;
                        color: #343a40;
                        margin-bottom: 10px;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                
                col1, col2, col3 = st.columns(3)

                # Détection IA
                with col1:
                    st.markdown('<div class="encadre">', unsafe_allow_html=True)
                    st.markdown('<div class="titre-analyse">Détection IA</div>', unsafe_allow_html=True)
                    with st.spinner("Analyse du contenu pour détecter si le CV est généré par une IA..."):
                        result = ai_detector(cv_text[:512])
                        label = result[0]['label']
                        score = result[0]['score']
                    
                    if label == "generated":
                        st.error(f"⚠️ Ce CV semble être rédigé par une IA avec une probabilité de {score:.2f}.")
                    else:
                        st.success(f"✅ Ce CV semble être rédigé par un humain avec une probabilité de {score:.2f}.")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Analyse du style et de la grammaire
                with col2:
                    st.markdown('<div class="encadre">', unsafe_allow_html=True)
                    st.markdown('<div class="titre-analyse">Analyse du style et de la grammaire</div>', unsafe_allow_html=True)
                    with st.spinner("Analyse du style et de la grammaire du CV..."):
                        style_analysis = analyze_text_style(cv_text)
                    st.write(f"- **Longueur moyenne des phrases** : {style_analysis['avg_sentence_length']:.2f} mots")
                    st.write(f"- **Nombre de phrases** : {style_analysis['num_sentences']}")
                    st.write(f"- **Mots inhabituels (longueur > 12)** : {', '.join(style_analysis['unusual_words']) if style_analysis['unusual_words'] else 'Aucun'}")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Calcul de la similarité
                with col3:
                    st.markdown('<div class="encadre">', unsafe_allow_html=True)
                    st.markdown('<div class="titre-analyse">Indice de similarité</div>', unsafe_allow_html=True)
                    with st.spinner("Calcul de la similarité avec les références..."):
                        max_similarity = compare_with_references(cv_text, reference_texts)

                    # Résultat de la similarité
                    st.write(f"**Indice de similarité de Jaccard :** {max_similarity:.2f}")

                    # Interprétation du score
                    if max_similarity > 0.8:
                        st.error("⚠️ Ce CV est très similaire à un CV généré par l'IA.")
                    elif max_similarity > 0.5:
                        st.warning("⚠️ Ce CV a des similarités significatives avec les références.")
                    else:
                        st.success("✅ Ce CV semble unique.")
                    st.markdown('</div>', unsafe_allow_html=True)

            # Enregistrer CVs
            nom_prenom = st.text_input("Nom & Prénom*", placeholder="Entrez votre nom & prénom", key="nom", help="Nom et prénom du candidat") 
            mail = st.text_input("Adresse Mail", placeholder="Entrez votre adresse mail ", key="mail", help="Adresse e-mail valide")
            numero_tlfn= st.text_input("Numéro de téléphone", placeholder="Entrez votre numéro de téléphone", key="numero tlfn", help="Numéro de téléphone du candidat")
            competences = st.text_area("Compétences *", placeholder="Entrez les compétences séparées par des virgules", key="competences", help="Liste des compétences du candidat")
            cv_text = extract_text_from_pdf(cv_file)
        
            if st.button("Enregistrer CV"):
                if not nom_prenom:
                    st.error("Veuillez renseigner les informations du propriétaire.")
                elif not is_valid_email(mail):
                    st.error("Veuillez entrer une adresse e-mail valide.")
                else:
                    try:
                        
                        preprocessed_cv_text = preprocess_text(cv_text)
                        # Enregistrement des informations de l'utilisateur
                        user_id = save_to_user(nom_prenom, mail, numero_tlfn)

                        if user_id:  
                            logging.info(f"user_id récupéré avec succès: {user_id}")
                            competences_list = [competence.strip() for competence in competences.split(",")]
                            cv_id = save_to_cv(user_id, preprocessed_cv_text, competences_list)
                
                            if cv_id:
                                st.success("CV enregistré avec succès.")
                            else:
                                st.error("Erreur lors de l'enregistrement du CV.")
                        else:
                            st.error("Erreur lors de l'enregistrement du candidat.")
                    except Exception as e:
                        logging.error(f"Erreur lors de l'enregistrement du CV : {e}")
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

    if selected == "Calculer Similarité":
        # Initialiser les variables dans session_state si elles n'existent pas
        if 'df_results' not in st.session_state:
            st.session_state['df_results'] = pd.DataFrame()
        if 'cvs_texts' not in st.session_state:
            st.session_state['cvs_texts'] = []

        st.header("Calcul de similarité entre CVs et offre")
        # Récupérer les CVs et offres d'emploi
        cvs = get_all_cvs()
        offres = get_all_offres()
        cv_options = {(cv["nom_prenom"]): cv["cv_id"] for cv in cvs}

        # Vérifier s'il y a des CVs et des offres
        if not cvs:
            st.error("Aucun CV trouvé dans la base de données.")
            return
        if not offres:
            st.error("Aucune offre d'emploi trouvée dans la base de données.")
            return

        # Ajouter "Tous" à la liste des CVs pour la sélection multiple
        cv_options_with_all = ["Tous"] + list(cv_options.keys())

        # Sélectionner plusieurs CVs et une seule offre
        selected_cvs = st.multiselect(
            "Sélectionnez un ou plusieurs candidats",
            options=cv_options_with_all
        )

        if "Tous" in selected_cvs:
            selected_cvs = list(cv_options.keys())

        selected_offer = st.selectbox(
            "Sélectionnez une Offre d'emploi",
            [offre['titre'] for offre in offres],
            help="Sélectionnez une offre d'emploi pour évaluer la similarité avec les CVs"
        )

        # Vérifier si une offre a été sélectionnée
        if selected_offer:
            # Récupérer le texte de l'offre sélectionnée
            text_offre = next(
                (offre['text_offre'] for offre in offres if offre['titre'] == selected_offer),
                None  # Valeur par défaut si aucune correspondance n'est trouvée
            )

            if text_offre:
                with st.spinner("Analyse de l'offre avec Gemini AI..."):
                    categorized_skills = categorize_skills_with_kano(text_offre)

                if categorized_skills:
                    st.write("### Compétences catégorisées selon le modèle de Kano :")
                    competences_utilisateur = []

                    # Extraire et afficher les compétences par catégorie
                    categories = ["Indispensable", "Proportionnelle", "Attractive", "Indifférente", "Double tranchant"]
                    for category in categories:
                        if f"**{category}:**" in categorized_skills:
                            st.subheader(f"**{category}:**")
                            category_section = categorized_skills.split(f"**{category}:**")[1].split("**")[0].strip()
                            skills = [skill.strip() for skill in category_section.split("\n") if skill.strip()]
                            competences_utilisateur.extend([(skill, category) for skill in skills])
                            for skill in skills:
                                st.write(f"- {skill}")

                    # Afficher les compétences récupérées
                    if competences_utilisateur:
                        st.success("Les compétences ont été automatiquement récupérées et classées.")
                    else:
                        st.warning("Aucune compétence n'a pu être extraite de l'offre.")

                else:
                    st.warning("Le modèle n'a pas pu générer de compétences catégorisées.")

            else:
                st.warning("Le texte de l'offre sélectionnée est introuvable.")
        else:
            st.warning("Veuillez sélectionner une offre avant de générer les compétences.")

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
            model1, model2, model3 = load_models()

            # Calculer les vecteurs de l'offre
            offer_vector = np.concatenate([model1.encode([offer_text]), model2.encode([offer_text]), model3.encode([offer_text])], axis=1)
            
            # Calculer la similarité pour chaque CV sélectionné
            results = []
            for cv_id in selected_cvs:
                # Récupérer le CV correspondant
                cv = next((cv for cv in cvs if cv['nom_prenom'] == cv_id), None)
                if not cv or not cv.get('cv_text'):
                    st.warning(f"Le texte du CV pour {cv_id} est introuvable ou vide. Il sera ignoré.")
                    continue

                # Calculer le score basé sur les compétences et le modèle de Kano
                score_kano = sum(
                    poids_kano.get(kano_category, 0) 
                    for competence, kano_category in competences_utilisateur 
                    if competence in cv.get('competences', [])
                )
                score_kano = min(score_kano, 1)

                # Encodage des vecteurs pour le CV
                cv_vectors = np.concatenate([
                    model1.encode([cv['cv_text']]),
                    model2.encode([cv['cv_text']]),
                    model3.encode([cv['cv_text']])
                ], axis=1)

                # Calculer la similarité cosinus
                similarity = compute_cosine_similarity(cv_vectors[0], offer_vector[0])

                # Ajouter le résultat à la liste
                results.append({
                    "Nom du CV": cv_id,
                    "Score Kano": score_kano,
                    "Similarité Cosinus": similarity
                })

            # Tri des résultats par score de similarité cosinus
            results.sort(key=lambda x: x["Similarité Cosinus"], reverse=True)
            
            #Stockage des vecteurs dan qdrant
            store_vectors_in_qdrant(cv_vectors, [f"{cv_id[0]}_{cv_id[1]}"])
            store_offer_vector_in_qdrant(offer_vector.flatten(), selected_offer)

            

            # Afficher les résultats
            if results:
                st.write("### Résultats de la similarité :")
                df_results = pd.DataFrame(results)
                st.dataframe(df_results.style.highlight_max(axis=0, subset=["Similarité Cosinus"], color="lightgreen"))
                st.session_state['df_results'] = df_results
            else:
                st.warning("Aucun résultat de similarité n'a été généré.")


            # Afficher le meilleur candidat
            if results:
                best_candidate = results[0]
                st.success(f"Le meilleur candidat est {best_candidate['Nom du CV']} avec une similarité de {best_candidate['Similarité Cosinus']:.4f}")
            
             # Stocker les résultats dans le session state pour communication
            session_state['df_results'] = df_results
            session_state['cvs_texts'] = cvs_texts

            if 'df_results' in session_state and not session_state['df_results'].empty:
                df_results = session_state['df_results']
            
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

                # Section des options de sélection des graphiques
                #with st.form("form_selection_graphiques"):
                 #   st.write("Sélectionnez les graphiques que vous souhaitez afficher pour analyser la similarité entre les CVs et l'offre d'emploi.")
                    
                    # Cases à cocher pour les graphiques
                    #show_bar_chart = st.checkbox("Graphique en Barres - Similarité des CVs")
                    #show_pie_chart = st.checkbox("Diagramme en Secteurs - Répartition des Similarités")
                    #show_histogram = st.checkbox("Histogramme - Distribution des Similarités")
                    #show_cumulative_line = st.checkbox("Graphique Linéaire - Similarité Cumulative")
                    #show_scatter_plot = st.checkbox("Nuage de Points - Similarité de chaque CV")
                    #show_boxplot = st.checkbox("Box Plot - Répartition des Similarités")
                    #show_stacked_bar = st.checkbox("Barres Empilées - Similarité par Compétence")
                    
                    # Bouton de validation du formulaire
                    #submitted = st.form_submit_button("Afficher les graphiques")

                # Afficher les graphiques sélectionnés uniquement après validation du formulaire
                #if submitted and not df_results.empty:
                 #   if show_bar_chart:
                   #     plot_results(df_results)
                    #if show_pie_chart:
                       # plot_pie_chart(df_results)
                    #if show_histogram:
                     #   plot_similarity_histogram(df_results)
                    #if show_cumulative_line:
                     #   plot_cumulative_similarity(df_results)
                    #if show_scatter_plot:
                     #   plot_similarity_scatter(df_results)
                    #if show_boxplot:
                     #   plot_similarity_boxplot(df_results)
                    #if show_stacked_bar:
                     #   plot_stacked_bar_competences(df_results)


    
                #plot_results(df_results)
        
                plot_pie_chart(df_results)
            
                plot_similarity_histogram(df_results)
            
                plot_cumulative_similarity(df_results)
            
                plot_similarity_scatter(df_results)
            
                plot_similarity_boxplot(df_results)
                
                    #plot_stacked_bar_competences(df_results)


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
            options=["Gestion des candidats", "Gestion des offres", "Gestion des résultats", "Gestion des cvs","Gestion Profil/Question"],
            icons=["person", "briefcase", "clipboard-data", "files", "gear"],
            menu_icon="database",  
            default_index=0,  
            styles={
                "container": {"padding": "0!important", "background-color": "#F0F2D6"},  
                "icon": {"color": "#191970", "font-size": "20px"},  # Style des icônes
                "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#E1AD01"},
                "nav-link-selected": {"background-color": "#E1AD01"},  # Couleur de l'option sélectionnée
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

            session_state.candidats_df = pd.DataFrame(session_state.candidat, columns=["user_id", "nom_prenom", "mail", "numero_tlfn", "profil"])
            st.dataframe(session_state.candidats_df)
    
            # Utiliser session_state pour garder en mémoire le candidat sélectionné
            if "selected_candidate" not in st.session_state:
                st.session_state.selected_candidate = None

            # Afficher les candidats dans une liste déroulante pour en sélectionner un
            st.session_state.candidat_selection = st.selectbox(
                "Sélectionnez un candidat à modifier", 
                [f"{c['nom_prenom']}" for c in session_state.candidat], 
                key="candidate_selectbox"
            )
        
            # Trouver l'enregistrement correspondant au candidat sélectionné
            candidat_selected = next((c for c in session_state.candidat if f"{c['nom_prenom']}" == session_state.candidat_selection), None)

            # Stocker le candidat sélectionné dans session_state pour éviter de perdre l'état
            st.session_state.selected_candidate = candidat_selected

            if st.session_state.selected_candidate:
                # Afficher les informations actuelles du candidat
                st.write("### Informations actuelles du candidat :")
                st.write(f"**Nom & Prénom :** {st.session_state.selected_candidate['nom_prenom']}")
                st.write(f"**Adresse Mail :** {st.session_state.selected_candidate['mail']}")
                st.write(f"**Numéro de téléphone :** {st.session_state.selected_candidate['numero_tlfn']}")

                st.write("### Modifier les informations du candidat :")
                # Champs de texte pré-remplis avec les informations actuelles
                nom_prenom = st.text_input("Nom & Prénom", st.session_state.selected_candidate["nom_prenom"], key="nom_input")
                mail = st.text_input("Adresse Mail", st.session_state.selected_candidate["mail"], key="mail_input")
                numero_tlfn = st.text_input("Numéro de téléphone", st.session_state.selected_candidate["numero_tlfn"], key="phone_input")

                # Bouton pour enregistrer les modifications
                if st.button("Enregistrer les modifications"):
                    updated_data = {
                        "nom_prenom": nom_prenom,
                        "mail": mail,
                        "numero_tlfn": numero_tlfn,
                    }

                    # Valider les champs avant de mettre à jour
                    if not nom_prenom:
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
            session_state.cv_df=pd.DataFrame(session_state.cv, columns=["cv_id", "user_id", "date_insertion", "cv_text"])
            st.dataframe(session_state.cv_df)
            
        if selected1 == "Gestion Profil/Question":
            st.header("Ici vous trouverez tous les types de profil ainsi que leurs questions spécifiques")

            # Récupérer tous les profils et leurs questions
            st.session_state.profil = get_all_profil()

            if not st.session_state.profil:
                st.write("Il n'existe aucun profil à ce jour")
            else:
                # Créer un DataFrame pour afficher tous les profils
                profils_df = pd.DataFrame(st.session_state.profil, columns=["profil", "question"])
                st.dataframe(profils_df)

                # Sélection d'un profil spécifique
                profil_names = [p['profil'] for p in st.session_state.profil]
                selected_profil = st.selectbox("Sélectionnez un profil pour afficher, modifier ou supprimer les questions", profil_names)

                # Filtrer les questions pour le profil sélectionné
                selected_profil_data = next((p for p in st.session_state.profil if p['profil'] == selected_profil), None)
                if selected_profil_data:
                    st.subheader(f"Questions pour le profil : {selected_profil}")

                    # Charger les questions dans des champs modifiables
                    questions = selected_profil_data['question'] if isinstance(selected_profil_data['question'], list) else []

                    modified_questions = []
                    for i, question in enumerate(questions):
                        # Afficher chaque question dans un champ de texte modifiable
                        modified_question = st.text_input(f"Question {i+1}", value=question, key=f"question_{i}")
                        modified_questions.append(modified_question)

                    # Bouton pour enregistrer les modifications
                    if st.button("Enregistrer les modifications"):
                        if all(modified_questions):
                            # Sauvegarder les questions modifiées dans la base de données
                            update_profil_questions(selected_profil, modified_questions)
                            st.success("Questions modifiées et enregistrées avec succès.")
                        else:
                            st.warning("Veuillez remplir toutes les questions avant de les enregistrer.")
                    
                    # Ajouter un bouton de suppression pour le profil
                    if st.button("Supprimer le profil"):
                        # Demander une confirmation
                        st.warning("Êtes-vous sûr de vouloir supprimer ce profil ? Cette action est irréversible.")
                        confirm_delete = st.button("Confirmer la suppression")
                        
                        if confirm_delete:
                            
                            delete_profil(selected_profil)
                            st.success(f"Le profil '{selected_profil}' a été supprimé avec succès.")
                            st.experimental_rerun()  

    
    if selected == "Gestion de suivi des candidats":
        st.header("Gestion de suivi des candidats")

        # Récupérer la liste des candidats
        candidates = get_all_candidates()
        profil_details = get_all_profil()
        if not candidates:
            st.error("Aucun candidat trouvé.")
        else:
            # Sélecteur de candidat
            selected_candidate = st.selectbox("Choisissez un candidat à évaluer :", 
                                            [f"{c['nom_prenom']}" for c in candidates])

            # Trouver le candidat sélectionné dans la liste
            candidate_details = next((c for c in candidates if f"{c['nom_prenom']}" == selected_candidate), None)

            # Vérifier si le candidat a été trouvé
            if candidate_details:
                st.write(f"**Email du candidat :** {candidate_details['mail']}")
                
                # Notation par étoiles
                sentiment_mapping = ["1 étoiles", "2 étoiles", "3 étoiles", "4 étoiles", "5 étoiles"]
                selected_rating = st.feedback("stars")
                selected_profil = st.selectbox("les profils disponibles :", 
                                            [f"{c['profil']}" for c in profil_details],help="on doit attrubuer un profil au candidat pour qu'il puisse répondre à des questions liés à son profil")
                # Saisie du message de recommandation
                message_body = st.text_area("Message de recommandation")

            
            email = "fabricejordan2001@gmail.com"
            # !test pour avoir le mail du candidat
            # st.write(st.session_state.selected_candidate['mail']),

            if st.button("Envoyer la recommandation"):
                if not selected_rating:
                    st.warning("notez d'abord le candidat")
                elif message_body:
                    # Message d'email
                    email = candidate_details['mail']
                    email_subject = f"Recommandation pour {selected_candidate} pour un profil de {selected_profil}"
                    email_message = f"Vous avez été recommandé avec une note de {sentiment_mapping[selected_rating]}.\n\n{message_body}\n\n Rendez vous sur ce lien : http://localhost:8501/entretien"
                
                    # Envoi de l'email
                    if send_email(email, email_subject, email_message,selected_profil):
                        st.success("La recommandation a été envoyée avec succès.")
                else:
                    st.warning("Veuillez saisir un message avant d'envoyer la recommandation.")

    
    if selected == "Génération de questions d'entretien":
        st.header("Génération de Questions d'Entretien")
        st.write("Cette page sert à créer des profils et générer des questions pour des entretiens.")

        # Étape 1: Saisie du profil
        with st.form("profil_form"):
            profil = st.text_input("Entrez le profil de métier (1 à la fois)", help="Exemple : Data Analyst, Fullstack Developer")
            generate_questions_button = st.form_submit_button("Vérifier et Enregistrer le Profil")

        # Vérification et enregistrement du profil
        if generate_questions_button:
            if not profil:
                st.warning("Veuillez entrer un profil.")
            elif checking_profil(profil) is None:
                
                st.success("Nouveau profil enregistré.")
            else:
                st.warning("Ce profil existe déjà !")

        # Utiliser session_state pour gérer l'état des questions générées
        if 'auto_generated_questions' not in st.session_state:
            st.session_state.auto_generated_questions = []

        # Étape 2: Gestion des profils vides
        st.header("Génération et Prévisualisation des Questions pour les Profils Récents")
        profil_empty = get_empty_profil()
        if not profil_empty:
            st.error("Il n'y a pas encore de profils vides.")
        else:
            selected_empty_profil = st.selectbox(
                "Les profils vides :", 
                [f"{c['profil']}" for c in profil_empty]
            )

            # Bouton pour générer automatiquement des questions
            generate_preview_button = st.button("Générer automatiquement des questions", key="generate_button")

            # Prévisualisation et modification des questions générées
            if generate_preview_button and not st.session_state.auto_generated_questions:
                try:
                    # Générer les questions et stocker dans session_state
                    st.session_state.auto_generated_questions = generate_questionnaire_google({"profil": selected_empty_profil})
                    # Filtrer les questions vides ou manquantes
                    st.session_state.auto_generated_questions = [q for q in st.session_state.auto_generated_questions if q]
                except Exception as e:
                    st.error(f"Erreur lors de la génération des questions : {e}")

            # Afficher la prévisualisation et permettre la modification des questions
            if st.session_state.auto_generated_questions:
                st.subheader("Prévisualisation et Modification des Questions Générées par l'IA")

                # Liste pour stocker les modifications
                modified_questions = []
                for i, question in enumerate(st.session_state.auto_generated_questions, 1):
                    # Afficher chaque question et permettre la modification
                    modified_question = st.text_input(f"Question {i}", value=question, key=f"generated_question_{i}")
                    modified_questions.append(modified_question)

                # Bouton pour enregistrer les questions
                if st.button("Enregistrer les Questions"):
                    if all(modified_questions):
                        save_question(selected_empty_profil, modified_questions)
                        st.success("Questions enregistrées avec succès.")
                        # Réinitialiser les questions générées
                        st.session_state.auto_generated_questions = []
                    else:
                        st.warning("Veuillez remplir toutes les questions avant l'enregistrement.")


if __name__ == "__main__":
    main()



