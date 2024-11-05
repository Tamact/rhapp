import psycopg2
from psycopg2 import sql

# Fonction pour établir une connexion à la base de données
def connect_to_db():
    return psycopg2.connect(
        dbname="rh",
        user="postgres",
        password="passer",
        host="localhost",
        port="5432"
    )

def save_to_user(nom, prenom, mail, numero_tlfn):
    try:
        conn = connect_to_db()
        conn.autocommit = True
        cursor = conn.cursor()

        # Insertion de l'utilisateur
        cursor.execute(sql.SQL('''
            INSERT INTO "candidat" (nom, prenom, mail, numero_tlfn)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id;
        '''), (nom, prenom, mail, numero_tlfn))
        
        # Récupération de l'ID de l'utilisateur (assurez-vous que c'est un entier)
        user_id = cursor.fetchone()[0]
        return user_id

    except psycopg2.Error as e:
        print(f"Erreur lors de l'enregistrement du CV: {e}")
        return None

    finally:
        if conn:
            conn.close()



# Enregistrement d'une offre
def save_to_offre(text_offre, offre_societe, titre):
    try:
        conn = connect_to_db()
        conn.autocommit = True
        cursor = conn.cursor()

        # Insertion dans la table des offres
        cursor.execute(sql.SQL('''
            INSERT INTO "offre" (text_offre, offre_societe, titre)
            VALUES (%s, %s, %s)
            RETURNING offre_id;
        '''), (text_offre, offre_societe, titre))
        
        # Récupération de l'ID de l'offre
        offre_id = cursor.fetchone()[0]
        return offre_id

    except psycopg2.Error as e:
        print(f"Erreur lors de l'enregistrement de l'offre: {e}")
        return None

    finally:
        if conn:
            conn.close()

# Enregistrement d'un résultat lié à un utilisateur
def save_to_resultat(cv_id, offre_id, cosine_similarity):
    try:
        conn = connect_to_db()
        conn.autocommit = True
        cursor = conn.cursor()

        cosine_similarity = float(cosine_similarity)
        
        # Insertion dans la table des résultats
        cursor.execute(sql.SQL('''
            INSERT INTO "resultat" (cv_id, offre_id, cosine_similarity)
            VALUES (%s, %s, %s)
            RETURNING resultat_id;
        '''), (cv_id, offre_id, cosine_similarity))
        
        # Récupération de l'ID du résultat
        resultat_id = cursor.fetchone()[0]
        print(f"Résultat enregistré avec l'ID: {resultat_id}")
        return resultat_id

    except psycopg2.Error as e:
        print(f"Erreur lors de l'enregistrement du résultat: {e}")
        return None

   
 
def save_to_cv(user_id, cv_text, competences):
    try:
        # Correction: Appel correct de la fonction connect_to_db()
        conn = connect_to_db()  
        conn.autocommit = True
        cursor = conn.cursor()

        # Insertion du CV avec la date actuelle et le texte du CV
        cursor.execute(sql.SQL('''
            INSERT INTO "cv" (user_id, date_insertion, cv_text, competences)
            VALUES (%s, NOW(), %s, %s)
            RETURNING cv_id;
        '''), (user_id, cv_text, competences))

        # Récupération de l'ID du CV
        cv_id = cursor.fetchone()[0]
        return cv_id

    except psycopg2.Error as e:
        print(f"Erreur lors de l'enregistrement du CV: {e}")
        return None


def get_user_id(nom, prenom, mail, numero_tlfn):
    """
    Récupérer l'ID d'un utilisateur existant en fonction de ses informations.
    """
    query = sql.SQL('''
        SELECT user_id FROM "candidat"
        WHERE nom = %s AND prenom = %s AND mail = %s AND numero_tlfn = %s;
    ''')

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query, (nom, prenom, mail, numero_tlfn))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        return None


def get_cv_id(user_id):
    """
    Récupérer l'ID d'un CV existant en fonction de l'utilisateur.
    """
    query = sql.SQL('''
        SELECT cv_id FROM "cv"
        WHERE user_id = %s;
    ''')

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur lors de la récupération du CV : {e}")
        return None


def get_offre_id(titre, offre_societe):
    """
    Récupérer l'ID d'une offre existante en fonction du titre et de la société.
    """
    query = sql.SQL('''
        SELECT offre_id FROM "offre"
        WHERE titre = %s AND offre_societe = %s;
    ''')

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query, (titre, offre_societe))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'offre : {e}")
        return None


