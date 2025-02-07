from flask import Flask, request, jsonify, render_template, send_from_directory
from db.postgres_db import PostgresDB
from db.neo4j_db import Neo4jDB
import os
from dotenv import load_dotenv
from utils import *

load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/history', methods=["GET"])
def history():
    return jsonify(get_history())

def create_entities(entity_type):
    data = request.json
    nb_entities = int(data.get(f"nb_entities", 1))
    db_target = data.get("db_target")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    create_function = getattr(db, f"create_{entity_type}", None)

    if not create_function:
        return jsonify({"error": f"Function create_{entity_type} not found"}), 400

    results, execution_time = create_function(nb_entities)

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, f"insert_{entity_type}", nb_entities, round(execution_time, 3))
    })

@app.route('/create_users', methods=["POST"])
def create_users():
    return create_entities("users")

@app.route('/create_produits', methods=["POST"])
def create_produits():
    return create_entities("produits")

@app.route('/create_achats', methods=["POST"])
def create_achats():
    return create_entities("achats")

@app.route('/size', methods=["POST"])
def db_size():
    data = request.json
    db_target = data.get("db_target")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    size, execution_time = db.db_size()

    return jsonify({
        "command_history": add_to_history(db_target, "db_size", 0, round(execution_time, 3)),
        "size": size
    })

@app.route('/clear', methods=["POST"])
def clear_db():
    data = request.json
    db_target = data.get("db_target")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    execution_time = execute_with_timer(db.clear_db)

    return jsonify({
        "result": f"Base de données {db_target} réinitialisée",
        "command_history": add_to_history(db_target, "clear_db", 0, round(execution_time, 3))
    })

@app.route('/request1', methods=["POST"])
def request1():
    data = request.json
    db_target = data.get("db_target")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    results, execution_time = db.request1()

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, "nb_followers", 0, round(execution_time, 3))
    })

if __name__ == "__main__":
    postgres_db = PostgresDB()
    postgres_db.init_db()

    neo4j_db = Neo4jDB()
    neo4j_db.init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)