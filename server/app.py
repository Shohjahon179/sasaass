import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import Json, RealDictCursor

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://vagon_user:vagon_pass@localhost:5432/vagon_db")
pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
COLLECTIONS = {"users", "records", "messages"}


def init_db():
    conn = pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sync_items (
                        collection TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        PRIMARY KEY (collection, item_id)
                    )
                """)
    finally:
        pool.putconn(conn)


@app.get("/health")
def health():
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify({"ok": True, "database": "postgresql"})
    except Exception:
        app.logger.exception("Health check failed")
        return jsonify({"ok": False, "error": "database unavailable"}), 503
    finally:
        pool.putconn(conn)


def validate_collection(collection):
    return collection in COLLECTIONS


@app.get("/api/vagon_app/<collection>")
def list_items(collection):
    if not validate_collection(collection):
        return jsonify({"error": "unknown collection"}), 404
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT item_id, payload FROM sync_items WHERE collection = %s ORDER BY updated_at ASC",
                (collection,),
            )
            rows = cur.fetchall()
        return jsonify({row["item_id"]: row["payload"] for row in rows})
    except Exception:
        app.logger.exception("List failed")
        return jsonify({"error": "database error"}), 500
    finally:
        pool.putconn(conn)


@app.put("/api/vagon_app/<collection>/<item_id>")
def upsert_item(collection, item_id):
    if not validate_collection(collection):
        return jsonify({"error": "unknown collection"}), 404
    if not item_id or len(item_id) > 180 or "/" in item_id:
        return jsonify({"error": "invalid item id"}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON object required"}), 400
    conn = pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sync_items (collection, item_id, payload, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (collection, item_id)
                    DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                """, (collection, item_id, Json(payload)))
        return jsonify({"ok": True}), 200
    except Exception:
        app.logger.exception("Upsert failed")
        return jsonify({"error": "database error"}), 500
    finally:
        pool.putconn(conn)


@app.delete("/api/vagon_app/<collection>/<item_id>")
def delete_item(collection, item_id):
    if not validate_collection(collection):
        return jsonify({"error": "unknown collection"}), 404
    conn = pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM sync_items WHERE collection = %s AND item_id = %s",
                    (collection, item_id),
                )
        return jsonify({"ok": True}), 200
    except Exception:
        app.logger.exception("Delete failed")
        return jsonify({"error": "database error"}), 500
    finally:
        pool.putconn(conn)


init_db()

if __name__ == "__main__":
    # Local-network development only. Use HTTPS + production WSGI server when deployed.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
