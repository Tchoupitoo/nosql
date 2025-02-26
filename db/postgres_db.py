import psycopg2
from db.base_db import *


class PostgresDB(base_db):
    def __init__(self):
        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT")
        )
        self.pg_cursor = self.pg_conn.cursor()

    def init_db(self):
        self.pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id VARCHAR(36) PRIMARY KEY,
                nom VARCHAR(255)
            );
                               
            CREATE TABLE IF NOT EXISTS followers (
                utilisateur_id VARCHAR(36) REFERENCES utilisateurs(id),
                follower_id VARCHAR(36) REFERENCES utilisateurs(id),
                PRIMARY KEY (utilisateur_id, follower_id)
            );

            CREATE TABLE IF NOT EXISTS produits (
                id VARCHAR(36) PRIMARY KEY,
                nom VARCHAR(255),
                prix DECIMAL
            );

            CREATE TABLE IF NOT EXISTS achats (
                utilisateur_id VARCHAR(36) REFERENCES utilisateurs(id),
                produit_id VARCHAR(36) REFERENCES produits(id),
                date_achat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (utilisateur_id, produit_id)
            );
        """)
        self.pg_conn.commit()
    
    def clear_db(self):
        try:
            self.pg_cursor.execute("TRUNCATE TABLE utilisateurs, followers, produits, achats RESTART IDENTITY CASCADE;")
            self.pg_conn.commit()
            print("Base de données PostgreSQL réinitialisée avec succès.")
            
            self.init_db()
        except Exception as e:
            self.pg_conn.rollback()
            print(f"Erreur lors de la réinitialisation de la base de données PostgreSQL: {e}")

    def create_users(self, num_users):
        users = []
        execution_time = 0

        for _ in range(num_users):
            nom = fake.name()
            user_id = str(uuid.uuid4())
            execution_time += execute_with_timer(self.pg_cursor.execute,
                "INSERT INTO utilisateurs (id, nom) VALUES (%s, %s) RETURNING id;",
                (user_id, nom,)
            )
            users.append({"id": user_id, "nom": nom})

        execution_time += self.commit()

        self.pg_cursor.execute("SELECT id FROM utilisateurs;")
        users_ids = [{"id": row[0]} for row in self.pg_cursor.fetchall()]

        for user in users:
            num_followers = random.randint(0, 20)
            followers = random.sample(users_ids, min(num_followers, len(users_ids) - 1))

            for follower in followers:
                if follower["id"] != user["id"]:
                    execution_time += execute_with_timer(self.pg_cursor.execute,
                        "INSERT INTO followers (utilisateur_id, follower_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (user["id"], follower["id"]) 
                    )

        execution_time += self.commit()

        return users, execution_time

    def create_produits(self, num_produits):
        produits = []
        execution_time = 0

        for _ in range(num_produits):
            nom = fake.word()
            prix = round(random.uniform(5, 500), 2)
            produit_id = str(uuid.uuid4())
            execution_time += execute_with_timer(self.pg_cursor.execute, 
                "INSERT INTO produits (id, nom, prix) VALUES (%s, %s, %s) RETURNING id;",
                (produit_id, nom, prix)
            )
            produits.append({"id": produit_id, "nom": nom, "prix": prix})

        return produits, execution_time

    def create_achats(self, num_achats_not_used):
        achats = []
        execution_time = 0
        self.pg_cursor.execute("SELECT id FROM utilisateurs;")
        user_ids = [row[0] for row in self.pg_cursor.fetchall()]

        self.pg_cursor.execute("SELECT id FROM produits;")
        produit_ids = [row[0] for row in self.pg_cursor.fetchall()]

        if not user_ids or not produit_ids:
            raise ValueError("Pas assez d'utilisateurs ou de produits disponibles.")

        for utilisateur_id in user_ids:
            num_achats_utilisateur = random.randint(0, 5)
            produits_achetes = random.sample(produit_ids, min(num_achats_utilisateur, len(produit_ids)))

            for produit_id in produits_achetes:
                date_achat = datetime.now()
                execution_time += execute_with_timer(self.pg_cursor.execute,
                    "INSERT INTO achats (utilisateur_id, produit_id, date_achat) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                    (utilisateur_id, produit_id, date_achat)
                )
                achats.append({"utilisateur_id": utilisateur_id, "produit_id": produit_id, "date_achat": date_achat})

        execution_time += self.commit()

        return achats, execution_time

    def select_users(self, num_users):
        start_time = datetime.now()
        self.pg_cursor.execute("SELECT * FROM utilisateurs ORDER BY RANDOM() LIMIT %s;", (num_users,))
        users = self.pg_cursor.fetchall()
        end_time = datetime.now()

        result = [{"id": row[0], "nom": row[1]} for row in users]

        return result, (end_time - start_time).total_seconds() * 1000

    def select_produits(self, num_produits):
        start_time = datetime.now()
        self.pg_cursor.execute("SELECT * FROM produits ORDER BY RANDOM() LIMIT %s;", (num_produits,))
        produits = self.pg_cursor.fetchall()
        end_time = datetime.now()

        result = [{"id": row[0], "nom": row[1], "prix": row[2]} for row in produits]

        return result, (end_time - start_time).total_seconds() * 1000

    def db_size(self):
        start_time = datetime.now()
        self.pg_cursor.execute("SELECT COUNT(*) FROM utilisateurs;")
        nb_utilisateurs = self.pg_cursor.fetchone()[0]

        self.pg_cursor.execute("SELECT COUNT(*) FROM followers;")
        nb_followers = self.pg_cursor.fetchone()[0]

        self.pg_cursor.execute("SELECT COUNT(*) FROM produits;")
        nb_produits = self.pg_cursor.fetchone()[0]

        self.pg_cursor.execute("SELECT COUNT(*) FROM achats;")
        nb_achats = self.pg_cursor.fetchone()[0]
        end_time = datetime.now()

        return {
            "nb_utilisateurs": nb_utilisateurs,
            "nb_follows": nb_followers,
            "nb_produits": nb_produits,
            "nb_achats": nb_achats
        }, (end_time - start_time).total_seconds() * 1000

    def requestGlobalFollows(self):
        start_time = datetime.now()

        self.pg_cursor.execute("""
            SELECT u.id, u.nom, COUNT(f.utilisateur_id) AS nb_followers
            FROM utilisateurs u
            LEFT JOIN followers f ON u.id = f.follower_id
            GROUP BY u.id, u.nom
            ORDER BY nb_followers DESC;           
        """)
        results = self.pg_cursor.fetchall()
        end_time = datetime.now()

        results = [
            {"id": row[0], "nom": row[1], "nb_followers": row[2]} 
            for row in results
        ]
        
        return results, (end_time - start_time).total_seconds() * 1000

    def requestGlobalAchatsByProduit(self):
        start_time = datetime.now()

        self.pg_cursor.execute("""
            SELECT p.id AS product_id, p.nom AS product_name, COUNT(DISTINCT a.utilisateur_id) AS num_buyers
            FROM achats a
            JOIN produits p ON a.produit_id = p.id
            GROUP BY p.id, p.nom
            ORDER BY num_buyers DESC;
        """)
        results = self.pg_cursor.fetchall()
        end_time = datetime.now()

        results = [
            {"product_id": row[0], "product_name": row[1], "num_buyers": row[2]} 
            for row in results
        ]
        
        return results, (end_time - start_time).total_seconds() * 1000
    
    def requestSpecific1(self, user_id, max_level=3): 
        query = """
        WITH RECURSIVE follower_hierarchy AS (
            SELECT follower_id, utilisateur_id, 1 AS level
            FROM followers
            WHERE utilisateur_id = %s
            UNION ALL
            SELECT f.follower_id, f.utilisateur_id, fh.level + 1
            FROM followers f
            INNER JOIN follower_hierarchy fh ON f.utilisateur_id = fh.follower_id
            WHERE fh.level < %s
        )
        SELECT p.id AS product_id, p.nom AS product_name, COUNT(*) AS nb_achats
        FROM follower_hierarchy fh
        JOIN achats a ON fh.follower_id = a.utilisateur_id
        JOIN produits p ON a.produit_id = p.id
        GROUP BY p.id, p.nom
        ORDER BY nb_achats DESC;
        """
    
        start_time = datetime.now()
        self.pg_cursor.execute(query, (user_id, max_level))
        rows = self.pg_cursor.fetchall()
        end_time = datetime.now()
    
        results = [ {"product_id": row[0], "product_name": row[1], "nb_achats": row[2]} for row in rows ]
    
        return results, (end_time - start_time).total_seconds() * 1000

    def requestSpecific2(self, user_id, product_id, max_level=3):
        query = """
        WITH RECURSIVE follower_hierarchy AS (
            SELECT follower_id, utilisateur_id, 1 AS level
            FROM followers
            WHERE utilisateur_id = %s
            UNION ALL
            SELECT f.follower_id, f.utilisateur_id, fh.level + 1
            FROM followers f
            INNER JOIN follower_hierarchy fh ON f.utilisateur_id = fh.follower_id
            WHERE fh.level < %s
        )
        SELECT COUNT(*) AS nb_achats
        FROM follower_hierarchy fh
        JOIN achats a ON fh.follower_id = a.utilisateur_id
        JOIN produits p ON a.produit_id = p.id 
        WHERE p.id = %s
        GROUP BY p.id, p.nom
        ORDER BY nb_achats DESC;
        """
    
        start_time = datetime.now()
        self.pg_cursor.execute(query, (user_id, max_level, product_id))
        rows = self.pg_cursor.fetchall()
        end_time = datetime.now()
    
    
        return rows[0], (end_time - start_time).total_seconds() * 1000

    def requestSpecific3(self, product_id, max_level=3):
        query = """
        WITH RECURSIVE follower_circle AS (
            SELECT a.utilisateur_id, 1 AS level
            FROM achats a
            WHERE a.produit_id = %s
            UNION ALL
            SELECT f.follower_id, fc.level + 1 AS level
            FROM follows f
            JOIN follower_circle fc ON f.utilisateur_id = fc.utilisateur_id
            WHERE fc.level < %s
        )
        SELECT p.id AS product_id, p.nom AS product_name, COUNT(DISTINCT a.utilisateur_id) AS num_buyers
        FROM produits p
        JOIN achats a ON p.id = a.produit_id
        JOIN follower_circle fc ON a.utilisateur_id = fc.utilisateur_id
        WHERE p.id = %s
        GROUP BY p.id, p.nom
        ORDER BY num_buyers DESC;
        """

        start_time = datetime.now()

        self.pg_cursor.execute(query, (product_id, max_level, product_id))
        
        products = self.pg_cursor.fetchall()
        end_time = datetime.now()

        products = [
            {"product_id": row[0], "product_name": row[1], "num_buyers": row[2]} 
            for row in products
        ]

        return products, (end_time - start_time).total_seconds() * 1000


    def commit(self):
        return execute_with_timer(self.pg_conn.commit)