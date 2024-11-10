import asyncio
import os
import asyncpg
import numpy as np
from data_processing import compute_cosine_similarity

# Connexion asynchrone à la base de données
async def connect_to_db():
    """Établit une connexion asynchrone à la base de données."""
    try:
        conn = await asyncpg.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return None

# Fonction de calcul de similarité asynchrone
async def calculate_similarity(cv_vector, offer_vector, score_similarite):
    """Calcule la similarité cosinus entre un CV et une offre en parallèle."""
    similarity = compute_cosine_similarity(cv_vector, offer_vector) + score_similarite / 25
    return similarity

async def process_cvs_async(cv_vectors, offer_vector, score_similarites):
    """Traite tous les calculs de similarité pour les CVs de manière asynchrone."""
    tasks = [
        calculate_similarity(cv_vector, offer_vector, score_similarite)
        for cv_vector, score_similarite in zip(cv_vectors, score_similarites)
    ]
    results = await asyncio.gather(*tasks)
    return results

# Insertion asynchrone d'un candidat
async def add_candidate_async(nom, prenom, mail, numero_tlfn):
    """Ajoute un candidat de manière asynchrone."""
    conn = await connect_to_db()
    if conn is None:
        return None

    try:
        user_id = await conn.fetchval('''
            INSERT INTO "candidat" (nom, prenom, mail, numero_tlfn)
            VALUES ($1, $2, $3, $4)
            RETURNING user_id;
        ''', nom, prenom, mail, numero_tlfn)
        print(f"Candidat ajouté avec user_id : {user_id}")
        return user_id
    except Exception as e:
        print(f"Erreur lors de l'insertion du candidat : {e}")
        return None
    finally:
        await conn.close()

async def calculate_similarity_async(cv, offer_vector, competences_utilisateur, poids_kano, models):
    score_similarite = 0
    for competence, kano_category in competences_utilisateur:
        if competence in cv['competences']:
            score_similarite += poids_kano[kano_category]
    score_similarite = min(score_similarite, 1)

    # Calculer les vecteurs des CVs
    cv_vector = np.concatenate([model.encode([cv['cv_text']]) for model in models], axis=1)

    # Calculer la similarité cosinus
    similarity = compute_cosine_similarity(cv_vector[0], offer_vector[0]) + score_similarite / 25
    return {"Nom du CV": (cv["nom"], cv["prenom"]), "Similarité Cosinus": similarity}