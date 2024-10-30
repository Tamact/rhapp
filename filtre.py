import streamlit as st
import pandas as pd


def filter_cvs_by_skills(df_results, skills, cvs_texts):
    """Filtrer les CVs en fonction des compétences demandées."""
    filtered_results = []
    for i, text in enumerate(cvs_texts):
        if any(skill.lower() in text.lower() for skill in skills):
            filtered_results.append(df_results.iloc[i])

    if not filtered_results:
        st.warning("Aucun CV ne correspond aux compétences demandées.")
        return pd.DataFrame()

    return pd.DataFrame(filtered_results)

def filter_cvs_by_results(df_results, threshold, num_cvs):
    """Filtrer les CVs en fonction de la similarité cosinus et du nombre de CVs souhaité."""
    filtered_results = df_results[df_results['Similarité Cosinus'] >= threshold]
    
    if filtered_results.empty:
        st.warning("Aucun CV ne correspond aux filtres démandés")
    
    return filtered_results.head(num_cvs)
