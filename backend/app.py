"""
Backend REST API for the AI Skin & Hair Health Assistant.

This is a pure JSON API layer over the LangGraph agentic pipeline defined in
graph/build_graph.py. It has no server-rendered pages of its own -- the
frontend/ folder (a separate static site) is the only UI, and it talks to
this API over HTTP (fetch) using the endpoints below.

Endpoints:
    POST /api/analyze   -> multipart/form-data (matches the intake form),
                            runs the full LangGraph agent, returns JSON state
    POST /api/book       -> JSON { session_id } , re-invokes the graph with
                            wants_booking=True using the stored prior state
    GET  /api/health     -> simple liveness check

Run with:
    pip install -r requirements.txt
    python app.py

Then open frontend/index.html (served separately, e.g. via
`python -m http.server` inside frontend/, or any static host) and it will
call this API at http://127.0.0.1:5000.
"""

import os
import uuid
import tempfile

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

from graph.build_graph import build_graph

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_upload_folder():
    """Prefer a local uploads/ folder; fall back to the system temp dir if
    the filesystem is read-only (e.g. on serverless platforms like Vercel)."""
    preferred = os.path.join(BASE_DIR, "uploads")
    try:
        os.makedirs(preferred, exist_ok=True)
        return preferred
    except OSError:
        fallback = os.path.join(tempfile.gettempdir(), "skin_hair_uploads")
        os.makedirs(fallback, exist_ok=True)
        return fallback


UPLOAD_FOLDER = _resolve_upload_folder()
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB photo limit

# Allow the separately-hosted frontend (different origin/port) to call this
# API. Implemented by hand (no flask-cors dependency needed) so the two
# folders can be run/deployed completely independently of each other.
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/<path:_any>", methods=["OPTIONS"])
def cors_preflight(_any):
    return ("", 204)


_graph_app = build_graph()

# In-memory store mapping a session_id -> last graph state, so /api/book can
# re-invoke the graph with wants_booking=True without the client resending
# the whole form. (Swap for Redis/a DB in production.)
_SESSIONS: dict[str, dict] = {}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    form = request.form
    image_path = None

    photo = request.files.get("photo")
    if photo and photo.filename and _allowed_file(photo.filename):
        unique_name = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        photo.save(image_path)

    initial_state = {
        "user_name": form.get("user_name", "Guest"),
        "concern_type": form.get("concern_type", "skin"),
        "symptoms_text": form.get("symptoms_text", ""),
        "image_path": image_path,
        "skin_or_hair_type": form.get("skin_or_hair_type", "normal"),
        "budget": form.get("budget", "medium"),
        "city": form.get("city", ""),
        "wants_booking": False,
    }

    result = _graph_app.invoke(initial_state)

    session_id = uuid.uuid4().hex
    _SESSIONS[session_id] = result

    return jsonify({"session_id": session_id, "result": result})


@app.route("/api/book", methods=["POST"])
def book():
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")

    prior_state = _SESSIONS.get(session_id)
    if not prior_state:
        return jsonify({"error": "No matching session. Please run an analysis first."}), 400

    prior_state = dict(prior_state)
    prior_state["wants_booking"] = True
    result = _graph_app.invoke(prior_state)
    _SESSIONS[session_id] = result

    return jsonify({"session_id": session_id, "result": result})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
