import plotly.express as px
import streamlit as st
import pandas as pd


def plot_results(df_results):
    # Afficher le contenu de df_results pour débogage
    #st.write("Contenu de df_results avant nettoyage :", df_results)

    # Vérification et nettoyage des données
    df_results = df_results.dropna(subset=['Similarité Cosinus', 'Nom du CV'])
    df_results['Similarité Cosinus'] = pd.to_numeric(df_results['Similarité Cosinus'], errors='coerce')
    df_results['Nom du CV'] = df_results['Nom du CV'].astype(str)

    # Retirer les valeurs nulles après conversion
    df_results = df_results.dropna(subset=['Similarité Cosinus', 'Nom du CV'])

    # Affichage après nettoyage pour confirmation
    #st.write("Contenu de df_results après nettoyage :", df_results)

    # Ajustement dynamique de la hauteur en fonction du nombre de lignes
    fig_height = 400 + len(df_results) * 20

    # Créer le graphique
    fig = px.bar(
        df_results, 
        x='Similarité Cosinus', 
        y='Nom du CV', 
        orientation='h', 
        title='Similarité des CVs par rapport à l\'offre d\'emploi',
        labels={'Nom du CV': 'CV', 'Similarité Cosinus': 'Similarité Cosinus'},
        color='Similarité Cosinus', 
        color_continuous_scale=px.colors.sequential.Sunset
    )

    # Mettre à jour la mise en page
    fig.update_layout(
        xaxis=dict(range=[0, 1]),  
        yaxis_title='CV',
        xaxis_title='Similarité Cosinus',
        title_x=0.5,
        height=fig_height  # Utilisation de la hauteur dynamique
    )

    # Ajouter des annotations pour les valeurs de similarité
    fig.update_traces(texttemplate='%{x:.2f}', textposition='outside')

    # Afficher le graphique
    st.plotly_chart(fig)


def plot_pie_chart(df_results):
    # Catégoriser les similarités en intervalles
    df_results['Intervalle'] = pd.cut(
        df_results['Similarité Cosinus'], 
        bins=[0, 0.4, 0.7, 1], 
        labels=['0-0.4', '0.41-0.7', '0.71-1']
    )

    # Compter le nombre de CVs dans chaque intervalle
    interval_counts = df_results['Intervalle'].value_counts().reset_index()
    interval_counts.columns = ['Intervalle', 'Nombre de CVs']

    # Créer le diagramme circulaire
    fig = px.pie(interval_counts, 
                 values='Nombre de CVs', 
                 names='Intervalle', 
                 title="Répartition des similarités des CVs",
                 color_discrete_sequence=px.colors.sequential.Sunset)

    # Afficher le graphique dans Streamlit
    st.plotly_chart(fig)


def plot_similarity_histogram(df_results):
    fig = px.histogram(df_results, 
                       x='Similarité Cosinus', 
                       nbins=10,
                       title="Distribution des scores de similarité",
                       labels={'Similarité Cosinus': 'Score de Similarité'},
                       color_discrete_sequence=['#E1AD01'])

    fig.update_layout(
        xaxis_title="Score de Similarité",
        yaxis_title="Nombre de CVs",
        title_x=0.5
    )

    st.plotly_chart(fig)


def plot_cumulative_similarity(df_results):
    # Trier les CVs par similarité décroissante
    df_results = df_results.sort_values(by='Similarité Cosinus', ascending=False).reset_index(drop=True)
    df_results['Cumulative Similarity'] = df_results['Similarité Cosinus'].cumsum()

    fig = px.line(df_results, 
                  x=df_results.index, 
                  y='Cumulative Similarity',
                  title="Similarité Cumulative des CVs",
                  labels={'index': 'CVs', 'Cumulative Similarity': 'Similarité Cumulative'},
                  markers=True)

    fig.update_layout(xaxis_title="CVs (ordonnés)", yaxis_title="Similarité Cumulative", title_x=0.5)
    st.plotly_chart(fig)


def plot_similarity_scatter(df_results):
    fig = px.scatter(df_results, 
                     x='Nom du CV', 
                     y='Similarité Cosinus', 
                     title="Similarité de chaque CV par rapport à l'offre",
                     labels={'Nom du CV': 'CV', 'Similarité Cosinus': 'Score de Similarité'},
                     color='Similarité Cosinus', 
                     color_continuous_scale=px.colors.sequential.Sunset,
                     size='Similarité Cosinus', 
                     size_max=15)

    fig.update_layout(xaxis_title="CV", yaxis_title="Score de Similarité", title_x=0.5)
    st.plotly_chart(fig)


def plot_similarity_boxplot(df_results):
    fig = px.box(df_results, 
                 y='Similarité Cosinus', 
                 title="Répartition des scores de similarité entre les CVs",
                 labels={'Similarité Cosinus': 'Score de Similarité'},
                 color_discrete_sequence=['#E1AD01'])

    fig.update_layout(yaxis_title="Score de Similarité", title_x=0.5)
    st.plotly_chart(fig)

def plot_stacked_bar_competences(df_results):
    # Exemple de données pour des barres empilées par compétence (adapter aux vôtres)
    stacked_data = pd.DataFrame({
        'Compétence': ['Python', 'Machine Learning', 'Data Analysis', 'SQL'],
        'CV1': [0.8, 0.6, 0.7, 0.9],
        'CV2': [0.4, 0.9, 0.3, 0.6],
        'CV3': [0.7, 0.8, 0.5, 0.4],
        'CV4': [0.6, 0.7, 0.8, 0.5]
    })

    fig = px.bar(stacked_data, 
                 x='Compétence', 
                 y=['CV1', 'CV2', 'CV3', 'CV4'], 
                 title="Similarité des CVs par Compétence",
                 labels={'value': 'Score de Similarité', 'variable': 'CV'},
                 color_discrete_sequence=px.colors.sequential.Sunset)

    fig.update_layout(barmode='stack', yaxis_title="Score de Similarité", title_x=0.5)
    st.plotly_chart(fig)
