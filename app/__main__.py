from app.app import app
from app.db.neo4j_db import Neo4jDB
from app.db.postgres_db import PostgresDB

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
