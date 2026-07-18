# Backend — LangGraph Agent + REST API

This is the entire "brain" of the assistant: a **LangGraph agent** wrapped in
a small Flask **JSON API**. It has no HTML pages of its own — the
`../frontend` folder is a completely separate static site that talks to this
API over HTTP. You can run, test, and deploy this backend independently of
any frontend.

## Architecture

```
graph/state.py         -> AssistantState (the shared state schema)
graph/nodes.py          -> node functions (pure logic, testable on their own)
graph/build_graph.py    -> wires nodes into a LangGraph StateGraph (the agent)
services/               -> the "AI"/data logic each node calls into
  image_analysis.py     -> heuristic photo analysis
  product_catalog.py    -> product recommendation
  reminders.py          -> habit reminder generator
  booking.py            -> dermatologist directory + mock appointment booking
data/                   -> mock product catalog + dermatologist directory
app.py                  -> Flask REST API (JSON only — /api/analyze, /api/book)
uploads/                -> uploaded photos land here (created automatically)
cli.py                  -> interactive terminal demo (talks to the graph directly)
```

### Graph flow (the agent)

```
START
  -> intake                  (scan symptom text for red flags)
  -> image_analysis          (heuristic photo stats, if a photo was given)
  -> risk_assessment         (combine text + photo signals -> low/moderate/high)
  -> routine_recommendation
  -> product_recommendation
  -> reminders
  -> referral                (decide if a dermatologist is needed)
  -> [conditional] booking   (only if high risk AND user agrees to book)
  -> END
```

The conditional edge (`route_after_referral`) is the key LangGraph feature
here: the agent *branches* based on state instead of running a fixed linear
script. `app.py` never talks to the individual nodes/services directly — it
only calls `build_graph().invoke(state)`, exactly like `cli.py` does, so the
API and the CLI are both thin clients of the same agent.

## API

| Method | Path          | Body                              | Returns |
|--------|---------------|------------------------------------|---------|
| GET    | `/api/health` | —                                  | `{ "status": "ok" }` |
| POST   | `/api/analyze`| `multipart/form-data` (form fields + optional `photo`) | `{ "session_id", "result" }` |
| POST   | `/api/book`   | `application/json` `{ "session_id" }` | `{ "session_id", "result" }` |

`result` is the full `AssistantState` produced by the graph (routine,
recommended products, reminders, risk level, referral message, booking
details, etc.) — the frontend renders this directly.

Sessions are kept in an in-memory dict keyed by `session_id` so `/api/book`
can re-invoke the graph with `wants_booking=True` without the client
resending the whole form. Swap `_SESSIONS` for Redis/a database in
production, and consider adding auth if this API becomes public.

CORS is enabled by hand in `app.py` (`Access-Control-Allow-Origin: *`) so the
frontend can call this API from a different origin/port with no extra
dependency required.

## Run locally

```
cd backend
pip install -r requirements.txt
python app.py
```

The API listens on `http://127.0.0.1:5000` by default (override with the
`PORT` env var). Then open `../frontend/index.html` in a browser, or serve
the frontend folder with any static server — see `../frontend/README.md`.

## CLI (no frontend needed)

```
cd backend
python cli.py
```

Walks through the same LangGraph agent in the terminal — useful for testing
the pipeline logic without touching the API or frontend at all.

## Deploying

Works well on **Render** (a real always-on process, so the in-memory
sessions and `data/appointments.json` persist between requests) or as
serverless functions on **Vercel** (`vercel.json` included) — on Vercel,
uploaded photos and sessions may not persist between requests since
serverless functions don't guarantee a persistent disk/process; the code
already falls back to a temp folder so it won't crash, it just won't
remember things across requests the way Render will.

Whichever you choose, once deployed, point the frontend at it by setting
`window.API_BASE_URL` in `frontend/index.html` to your deployed URL.
