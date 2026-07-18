# Frontend — Static UI

Plain HTML/CSS/JS (no build step, no framework) that renders the intake
form and results view, and talks to the backend purely over HTTP `fetch`
calls. It is a completely separate project from `../backend` — it doesn't
import any backend code and could be deployed to any static host (Netlify,
GitHub Pages, S3, etc.) independently of where the backend runs.

```
index.html    -> page shell, sets window.API_BASE_URL, loads app.js
app.js        -> all UI logic: renders the form, calls the API, renders results
style.css     -> all styling
```

## How it connects to the backend

Every request goes through the `API_BASE_URL` constant at the top of
`app.js` (set in `index.html`):

```html
<script>
  window.API_BASE_URL = window.API_BASE_URL || "http://127.0.0.1:5000";
</script>
```

- `POST {API_BASE_URL}/api/analyze` — submits the intake form
  (`multipart/form-data`, including the optional photo) and renders whatever
  JSON comes back.
- `POST {API_BASE_URL}/api/book` — sent when the user clicks "Book a
  dermatologist appointment", with the `session_id` from the analyze step.

If you deploy the backend somewhere other than your machine, change that one
URL to the deployed backend's address — nothing else needs to change.

## Run locally

Make sure the backend is running first (see `../backend/README.md`), then
just open `index.html` directly in a browser, or serve the folder so
relative paths behave the same as in production:

```
cd frontend
python -m http.server 8000
```

Then visit `http://127.0.0.1:8000`.

## Note on CORS

The backend sends `Access-Control-Allow-Origin: *`, so the frontend can be
served from any origin/port (including `file://`) without extra
configuration.
