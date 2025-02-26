from flask import Flask, request, jsonify, render_template, send_from_directory

from app.db.neo4j_db import Neo4jDB
from app.db.postgres_db import PostgresDB
from app.utils import *

postgres_db = PostgresDB()
postgres_db.init_db()

neo4j_db = Neo4jDB()
neo4j_db.init_db()
app = Flask(__name__)
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


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
        "command_history": add_to_history(db_target, f"insert_{entity_type}",
                                          nb_entities if entity_type != "achats" else 0, round(execution_time, 3))
    })


def select_entities(entity_type):
    data = request.json
    nb_entities = int(data.get(f"nb_entities", 1))
    db_target = data.get("db_target")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    select_function = getattr(db, f"select_{entity_type}", None)

    if not select_function:
        return jsonify({"error": f"Function select_{entity_type} not found"}), 400

    results, execution_time = select_function(nb_entities)

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, f"select_{entity_type}", nb_entities, round(execution_time, 3))
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


@app.route('/select_users', methods=["POST"])
def select_users():
    return select_entities("users")


@app.route('/select_produits', methods=["POST"])
def select_produits():
    return select_entities("produits")


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


@app.route('/clear_history', methods=["POST"])
def clearHistory():
    clear_history()
    return jsonify({"result": "Historique effacé"})


@app.route('/request/global/follows', methods=["POST"])
def requestGlobalFollows():
    data = request.json
    db_target = data.get("db_target")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    results, execution_time = db.requestGlobalFollows()

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, "nb_followers", 0, round(execution_time, 3))
    })


@app.route('/request/global/achats', methods=["POST"])
def requestGlobalAchatsByProduit():
    data = request.json
    db_target = data.get("db_target")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    results, execution_time = db.requestGlobalAchatsByProduit()

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, "nb_achats", 0, round(execution_time, 3))
    })


@app.route('/request/specific/1', methods=["POST"])
def requestSpecific1():
    data = request.json
    db_target = data.get("db_target")
    user_id = data.get("user_id")
    deep_level = data.get("deep_level")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    results, execution_time = db.requestSpecific1(user_id, deep_level)

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, "nb_achats_produits_deep" + deep_level, 0,
                                          round(execution_time, 3))
    })


@app.route('/request/specific/2', methods=["POST"])
def requestSpecific2():
    data = request.json
    db_target = data.get("db_target")
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    deep_level = data.get("deep_level")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    results, execution_time = db.requestSpecific2(user_id, product_id, deep_level)

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, "nb_achats_produit_unique_deep" + deep_level, 0,
                                          round(execution_time, 3))
    })


@app.route('/request/specific/3', methods=["POST"])
def requestSpecific3():
    data = request.json
    db_target = data.get("db_target")
    product_id = data.get("product_id")
    deep_level = data.get("deep_level")

    if db_target == "postgres":
        db = postgres_db
    elif db_target == "neo4j":
        db = neo4j_db
    else:
        return jsonify({"error": "Invalid database target"}), 400

    results, execution_time = db.requestSpecific3(product_id, deep_level)

    return jsonify({
        "results": results,
        "command_history": add_to_history(db_target, "viralité_produits_deep" + deep_level, 0, round(execution_time, 3))
    })
