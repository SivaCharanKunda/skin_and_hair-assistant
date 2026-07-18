# Skin & Hair Health Assistant

An agentic AI assistant (built with **LangGraph**) that reviews a skin/hair
concern (free-text description + optional photo), returns a personalized
routine and product recommendations, flags when a dermatologist should be
seen, and can book that appointment — all as branching steps in a single
LangGraph agent.

The project is split into two independent halves that talk to each other
only over HTTP:

```
skin_and_hair_assistant/
├── backend/    Flask REST API + the LangGraph agent (graph/, services/, data/)
└── frontend/   Static HTML/CSS/JS UI that calls the backend via fetch
```

- **`backend/`** owns all the intelligence: the LangGraph `StateGraph`
  (`backend/graph/build_graph.py`), its nodes (`backend/graph/nodes.py`),
  and the services each node calls into (image analysis, product catalog,
  reminders, booking). `backend/app.py` exposes this agent as a small JSON
  API (`/api/analyze`, `/api/book`). See `backend/README.md`.

- **`frontend/`** is a plain static site — no build step, no framework —
  that renders the intake form and results, and calls the backend's API.
  It can be hosted anywhere (even opened as a local file) as long as it can
  reach the backend's URL. See `frontend/README.md`.

## Quick start

```bash
# 1. Start the backend (the agent + API)
cd backend
pip install -r requirements.txt
python app.py
# -> listening on http://127.0.0.1:5000

# 2. In a second terminal, serve the frontend
cd frontend
python -m http.server 8000
# -> open http://127.0.0.1:8000
```

The frontend is pre-configured to call the backend at
`http://127.0.0.1:5000` (see `frontend/index.html`). If you deploy the
backend elsewhere, update that one line.

## Why LangGraph

The agent is a `StateGraph` over a single shared `AssistantState`, with one
node per step (intake → image analysis → risk assessment → routine →
products → reminders → referral → conditional booking). The interesting
part is the **conditional edge** after `referral`: the graph only routes to
the `booking` node if the risk assessment came back high *and* the user
asked to book — a real branching decision made by the agent at runtime,
not a fixed script. See `backend/README.md` for the full flow diagram and
`backend/graph/` for the implementation.

## What this is (and isn't)

This is a working pipeline/demo, not a trained medical model — the "AI"
inside each node (symptom keyword matching, photo heuristics, product
filtering) is intentionally simple and explainable so it can be swapped
for a real LLM/vision model later without touching the graph wiring or the
API/frontend built on top of it. It does not diagnose conditions; it flags
when a professional opinion is worth getting.
