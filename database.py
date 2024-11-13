import psycopg2
from psycopg2 import sql, OperationalError
import os
from dotenv import load_dotenv
import logging

# Charger les variables d'environnement
load_dotenv()

# Configurer le fichier de log pour les erreurs
logging.basicConfig(filename='database_errors.log', level=logging.ERROR)

def connect_to_db():
    """Établit une connexion à la base de données."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        conn.autocommit = True  # Activer l'autocommit pour valider automatiquement les transactions
        return conn
    except OperationalError as e:
        logging.error(f"Erreur de connexion à la base de données : {e}")
        return None


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    conn = connect_to_db()
    if conn is None:
        logging.error("Connexion à la base de données échouée.")
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch_one:
                result = cursor.fetchone()
                logging.info(f"Requête exécutée avec succès, résultat unique obtenu : {result}")
                return result
            elif fetch_all:
                results = cursor.fetchall()
                logging.info(f"Requête exécutée avec succès, tous les résultats obtenus : {results}")
                return results
            conn.commit()
            logging.info("Requête d'insertion/mise à jour exécutée avec succès.")
    except psycopg2.Error as e:
        logging.error(f"Erreur lors de l'exécution de la requête : {e} - Query: {query} - Params: {params}")
        return None
    finally:
        conn.close()


def save_to_user(nom, prenom, mail, numero_tlfn):
    query = '''
        INSERT INTO "candidat" (nom, prenom, mail, numero_tlfn)
        VALUES (%s, %s, %s, %s)
        RETURNING user_id;
    '''
    result = execute_query(query, (nom, prenom, mail, numero_tlfn), fetch_one=True)
    if result:
        user_id = result[0]
        logging.info(f"Candidat enregistré avec user_id: {user_id}")
        return user_id
    else:
        logging.error("Erreur lors de l'enregistrement du candidat. Aucun user_id retourné.")
        return None


def save_to_offre(text_offre, offre_societe, titre):
    query = '''
        INSERT INTO "offre" (text_offre, offre_societe, titre)
        VALUES (%s, %s, %s)
        RETURNING offre_id;
    '''
    result = execute_query(query, (text_offre, offre_societe, titre), fetch_one=True)
    return result[0] if result else None

def save_to_resultat(cv_id, offre_id, cosine_similarity):
    query = '''
        INSERT INTO "resultat" (cv_id, offre_id, cosine_similarity)
        VALUES (%s, %s, %s)
        RETURNING resultat_id;
    '''
    result = execute_query(query, (cv_id, offre_id, float(cosine_similarity)), fetch_one=True)
    return result[0] if result else None

def save_to_cv(user_id, cv_text, competences):
    query = '''
        INSERT INTO "cv" (user_id, date_insertion, cv_text, competences)
        VALUES (%s, NOW(), %s, %s)
        RETURNING cv_id;
    '''
    result = execute_query(query, (user_id, cv_text, competences), fetch_one=True)
    return result[0] if result else None

# Fonctions de récupération d'ID
def get_user_id(nom, prenom, mail, numero_tlfn):
    query = '''
        SELECT user_id FROM "candidat"
        WHERE nom = %s AND prenom = %s AND mail = %s AND numero_tlfn = %s;
    '''
    result = execute_query(query, (nom, prenom, mail, numero_tlfn), fetch_one=True)
    return result[0] if result else None

def get_cv_id(user_id):
    query = '''
        SELECT cv_id FROM "cv"
        WHERE user_id = %s;
    '''
    result = execute_query(query, (user_id,), fetch_one=True)
    return result[0] if result else None

def get_offre_id(titre, offre_societe):
    query = '''
        SELECT offre_id FROM "offre"
        WHERE titre = %s AND offre_societe = %s;
    '''
    result = execute_query(query, (titre, offre_societe), fetch_one=True)
    return result[0] if result else None

# Fonctions pour récupérer tous les enregistrements
def get_all_candidates():
    query = '''SELECT user_id, nom, prenom, mail, numero_tlfn FROM candidat;'''
    result = execute_query(query, fetch_all=True)
    return [{"user_id": c[0], "nom": c[1], "prenom": c[2], "mail": c[3], "numero_tlfn": c[4]} for c in result] if result else []

def get_all_offres():
    query = '''SELECT offre_id, text_offre, offre_societe, titre FROM offre;'''
    result = execute_query(query, fetch_all=True)
    return [{"offre_id": o[0], "text_offre": o[1], "offre_societe": o[2], "titre": o[3]} for o in result] if result else []

def get_all_cvs():
    query = '''
        SELECT cv.cv_id, cv.user_id, cv.date_insertion, cv.cv_text, candidat.nom, candidat.prenom, cv.competences
        FROM cv
        JOIN candidat ON cv.user_id = candidat.user_id;
    '''
    result = execute_query(query, fetch_all=True)
    return [{"cv_id": v[0], "user_id": v[1], "date_insertion": v[2], "cv_text": v[3], "nom": v[4], "prenom": v[5], "competences": v[6]} for v in result] if result else []

def get_all_resultats():
    query = '''SELECT resultat_id, cv_id, offre_id, cosine_similarity FROM resultat;'''
    result = execute_query(query, fetch_all=True)
    return [{"resultat_id": r[0], "cv_id": r[1], "offre_id": r[2], "cosine_similarity": r[3]} for r in result] if result else []

# Fonctions de mise à jour
def update_candidate(user_id, updated_data):
    query = '''
        UPDATE "candidat"
        SET nom = %s, prenom = %s, mail = %s, numero_tlfn = %s
        WHERE user_id = %s;
    '''
    return execute_query(query, (updated_data['nom'], updated_data['prenom'], updated_data['mail'], updated_data['numero_tlfn'], user_id))

def update_offre(offre_id, updated_data):
    query = '''
        UPDATE "offre"
        SET text_offre = %s, offre_societe = %s, titre = %s
        WHERE offre_id = %s;
    '''
    return execute_query(query, (updated_data['text_offre'], updated_data['offre_societe'], updated_data['titre'], offre_id))

def update_resultat(resultat_id, updated_data):
    query = '''
        UPDATE "resultat"
        SET cv_id = %s, offre_id = %s, cosine_similarity = %s
        WHERE resultat_id = %s;
    '''
    return execute_query(query, (updated_data['cv_id'], updated_data['offre_id'], updated_data['cosine_similarity'], resultat_id))

def generate_code(mail, code):
    """Met à jour la colonne 'code' pour l'utilisateur spécifié par son email."""
    query = '''
        UPDATE "candidat"
        SET code = %s
        WHERE mail = %s;
    '''
    result = execute_query(query, (code, mail))
    if result is None:
        logging.error(f"Erreur lors de la mise à jour du code pour l'utilisateur avec l'email : {mail}")
        return False
    logging.info(f"Code mis à jour avec succès pour l'utilisateur avec l'email : {mail}")
    return True

