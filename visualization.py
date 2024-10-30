import plotly.express as px
import streamlit as st
import pandas as pd


def plot_results(df_results):
    fig = px.bar(df_results, 
                  x='Similarité Cosinus', 
                  y='Nom du CV', 
                  orientation='h', 
                  title='Similarité des CVs par rapport à l\'offre d\'emploi',
                  labels={'Nom du CV': 'CV', 'Similarité Cosinus': 'Similarité Cosinus'},
                  color='Similarité Cosinus', 
                  color_continuous_scale=px.colors.sequential.Sunset)

    fig.update_layout(xaxis=dict(range=[0, 1]),  
                        yaxis_title='CV',
                        xaxis_title='Similarité Cosinus',
                        title_x=0.5)  

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



