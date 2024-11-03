import streamlit as st
import os
import uuid
import numpy as np
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Configurer Qdrant API
os.environ['QDRANT_HOST'] = "https://5ab76626-81f8-42db-b56f-f23928129cce.europe-west3-0.gcp.cloud.qdrant.io:6333"
os.environ['QDRANT_API_KEY'] = "GToQ0tM7oryP7zOxTO_P5eeftQW0UErJCYOh1wrhInH4HRlOSscewQ"

# Initialiser Qdrant client
client = QdrantClient(
    url=os.getenv("QDRANT_HOST"),
    api_key=os.getenv("QDRANT_API_KEY")
)

def store_vectors_in_qdrant(vectors, names):
    """Stockage des vecteurs dans Qdrant."""
    points = [
        {
            "id": str(uuid.uuid4()),
            "vector": vector.tolist(),
            "payload": {"name": name}
        }
        for name, vector in zip(names, vectors)
    ]
    try:
        client.upsert(collection_name="cvs_collection5", points=points)
    except Exception as e:
        st.error(f"Erreur lors du stockage des vecteurs : {str(e)}")

def compute_cosine_similarity(vector1, vector2):
    """Calcul de la similarité cosinus entre deux vecteurs."""
    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vector1, vector2) / (norm1 * norm2)


def store_offer_vector_in_qdrant(offer_vector, offer_name):
    """Stockage du vecteur de l'offre d'emploi dans Qdrant."""
    point = {
        "id": str(uuid.uuid4()),
        "vector": offer_vector.tolist(),
        "payload": {"name": offer_name}
    }

    try:
        client.upsert(
            collection_name="offers_collection5",
            points=[point]
        )
        st.success("Vecteur de l'offre d'emploi stocké avec succès dans Qdrant.")
    except Exception as e:
        st.error(f"Erreur lors du stockage du vecteur de l'offre d'emploi : {str(e)}")

@st.cache_resource
def load_models():
    model1 = SentenceTransformer('all-MPNet-base-v2')
    model2 = SentenceTransformer('paraphrase-MiniLM-L12-v2')
    model3 = SentenceTransformer('all-MiniLM-L12-v2')
    return model1, model2, model3

model1, model2, model3 = load_models()

def highlight_best_candidates(row):
    """Met en évidence les meilleurs candidats."""
    return ['background-color: #E1AD01' if row['Similarité Cosinus'] > 0.7 else '' for _ in row]


