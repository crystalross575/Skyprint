# Skyprint — Render-ready App (FastAPI + Static UI)

This is your **click-a-link** astrology app. Deploy it to Render in minutes — no coding.

## Quick Deploy (Render)
1) Push this folder to a GitHub repo (GitHub → New → Upload files → drag everything inside this folder).
2) In Render: **New + → Blueprint** → connect your repo.
3) Click **Create Resources** → **Deploy**.
4) Your app will be live at a URL like `https://skyprint.onrender.com`.

### Endpoints
- UI: `/`
- Mock charts (instant): `POST /api/charts`
- Swiss charts (real math): `POST /api/charts/swiss`
- Daily transits: `GET /api/transits?date=YYYY-MM-DD&days=7&tz=America/Chicago&natal_json={...}`
- Export PDF: `GET /api/export/pdf?reading_id=...`

### Swiss Ephemeris files
- For **real planetary & house positions**, add the Swiss ephemeris data files to the `/ephe` folder here, or set env var `SWISS_EPHE_PATH`.
- If those files are missing, the app will automatically fall back to the mock engine (you’ll see a note in the UI).

### Notes
- Everything is served by one FastAPI app (no Node build needed).
- Content blocks live in `content/` — add more JSON files to expand interpretations.
