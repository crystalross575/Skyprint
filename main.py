from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os, json
from .astro import engine_mock, engine_swiss
from .export_pdf import render_pdf
from datetime import datetime, timedelta
import pytz

app = FastAPI(title="Skyprint — Live", version="1.0.0")

# Mount static
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

class BirthData(BaseModel):
    name: str
    date: str  # YYYY-MM-DD
    time: Optional[str] = None  # HH:MM
    time_precision: str = Field(default="exact", pattern="^(exact|unknown)$")
    place: str
    lat: float
    lng: float
    tz: str = "America/Chicago"

@app.post("/api/charts")
def create_chart_mock(birth: BirthData):
    return engine_mock.compute_chart(birth.model_dump())

@app.post("/api/charts/swiss")
def create_chart_swiss(birth: BirthData):
    try:
        return engine_swiss.compute_chart(birth.model_dump())
    except Exception as e:
        raise HTTPException(500, f"Swiss Ephemeris not available yet ({e}).")

@app.post("/api/readings")
def generate_reading(payload: Dict[str, Any]):
    chart = payload.get("chart")
    if not chart:
        raise HTTPException(400, "Missing chart")
    blocks = engine_mock.load_blocks()  # same loader for both
    reading = engine_mock.assemble_reading(chart, blocks)
    # Save reading JSON so the PDF endpoint can fetch it
    out_dir = os.path.join(STATIC_DIR, "readings")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, reading["id"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(reading, f, ensure_ascii=False, indent=2)
    return reading

@app.get("/api/export/pdf")
def export_pdf(reading_id: str = Query(...)):
    p = os.path.join(STATIC_DIR, "readings", f"{reading_id}.json")
    if not os.path.exists(p):
        raise HTTPException(404, "Reading not found (generate in the UI first)")
    with open(p, "r", encoding="utf-8") as f:
        reading = json.load(f)
    pdf_bytes = render_pdf(reading)
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename=skyprint_{reading_id}.pdf"})

@app.get("/api/transits")
def daily_transits(date: str, days: int = 7, tz: str = "UTC",
                   natal_json: str = Query(..., description="JSON: {name: longitude_deg}")):
    # compute 7-day major hits using Swiss if possible
    try:
        natal = json.loads(natal_json)
    except Exception:
        raise HTTPException(400, "Invalid natal_json")
    try:
        events = engine_swiss.compute_transits(date=date, days=days, tz=tz, natal_points=natal)
    except Exception as e:
        raise HTTPException(500, f"Swiss Ephemeris not available for transits ({e}).")
    return {"events": events}
