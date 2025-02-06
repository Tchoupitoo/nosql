from flask import Flask, send_from_directory, jsonify
import mysql.connector
from neo4j import GraphDatabase

app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")

# Connexion MariaDB
mariadb_conn = mysql.connector.connect(
    host="mariadb",
    user="user",
    password="password",
    database="social_network"
)

# Connexion Neo4j
neo4j_driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

@app.route("/")
def serve_react():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/users")
def get_users():
    cursor = mariadb_conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM utilisateurs")
    users = cursor.fetchall()
    return jsonify(users)

@app.route("/api/graph")
def get_graph():
    with neo4j_driver.session() as session:
        result = session.run("MATCH (n) RETURN n LIMIT 10")
        nodes = [record["n"] for record in result]
    return jsonify(nodes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
