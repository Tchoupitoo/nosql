import os
import random
import uuid
from datetime import datetime

from neo4j import GraphDatabase

from app.db.base_db import *
from app.utils import execute_with_timer


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

    def create_achats(self, num_achats_not_used):
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

                    achats.append(
                        {"utilisateur_id": utilisateur_id, "produit_id": produit_id, "date_achat": date_achat})

        return achats, execution_time

    def select_users(self, num_users):
        with self.neo4j_driver.session() as session:
            start_time = datetime.now()
            result = session.run(
                """
                MATCH (u:Utilisateur)
                RETURN u.id AS id, u.nom AS nom
                ORDER BY rand()
                LIMIT $num
                """,
                {"num": num_users}
            )
            end_time = datetime.now()

            result = [record.data() for record in result]

            return result, (end_time - start_time).total_seconds() * 1000

    def select_produits(self, num_produits):
        with self.neo4j_driver.session() as session:
            start_time = datetime.now()
            result = session.run(
                """
                MATCH (p:Produit)
                RETURN p.id AS id, p.nom AS nom, p.prix AS prix
                ORDER BY rand()
                LIMIT $num
                """,
                {"num": num_produits}
            )
            end_time = datetime.now()

            result = [record.data() for record in result]

            return result, (end_time - start_time).total_seconds() * 1000

    def db_size(self):
        with self.neo4j_driver.session() as session:
            start_time = datetime.now()
            result = session.run("MATCH (u:Utilisateur) RETURN count(u) AS nb_utilisateurs")
            nb_utilisateurs = result.single()["nb_utilisateurs"]

            result = session.run("MATCH ()-[:FOLLOWS]->() RETURN count(*) AS nb_follows")
            nb_follows = result.single()["nb_follows"]

            result = session.run("MATCH (p:Produit) RETURN count(p) AS nb_produits")
            nb_produits = result.single()["nb_produits"]

            result = session.run("MATCH ()-[:ACHAT]->() RETURN count(*) AS nb_achats")
            nb_achats = result.single()["nb_achats"]

            end_time = datetime.now()
            return {
                "nb_utilisateurs": nb_utilisateurs,
                "nb_follows": nb_follows,
                "nb_produits": nb_produits,
                "nb_achats": nb_achats
            }, (end_time - start_time).total_seconds() * 1000

    def requestGlobalFollows(self):
        with self.neo4j_driver.session() as session:
            start_time = datetime.now()
            result = session.run("""
                MATCH (u:Utilisateur)
                OPTIONAL MATCH (f)-[:FOLLOWS]->(u)
                RETURN u.id AS id, u.nom AS nom, COUNT(f) AS nb_followers ORDER BY nb_followers DESC
            """)
            end_time = datetime.now()

            result = [record.data() for record in result]

            return result, (end_time - start_time).total_seconds() * 1000

    def requestGlobalAchatsByProduit(self):
        with self.neo4j_driver.session() as session:
            start_time = datetime.now()

            result = session.run("""
                MATCH (u:Utilisateur)-[:ACHAT]->(p:Produit)
                RETURN 
                    p.id AS product_id, 
                    p.nom AS product_name, 
                    COUNT(DISTINCT u) AS num_buyers
                ORDER BY num_buyers DESC
            """)

            end_time = datetime.now()

            results = [record.data() for record in result]

            return {"results": results}, (end_time - start_time).total_seconds() * 1000

    def requestSpecific1(self, user_id, max_level=3):
        query = f"""
        MATCH (follower)-[:FOLLOWS*1..{max_level}]->(u:Utilisateur {{id: "{user_id}"}})
        MATCH (follower)-[:ACHAT]->(p:Produit)
        RETURN 
            p.id AS product_id, 
            p.nom AS product_name, 
            COUNT(*) AS nb_achats
        ORDER BY nb_achats DESC
        """

        start_time = datetime.now()
        with self.neo4j_driver.session() as session:
            result = session.run(query)
            records = result.data()

        end_time = datetime.now()

        results = [
            {"product_id": row["product_id"], "product_name": row["product_name"], "nb_achats": row["nb_achats"]}
            for row in records
        ]

        return results, (end_time - start_time).total_seconds() * 1000

    def requestSpecific2(self, user_id, product_id, max_level=3):
        query = f"""
        MATCH (follower)-[:FOLLOWS*1..{max_level}]->(u:Utilisateur {{id: "{user_id}"}})
        MATCH (follower)-[:ACHAT]->(p:Produit {{id: "{product_id}"}})
        RETURN
            COUNT(*) AS nb_achats
        ORDER BY nb_achats DESC
        """

        start_time = datetime.now()
        with self.neo4j_driver.session() as session:
            result = session.run(query)
            records = [record.data() for record in result]

        end_time = datetime.now()

        return records[0]["nb_achats"], (end_time - start_time).total_seconds() * 1000

    def requestSpecific3(self, product_id, max_level=3):
        query = f"""
        MATCH (follower)-[:FOLLOWS*1..{max_level}]->(u:Utilisateur)
        MATCH (follower)-[:ACHAT]->(p:Produit {{id: "{product_id}"}})
        RETURN p.id AS product_id, p.nom AS product_name, COUNT(DISTINCT follower) AS num_buyers
        ORDER BY num_buyers DESC
        """

        start_time = datetime.now()
        with self.neo4j_driver.session() as session:
            result = session.run(query)
            records = result.data()

        end_time = datetime.now()

        results = [
            {"product_id": row["product_id"], "product_name": row["product_name"], "num_buyers": row["num_buyers"]}
            for row in records
        ]

        return results, (end_time - start_time).total_seconds() * 1000
