from typing import Dict, Any, List
from datetime import datetime, timedelta
import pytz
import swisseph as swe
import math, os, json
from ..config import EPHE_PATH

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
    "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO
}
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def _to_julday_utc(date_iso: str, time_str: str|None, tz_name: str) -> float:
    hour, minute = 12, 0
    if time_str:
        parts = time_str.split(":")
        hour = int(parts[0]); minute = int(parts[1]) if len(parts)>1 else 0
    local = pytz.timezone(tz_name).localize(datetime.fromisoformat(f"{date_iso}T{hour:02d}:{minute:02d}:00"))
    utc = local.astimezone(pytz.utc)
    jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute/60.0 + utc.second/3600.0)
    return jd

def _lon_to_sign_idx(lon: float) -> int:
    return int(math.floor((lon % 360.0) / 30.0))

def compute_chart(birth: Dict[str,Any]) -> Dict[str,Any]:
    swe.set_ephe_path(EPHE_PATH)
    jd = _to_julday_utc(birth["date"], birth.get("time"), birth.get("tz","UTC"))
    planets: Dict[str, Dict[str, float]] = {}
    for name, pcode in PLANETS.items():
        lon, lat, dist, _ = swe.calc_ut(jd, pcode, swe.FLG_SWIEPH | swe.FLG_SPEED)
        planets[name] = {"sign": _lon_to_sign_idx(lon), "lon": float(lon)}
    known_time = (birth.get("time_precision","exact") == "exact" and birth.get("time"))
    if known_time:
        houses, ascmc, _, _ = swe.houses_ex(jd, int(0), birth["lat"], birth["lng"], b"P")
        house_cusps = {f"H{i+1}": float(houses[i]) for i in range(12)}
        method = "placidus"
    else:
        sun_lon = planets["Sun"]["lon"]
        asc = 30.0 * _lon_to_sign_idx(sun_lon)
        house_cusps = {f"H{i}": (asc + (i-1)*30.0)%360.0 for i in range(1,13)}
        method = "whole_sign_solar"
    aspects: List[Dict[str,Any]] = []
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
        "id": f"sw_{abs(hash((birth['date'], birth.get('time'), birth['lat'], birth['lng']))):x}"[:10],
        "method": method,
        "datetime_utc": "from_local_tz",
        "tz": birth.get("tz","UTC"),
        "lat": birth["lat"],
        "lng": birth["lng"],
        "planets": planets,
        "houses": house_cusps,
        "aspects": aspects,
        "meta": {"name": birth.get("name","You"), "place": birth["place"], "time_precision": birth.get("time_precision","exact")}
    }

def current_positions(jd_ut: float) -> Dict[str, float]:
    swe.set_ephe_path(EPHE_PATH)
    pos = {}
    for name, pcode in PLANETS.items():
        lon, lat, dist, _ = swe.calc_ut(jd_ut, pcode, swe.FLG_SWIEPH | swe.FLG_SPEED)
        pos[name] = lon % 360.0
    return pos

def aspects_to_natal(transit_pos: Dict[str,float], natal_points: Dict[str,float], orb_limits: Dict[str,float]|None=None) -> List[Dict[str,Any]]:
    majors = [("conjunction",0),("opposition",180),("trine",120),("square",90),("sextile",60)]
    results = []
    for tname, tlon in transit_pos.items():
        for nname, nlon in natal_points.items():
            ang = abs(tlon - nlon) % 360.0
            ang = min(ang, 360.0-ang)
            for name, exact in majors:
                orb_limit = 2.0 if orb_limits is None else orb_limits.get(name, 2.0)
                orb = abs(ang - exact)
                if orb <= orb_limit:
                    results.append({"transit": tname, "natal": nname, "aspect": name, "orb": round(orb,2)})
                    break
    return results

def compute_transits(date: str, days: int, tz: str, natal_points: Dict[str,float]) -> List[Dict[str,Any]]:
    swe.set_ephe_path(EPHE_PATH)
    # compute at local noon per day
    zone = pytz.timezone(tz)
    start = zone.localize(datetime.fromisoformat(date + "T00:00:00"))
    events: List[Dict[str,Any]] = []
    for d in range(days):
        cur = start + timedelta(days=d)
        noon_utc = cur.astimezone(pytz.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        jd = swe.julday(noon_utc.year, noon_utc.month, noon_utc.day, noon_utc.hour + noon_utc.minute/60.0)
        tpos = current_positions(jd)
        hits = aspects_to_natal(tpos, natal_points)
        for h in hits:
            h2 = dict(h); h2["date"] = cur.date().isoformat()
            events.append(h2)
    return events
