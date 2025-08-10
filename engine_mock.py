# Fast mock engine so the app works instantly even without Swiss files
from datetime import datetime, timezone
import hashlib, os, json, math
from typing import Dict, Any, List

PLANETS = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]

def _deterministic_longitude(seed: str, offset: int) -> float:
    h = hashlib.sha256((seed+str(offset)).encode()).hexdigest()
    val = int(h[:8], 16) % 36000 / 100.0
    return float(val)

def _sign_idx(lon: float) -> int:
    return int(math.floor((lon % 360.0) / 30.0))

def compute_chart(birth: Dict[str,Any]) -> Dict[str,Any]:
    dt_local = datetime.fromisoformat(birth["date"] + ("T"+birth["time"] if birth.get("time") else "T12:00"))
    dt_utc = dt_local.replace(tzinfo=timezone.utc)
    seed = f"{birth['date']}-{birth.get('time')}-{birth['lat']}-{birth['lng']}"
    planets = {}
    for i, p in enumerate(PLANETS):
        lon = _deterministic_longitude(seed, i)
        planets[p] = {"sign": _sign_idx(lon), "lon": lon}
    asc_lon = _deterministic_longitude(seed, 99)
    houses = {f"H{k}": (asc_lon + (k-1)*30)%360 for k in range(1,13)}
    aspects = []
    majors = [("conjunction",0),("opposition",180),("trine",120),("square",90),("sextile",60)]
    personals = ["Sun","Moon","Mercury","Venus","Mars"]
    for i, a in enumerate(personals):
        for b in personals[i+1:]:
            ang = abs(planets[a]["lon"] - planets[b]["lon"]) % 360.0
            ang = min(ang, 360.0-ang)
            for name, exact in majors:
                orb = abs(ang - exact)
                if orb <= 6.0:
                    aspects.append({"a": a, "b": b, "type": name, "orb": round(orb,2)})
                    break
    return {
        "id": hashlib.md5(seed.encode()).hexdigest()[:10],
        "method": "whole_sign_demo",
        "datetime_utc": dt_utc.isoformat(),
        "tz": birth.get("tz","UTC"),
        "lat": birth["lat"],
        "lng": birth["lng"],
        "planets": planets,
        "houses": houses,
        "aspects": aspects,
        "meta": {"name": birth.get("name","You"), "place": birth["place"], "time_precision": birth.get("time_precision","exact")}
    }

def blocks_dir():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "content")

def load_blocks() -> Dict[str, Any]:
    dirp = blocks_dir()
    data = {}
    for fn in os.listdir(dirp):
        if fn.endswith(".json"):
            with open(os.path.join(dirp, fn), "r", encoding="utf-8") as f:
                blk = json.load(f)
                data[blk["key"]] = blk
    return data

def assemble_reading(chart: Dict[str,Any], blocks: Dict[str,Any]) -> Dict[str,Any]:
    def fetch(k): return blocks.get(k, {"key":k, "title":k, "short":"", "long":"", "actions":[]})
    def sign_name(idx): 
        return ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"][idx]

    sun = sign_name(chart["planets"]["Sun"]["sign"])
    moon = sign_name(chart["planets"]["Moon"]["sign"])

    sections: List[Dict[str,Any]] = []
    sections.append(fetch(f"sun.sign.{sun}"))
    sections.append(fetch(f"moon.sign.{moon}"))
    sections.append(fetch("venus.house.H7"))
    merc = sign_name(chart["planets"]["Mercury"]["sign"])
    if f"mercury.sign.{merc}" in blocks: sections.append(fetch(f"mercury.sign.{merc}"))
    mars = sign_name(chart["planets"]["Mars"]["sign"])
    if f"mars.sign.{mars}" in blocks: sections.append(fetch(f"mars.sign.{mars}"))

    return {"id": chart["id"]+"_r", "chart_id": chart["id"], "signature": ["BigThree","RelationshipFocus"], "sections": sections, "meta": {"name": chart["meta"]["name"]}}