# Fonction pour récupérer tous les enregistrements de la base de données
def get_all_candidates():
    """
    Récupérer tous les enregistrements de la table des candidats.
    """
    query = sql.SQL('''SELECT user_id, nom, prenom, mail, numero_tlfn FROM candidat;''')
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query)
        candidat = cursor.fetchall()  
        cursor.close()
        conn.close()
        return [{"user_id": c[0], "nom": c[1], "prenom": c[2], "mail": c[3], "numero_tlfn": c[4]} for c in candidat]
    except Exception as e:
        print(f"Erreur lors de la récupération des candidats : {e}")
        return None

# Fonction pour mettre à jour les informations d'un candidat dans la base de données
def update_candidate(user_id, updated_data):
    conn = connect_to_db()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql.SQL('''UPDATE "candidat" SET nom = %s, prenom = %s, mail = %s, numero_tlfn = %s WHERE user_id = %s;'''),
                           (updated_data['nom'], updated_data['prenom'], updated_data['mail'], updated_data['numero_tlfn'], user_id))
            return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour du candidat : {e}")
        return False
            

# Fonction pour récupérer tous les enregistrements de la base de données
def get_all_offres():
    """
    Récupérer tous les enregistrements de la table des offres.
    """
    query = sql.SQL('''SELECT offre_id, text_offre, offre_societe, titre FROM offre;''')
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query)
        offre = cursor.fetchall()  
        cursor.close()
        conn.close()
        return [{"offre_id": o[0], "text_offre": o[1], "offre_societe": o[2], "titre": o[3]} for o in offre]
    except Exception as e:
        print(f"Erreur lors de la récupération des offres : {e}")
        return None
    

def get_all_cvs():
    """
    Récupérer tous les enregistrements de la table des offres.
    """
    query = sql.SQL('''
        SELECT cv.cv_id, cv.user_id, cv.date_insertion, cv.cv_text, candidat.nom, candidat.prenom, cv.competences
        FROM cv
        JOIN candidat ON cv.user_id = candidat.user_id;
    ''')
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query)
        cv = cursor.fetchall()  
        cursor.close()
        conn.close()
        return [
            {
                "cv_id": v[0],
                "user_id": v[1],
                "date_insertion": v[2],
                "cv_text": v[3],
                "nom": v[4],
                "prenom": v[5],
                "competences": v[6]

            }
            for v in cv
        ]
    except Exception as e:
        print(f"Erreur lors de la récupération des cvs: {e}")
        return None

# Fonction pour mettre à jour les informations d'un candidat dans la base de données
def update_offre(offre_id, updated_data):
    conn = connect_to_db()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql.SQL('''UPDATE "offre" SET text_offre= %s, offre_societe = %s, titre = %s WHERE offre_id = %s;'''),
                           (updated_data['text_offre'], updated_data['offre_societe'], updated_data['titre'], offre_id))
            return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour de l'offre: {e}")
        return False
    
    # Fonction pour récupérer tous les enregistrements de la base de données
def get_all_resultats():
    """
    Récupérer tous les enregistrements de la table des offres.
    """
    query = sql.SQL('''SELECT resultat_id, cv_id, offre_id, cosine_similarity FROM resultat;''')
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query)
        resultat = cursor.fetchall()  
        cursor.close()
        conn.close()
        return [{"resultat_id": r[0], "cv_id": r[1], "offre_id": r[2], "cosine_similarity": r[3]} for r in resultat]
    except Exception as e:
        print(f"Erreur lors de la récupération des offres : {e}")
        return None
    

# Fonction pour mettre à jour les informations d'un candidat dans la base de données
def resultat(resultat_id, updated_data):
    conn = connect_to_db()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(sql.SQL('''UPDATE "resultat" SET cv_id= %s, offre_id = %s, cosine_similarity = %s WHERE resultat_id = %s;'''),
                           (updated_data['cv_id'], updated_data['offre_id'], updated_data['cosine_similarity'], resultat_id))
            return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour de l'offre: {e}")
        return False
    

def get_user_id1(nom, prenom):
    """
    Récupérer l'ID d'un utilisateur existant en fonction de ses informations.
    """
    query = sql.SQL('''
        SELECT user_id FROM "candidat"
        WHERE nom = %s AND prenom = %s;
    ''')

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query, (nom, prenom))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        return None
    
def save_to_user1(nom, prenom):
    try:
        conn = connect_to_db()
        conn.autocommit = True
        cursor = conn.cursor()

        # Insertion de l'utilisateur
        cursor.execute(sql.SQL('''
            INSERT INTO "candidat" (nom, prenom, mail, numero_tlfn)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id;
        '''), (nom, prenom))
        
        # Récupération de l'ID de l'utilisateur (assurez-vous que c'est un entier)
        user_id = cursor.fetchone()[0]
        
        return user_id

    except psycopg2.Error as e:
        print(f"Erreur lors de l'enregistrement du CV: {e}")
        return None

    finally:
        if conn:
            conn.close()
