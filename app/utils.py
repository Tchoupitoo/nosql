import json
import os
from datetime import datetime


def execute_with_timer(func, *args, **kwargs):
    start_time = datetime.now()
    func(*args, **kwargs)
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds() * 1000
    return execution_time


def add_to_history(db_target, command, nb_entities, execution_time):
    command_history = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "db_target": db_target,
        "command": command,
        "nb_entities": nb_entities,
        "execution_time": execution_time
    }

    with open("/app/logs/history.json", "a") as f:
        f.write(json.dumps(command_history) + "\n")  # Convertir en JSON et ajouter un saut de ligne

    return command_history


def get_history():
    if not os.path.exists("/app/logs/history.json"):
        return []

    history = []
    with open("/app/logs/history.json", "r") as f:
        for line in f:
            history.append(json.loads(line))
    return history


def clear_history():
    if os.path.exists("/app/logs/history.json"):
        os.remove("/app/logs/history.json")
    return "Historique effacé"
