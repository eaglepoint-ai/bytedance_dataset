# app.py
from flask import Flask, jsonify
from repository_before import db
from repository_before.access_logic import get_accessible_resources

def create_app(db_url=None):
    app = Flask(__name__)
    db.init_db(db_url)

    @app.route("/dashboard/<user_id>")
    def dashboard(user_id):
        session = db.SessionLocal()
        try:
            data = get_accessible_resources(session, user_id)
            return jsonify(data)
        finally:
            session.close()

    return app


if __name__ == "__main__":
    app = create_app()  # Uses DATABASE_URL from environment
    app.run(host="0.0.0.0", port=5000)
