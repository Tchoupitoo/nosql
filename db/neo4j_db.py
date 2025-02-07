from neo4j import GraphDatabase
from db.base_db import *
import uuid
from utils import execute_with_timer
import os

class Neo4jDB(base_db):
    def __init__(self):
        self.neo4j_driver = GraphDatabase.driver(
            f"bolt://{os.getenv('ENV_NEO4J_HOST')}:{os.getenv('ENV_NEO4J_BOLT_PORT')}",
            auth=(os.getenv("ENV_NEO4J_USER"), os.getenv("ENV_NEO4J_PASSWORD"))
        )

    def init_db(self):
        with self.neo4j_driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:Utilisateur) REQUIRE u.id IS UNIQUE;")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Produit) REQUIRE p.id IS UNIQUE;")

    def clear_db(self):
        try:
            with self.neo4j_driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n;")
                print("Base de données Neo4j réinitialisée avec succès.")

                self.init_db()
        except Exception as e:
            print(f"Erreur lors de la réinitialisation de la base de données Neo4j: {e}")


    def create_users(self, num_users):
        users = []
        execution_time = 0
        with self.neo4j_driver.session() as session:
            for _ in range(num_users):
                nom = fake.name()
                user_id = str(uuid.uuid4())
                execution_time += execute_with_timer(session.run,
                    "CREATE (u:Utilisateur {id: $id, nom: $nom})",
                    id=user_id,
                    nom=nom)
                users.append({"id": user_id, "nom": nom})

            users_list = session.run("MATCH (u:Utilisateur) RETURN u.id AS id")
            users_id = [record["id"] for record in users_list]

            for user in users:
                num_followers = random.randint(0, 20)
                followers = random.sample(users_id, min(num_followers, len(users_id)))

                for follower_id in followers:
                    if follower_id != user["id"]:
                        start_time = datetime.now()
                        execution_time += execute_with_timer(session.run,
                            """
                                MATCH (a:Utilisateur {id: $user_id}), (b:Utilisateur {id: $follower_id})
                                CREATE (a)-[:FOLLOWS]->(b)
                            """,
                            follower_id=follower_id,
                            user_id=user["id"])

        return users, execution_time

    def create_produits(self, num_produits):
        produits = []
        execution_time = 0
        with self.neo4j_driver.session() as session:
            for _ in range(num_produits):
                nom = fake.word()
                prix = round(random.uniform(5, 500), 2)
                produit_id = str(uuid.uuid4())
                execution_time += execute_with_timer(session.run, 
                    "CREATE (p:Produit {id: $id, nom: $nom, prix: $prix})",
                    id=produit_id,
                    nom=nom,
                    prix=prix)
                produits.append({"id": produit_id, "nom": nom, "prix": prix})

        return produits, execution_time

    def create_achats(self, num_achats):
        achats = []
        execution_time = 0
        with self.neo4j_driver.session() as session:
            user_results = session.run("MATCH (u:Utilisateur) RETURN u.id AS id")
            user_ids = [record["id"] for record in user_results]

            produit_results = session.run("MATCH (p:Produit) RETURN p.id AS id")
            produit_ids = [record["id"] for record in produit_results]

            if not user_ids or not produit_ids:
                raise ValueError("Pas assez d'utilisateurs ou de produits disponibles.")

            for utilisateur_id in user_ids:
                num_achats_utilisateur = random.randint(0, 5)
                produits_achetes = random.sample(produit_ids, min(num_achats_utilisateur, len(produit_ids)))

                for produit_id in produits_achetes:
                    date_achat = datetime.now().isoformat()
                    execution_time += execute_with_timer(session.run,
                        """
                            MATCH (u:Utilisateur {id: $utilisateur_id}), (p:Produit {id: $produit_id})
                            CREATE (u)-[:ACHAT {date: $date}]->(p)
                        """,
                        utilisateur_id=utilisateur_id,
                        produit_id=produit_id,
                        date=date_achat)

                    achats.append({"utilisateur_id": utilisateur_id, "produit_id": produit_id, "date_achat": date_achat})

        return achats, execution_time

    def db_size(self):
        with self.neo4j_driver.session() as session:
            start_time = datetime.now()
            result = session.run("MATCH (u:Utilisateur) RETURN count(u) AS nb_utilisateurs")
            nb_utilisateurs = result.single()["nb_utilisateurs"]

            result = session.run("MATCH ()-[:FOLLOWS]->() RETURN count(*) AS nb_followers")
            nb_followers = result.single()["nb_followers"]

            result = session.run("MATCH (p:Produit) RETURN count(p) AS nb_produits")
            nb_produits = result.single()["nb_produits"]

            result = session.run("MATCH ()-[:ACHAT]->() RETURN count(*) AS nb_achats")
            nb_achats = result.single()["nb_achats"]

            end_time = datetime.now()
            return {
                "nb_utilisateurs": nb_utilisateurs,
                "nb_followers": nb_followers,
                "nb_produits": nb_produits,
                "nb_achats": nb_achats
            }, (end_time - start_time).total_seconds() * 1000

    def request1(self):
        # Get number of followers for each user
        with self.neo4j_driver.session() as session:
            start_time = datetime.now()
            result = session.run("""
                MATCH (u:Utilisateur)
                OPTIONAL MATCH (u)-[:FOLLOWS]->(f)
                RETURN u.id AS id, u.nom AS nom, COUNT(f) AS nb_followers
            """)
            end_time = datetime.now()
            
            result = [record.data() for record in result]

            return result, (end_time - start_time).total_seconds() * 1000


    def request2(self):
        pass

    def request3(self):
        pass

    def request4(self):
        pass