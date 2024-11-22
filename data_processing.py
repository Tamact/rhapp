import streamlit as st
import os
import uuid
import numpy as np
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from transformers import pipeline
import spacy
import json

# Charger les variables d'environnement
load_dotenv()

# Configurer Qdrant API
#os.environ['QDRANT_HOST'] = "https://5ab76626-81f8-42db-b56f-f23928129cce.europe-west3-0.gcp.cloud.qdrant.io:6333"
#os.environ['QDRANT_API_KEY'] = "GToQ0tM7oryP7zOxTO_P5eeftQW0UErJCYOh1wrhInH4HRlOSscewQ"

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
        client.upsert(collection_name="cv_collection99", points=points)
        st.success("Vecteurs de CVs stockés avec succès dans Qdrant.")
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
            collection_name="offer_collection99",
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
    #model4 = SentenceTransformer('bert-base-nli-mean-tokens')
    return model1, model2, model3 #model4

model1, model2, model3  = load_models()

def highlight_best_candidates(row):
    """Met en évidence les meilleurs candidats en fonction de la similarité cosinus."""
    color = '#E1AD01' if row['Similarité Cosinus'] > 0.7 else ''
    return ['background-color: {}'.format(color) if col == 'Similarité Cosinus' else '' for col in row.index]


@st.cache_resource
def load_ai_detector():
    return pipeline("text-classification", model="roberta-base-openai-detector")

ai_detector = load_ai_detector


def analyze_text_style(text):
    """
    Analyse le texte pour détecter des anomalies dans le style et le ton.
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    avg_sentence_length = sum(len(sent) for sent in doc.sents) / len(list(doc.sents))
    unusual_words = [token.text for token in doc if token.is_alpha and len(token.text) > 12]
    return {
        "avg_sentence_length": avg_sentence_length,
        "unusual_words": unusual_words,
        "num_sentences": len(list(doc.sents))
    }



# Charger les références depuis references.json
def load_references(file_path="references.json"):
    with open(file_path, "r", encoding="utf-8") as file:
        references = json.load(file)
    return [ref["cv"] for ref in references]

# Calculer la similarité de Jaccard
def jaccard_similarity(text1, text2):
    set1 = set(text1.split())
    set2 = set(text2.split())
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0

# Comparer un CV soumis avec les références
def compare_with_references(submitted_cv, reference_texts):
    max_score = 0
    for ref in reference_texts:
        score = jaccard_similarity(submitted_cv, ref)
        max_score = max(max_score, score)
    return max_score
