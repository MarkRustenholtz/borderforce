#!/usr/bin/env python3
"""Génère data/blablacar_turbie.json pour BorderForce.

Source : GTFS officiel BlaBlaCar Bus publié sur le Point d'Accès National.
Le catalogue conserve uniquement les courses qui passent d'un arrêt italien
vers Nice, puis estime l'heure de passage au péage de La Turbie par
interpolation temporelle entre le dernier arrêt italien et le premier arrêt
niçois.

Le script n'utilise que la bibliothèque standard Python.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

GTFS_URL = "https://www.data.gouv.fr/api/1/datasets/r/fd54f81f-4389-4e73-be75-491133d011c3"
OUT = Path("data/blablacar_turbie.json")
DAYS = 21
DEFAULT_TZ = "Europe/Paris"
TOLL = (43.74367, 7.37827)

# Noms d'arrêts italiens susceptibles de précéder Nice sur les liaisons
# internationales BlaBlaCar Bus. On garde une liste assez large ; le contrôle
# final exige de toute façon qu'un arrêt Nice se trouve ensuite dans la course.
ITALIAN_RE = re.compile(
    r"(?:san\s*remo|sanremo|imperia|ventimiglia|vintimille|savona|savone|"
    r"genoa|genova|g[eê]nes|la\s+spezia|turin|torino|milan|milano|bergamo|"
    r"piacenza|parma|bologna|florence|firenze|rome|roma|naples|napoli|"
    r"verona|venice|venezia|trieste)",
    re.I,
)
NICE_RE = re.compile(r"(?:\bnice\b|\bnizza\b)", re.I)


def log(msg: str) -> None:
    print(msg, flush=True)


def read_csv_from_zip(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    try:
        raw = zf.read(name)
    except KeyError:
        return []
    text = raw.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def parse_gtfs_date(v: str) -> date | None:
    v = (v or "").strip()
    if not re.fullmatch(r"\d{8}", v):
        return None
    return datetime.strptime(v, "%Y%m%d").date()


def parse_gtfs_seconds(v: str) -> int | None:
    v = (v or "").strip()
    m = re.fullmatch(r"(\d{1,3}):(\d{2}):(\d{2})", v)
    if not m:
        return None
    h, mi, s = map(int, m.groups())
    if mi > 59 or s > 59:
        return None
    return h * 3600 + mi * 60 + s


def safe_float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def iso_local(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def service_active_builder(
    calendar_rows: list[dict[str, str]],
    exception_rows: list[dict[str, str]],
):
    weekly: dict[str, dict[str, object]] = {}
    weekday_cols = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    for row in calendar_rows:
        sid = (row.get("service_id") or "").strip()
        start = parse_gtfs_date(row.get("start_date") or "")
        end = parse_gtfs_date(row.get("end_date") or "")
        if not sid or not start or not end:
            continue
        weekly[sid] = {
            "start": start,
            "end": end,
            "days": tuple((row.get(c) or "0").strip() == "1" for c in weekday_cols),
        }

    exceptions: dict[tuple[str, date], int] = {}
    for row in exception_rows:
        sid = (row.get("service_id") or "").strip()
        d = parse_gtfs_date(row.get("date") or "")
        try:
            kind = int((row.get("exception_type") or "0").strip())
        except ValueError:
            kind = 0
        if sid and d and kind in (1, 2):
            exceptions[(sid, d)] = kind

    def active(service_id: str, d: date) -> bool:
        ex = exceptions.get((service_id, d))
        if ex == 1:
            return True
        if ex == 2:
            return False
        base = weekly.get(service_id)
        if not base:
            return False
        return bool(base["start"] <= d <= base["end"] and base["days"][d.weekday()])

    return active


def main() -> None:
    log("Downloading official BlaBlaCar Bus GTFS...")
    req = urllib.request.Request(
        GTFS_URL,
        headers={"User-Agent": "BorderForce-La-Turbie-GTFS/1.0", "Accept": "application/zip,*/*"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = response.read()
    log(f"Downloaded {len(payload) / 1024:.1f} KB")

    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        agency = read_csv_from_zip(zf, "agency.txt")
        stops_rows = read_csv_from_zip(zf, "stops.txt")
        routes_rows = read_csv_from_zip(zf, "routes.txt")
        trips_rows = read_csv_from_zip(zf, "trips.txt")
        stop_times_rows = read_csv_from_zip(zf, "stop_times.txt")
        calendar_rows = read_csv_from_zip(zf, "calendar.txt")
        exception_rows = read_csv_from_zip(zf, "calendar_dates.txt")
        feed_info = read_csv_from_zip(zf, "feed_info.txt")

    tz_name = (agency[0].get("agency_timezone") if agency else "") or DEFAULT_TZ
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz_name = DEFAULT_TZ
        tz = ZoneInfo(DEFAULT_TZ)

    stops: dict[str, dict[str, object]] = {}
    for row in stops_rows:
        sid = (row.get("stop_id") or "").strip()
        if not sid:
            continue
        stops[sid] = {
            "name": (row.get("stop_name") or sid).strip(),
            "lat": safe_float(row.get("stop_lat") or ""),
            "lon": safe_float(row.get("stop_lon") or ""),
        }

    routes = {((r.get("route_id") or "").strip()): r for r in routes_rows if (r.get("route_id") or "").strip()}
    trips = {((t.get("trip_id") or "").strip()): t for t in trips_rows if (t.get("trip_id") or "").strip()}

    times_by_trip: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in stop_times_rows:
        trip_id = (row.get("trip_id") or "").strip()
        stop_id = (row.get("stop_id") or "").strip()
        if trip_id not in trips or stop_id not in stops:
            continue
        try:
            seq = int(float((row.get("stop_sequence") or "0").strip()))
        except ValueError:
            seq = 0
        arr_sec = parse_gtfs_seconds(row.get("arrival_time") or "")
        dep_sec = parse_gtfs_seconds(row.get("departure_time") or "")
        times_by_trip[trip_id].append({
            "seq": seq,
            "stop_id": stop_id,
            "arr": arr_sec,
            "dep": dep_sec,
        })

    for arr in times_by_trip.values():
        arr.sort(key=lambda x: int(x["seq"]))

    active = service_active_builder(calendar_rows, exception_rows)
    today = datetime.now(tz).date()

# On prend aussi la veille.
# Important pour les services GTFS nocturnes dont les horaires
# peuvent dépasser 24:00 (ex. 26:30 = 02:30 le lendemain).
start_date = today - timedelta(days=1)

# On conserve la même portée future qu'avant,
# mais on ajoute la veille au catalogue.
service_dates = [
    start_date + timedelta(days=i)
    for i in range(DAYS + 1)
]

    buses: list[dict[str, object]] = []

    for trip_id, trip in trips.items():
        calls = times_by_trip.get(trip_id) or []
        if len(calls) < 2:
            continue

        nice_index = -1
        italian_index = -1
        for i, call in enumerate(calls):
            stop = stops.get(str(call["stop_id"])) or {}
            if NICE_RE.search(str(stop.get("name") or "")):
                # Il faut au moins un arrêt italien avant ce Nice.
                candidate = -1
                for j in range(i - 1, -1, -1):
                    s2 = stops.get(str(calls[j]["stop_id"])) or {}
                    if ITALIAN_RE.search(str(s2.get("name") or "")):
                        candidate = j
                        break
                if candidate >= 0:
                    nice_index = i
                    italian_index = candidate
                    break
        if nice_index < 0 or italian_index < 0:
            continue

        it_call = calls[italian_index]
        fr_call = calls[nice_index]
        it_stop = stops[str(it_call["stop_id"])]
        fr_stop = stops[str(fr_call["stop_id"])]

        t0 = it_call["dep"] if it_call["dep"] is not None else it_call["arr"]
        t1 = fr_call["arr"] if fr_call["arr"] is not None else fr_call["dep"]
        if t0 is None or t1 is None or int(t1) <= int(t0):
            continue

        it_lat, it_lon = it_stop.get("lat"), it_stop.get("lon")
        fr_lat, fr_lon = fr_stop.get("lat"), fr_stop.get("lon")
        if None in (it_lat, it_lon, fr_lat, fr_lon):
            continue

        d_toll = haversine_km((float(it_lat), float(it_lon)), TOLL)
        d_fr = haversine_km((float(it_lat), float(it_lon)), (float(fr_lat), float(fr_lon)))
        if d_fr <= 0:
            continue
        ratio = max(0.05, min(0.98, d_toll / d_fr))
        eta_sec = int(round(int(t0) + (int(t1) - int(t0)) * ratio))

        route = routes.get((trip.get("route_id") or "").strip(), {})
        line = (
            (route.get("route_short_name") or "").strip()
            or (trip.get("trip_short_name") or "").strip()
            or (trip.get("trip_headsign") or "").strip()
            or (route.get("route_long_name") or "").strip()
            or trip_id
        )

        origin_stop = stops.get(str(calls[0]["stop_id"])) or {}
        destination_stop = stops.get(str(calls[-1]["stop_id"])) or {}
        origin = str(origin_stop.get("name") or "")
        destination = str(destination_stop.get("name") or trip.get("trip_headsign") or "")
        service_id = (trip.get("service_id") or "").strip()

        for d in service_dates:
            if not active(service_id, d):
                continue

            midnight = datetime(d.year, d.month, d.day, tzinfo=tz)
            last_dt = midnight + timedelta(seconds=int(t0))
            next_dt = midnight + timedelta(seconds=int(t1))
            eta_dt = midnight + timedelta(seconds=eta_sec)

            buses.append({
                "id": f"blablacar-gtfs:{trip_id}:{d.isoformat()}",
                "company": "BlaBlaCar Bus",
                "journeyRef": trip_id,
                "tripId": trip_id,
                "routeId": (trip.get("route_id") or "").strip(),
                "line": line,
                "origin": origin,
                "destination": destination,
                "lastItalianStop": str(it_stop.get("name") or ""),
                "nextFrenchStop": str(fr_stop.get("name") or ""),
                "serviceDate": d.isoformat(),
                "lastItalianScheduledIso": iso_local(last_dt),
                "nextFrenchScheduledIso": iso_local(next_dt),
                "etaTurbieIso": iso_local(eta_dt),
                "etaTurbieDate": eta_dt.date().isoformat(),
                "etaTurbieTime": eta_dt.strftime("%H:%M"),
                "etaTurbieDisplay": eta_dt.strftime("%Hh%M"),
                "interpolationRatio": round(ratio, 4),
                "quality": "ESTIME_GTFS_BLABLACAR",
                "qualityLabel": "ESTIMÉ GTFS",
                "cancelled": False,
            })

    # Déduplication stricte puis tri chronologique.
    unique = {str(b["id"]): b for b in buses}
    buses = sorted(unique.values(), key=lambda b: (str(b["etaTurbieIso"]), str(b["id"])))

    feed_start = ""
    feed_end = ""
    if feed_info:
        feed_start = (feed_info[0].get("feed_start_date") or "").strip()
        feed_end = (feed_info[0].get("feed_end_date") or "").strip()

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "BlaBlaCar Bus GTFS officiel — transport.data.gouv.fr",
        "sourceUrl": GTFS_URL,
        "timezone": tz_name,
        "days": DAYS,
        "feedStartDate": feed_start,
        "feedEndDate": feed_end,
        "count": len(buses),
        "buses": buses,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"Wrote {OUT} with {len(buses)} BlaBlaCar Bus passages")


if __name__ == "__main__":
    main()