def checking_profil (profil):
    # Vérifier si le profil existe déjà dans la table "entretien"
    check_query = '''
        SELECT profil FROM "entretien"
        WHERE profil = %s;
    '''
    # si la valeur retourner est none le profil n'existe pas
    exists = execute_query(check_query, (profil,), fetch_one=True)
    if exists:
        print("le profil existe deja:",exists)
        return exists
    else:
        print("au cas ou il n'existe pas de profil  :", exists)
        insert_query = ''' INSERT INTO "entretien" (profil) VALUES (%s); '''
        if execute_query(insert_query, (profil,)): 
            print("erreur d'insertion:", insert_query) 
            return exists
        else: 
            print("\n\nNouveau profil ajouté a la bd:",profil) 
            return exists

def get_all_profil ():
    """ Pour afficher tous les profils dans la tables """
    query = '''SELECT profil , question FROM entretien;'''
    result = execute_query(query, fetch_all=True)
    if result:
        return [{"profil": row[0], "question": row[1]} for row in result]
    return []

def get_empty_profil():
    """Pour le selected box pour afficher que les profils qui n'ont pas encore de question """
    query = '''SELECT profil FROM entretien WHERE question IS NULL;'''
    result = execute_query(query, fetch_all=True)
    if result:
        return [{"profil": row[0]} for row in result]
    return []
def save_question(profil, question):
    """Pour insérer les questions une fois le profil validé """
    query = '''
        UPDATE "entretien" 
        SET question = %s
        WHERE profil = %s;
    '''
    result = execute_query(query ,(question, profil))
    if result is None:
        logging.error(f"Mise a jour du profil : {profil}")
        return False
    logging.error(f"Erreur : {profil} n'est pas vide")
    return True
    