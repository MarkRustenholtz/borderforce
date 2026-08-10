#!/usr/bin/env python3
"""Build a small FlixBus Italy -> Nice catalog for BorderForce.

Downloads the official FlixBus Europe GTFS and calculates the theoretical
passage time at the A8 La Turbie toll by projecting the toll and the bounding
stops onto each trip shape, then interpolating scheduled stop times by distance.

Output: flix_turbie.json
Dependencies: Python standard library only.
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
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

GTFS_URL = "https://gtfs.gis.flix.tech/gtfs_generic_eu.zip"
OUT = Path("data/flix_turbie.json")
DAYS = 21
TZ = ZoneInfo("Europe/Paris")
TOLL = (43.74367, 7.37827)

ITALY_RE = re.compile(
    r"san\s*remo|sanremo|ventimiglia|imperia|savona|genoa|genova|g[eê]nes|"
    r"la\s+spezia|turin|torino|milan|milano|bergamo|piacenza|parma|bologna|"
    r"florence|firenze|rome|roma|naples|napoli|verona|venice|venezia|trieste",
    re.I,
)
NICE_RE = re.compile(r"\bnice\b|nizza", re.I)


def read_csv(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        yield from csv.DictReader(text)


def hav_km(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def project_distance(poly, target):
    """Cumulative km on polyline at orthogonal projection nearest target."""
    if len(poly) < 2:
        return None
    lat0 = math.radians(target[0])
    kx = 111.320 * math.cos(lat0)
    ky = 110.574
    tx, ty = target[1] * kx, target[0] * ky

    cum = 0.0
    best = None
    best_d2 = float("inf")
    for a, b in zip(poly, poly[1:]):
        ax, ay = a[1] * kx, a[0] * ky
        bx, by = b[1] * kx, b[0] * ky
        vx, vy = bx - ax, by - ay
        wx, wy = tx - ax, ty - ay
        vv = vx * vx + vy * vy
        t = 0.0 if vv == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / vv))
        px, py = ax + t * vx, ay + t * vy
        d2 = (tx - px) ** 2 + (ty - py) ** 2
        seg = hav_km(a, b)
        if d2 < best_d2:
            best_d2 = d2
            best = cum + seg * t
        cum += seg
    return best


def gtfs_seconds(value: str):
    try:
        h, m, s = map(int, value.split(":"))
        return h * 3600 + m * 60 + s
    except Exception:
        return None


def service_active(service, d, calendars, exceptions):
    key = d.strftime("%Y%m%d")
    exc = exceptions.get((service, key))
    if exc == "1":
        return True
    if exc == "2":
        return False
    c = calendars.get(service)
    if not c:
        return False
    if not (c["start_date"] <= key <= c["end_date"]):
        return False
    weekday = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][d.weekday()]
    return c.get(weekday) == "1"


def main():
    print("Downloading FlixBus GTFS...")
    req = urllib.request.Request(GTFS_URL, headers={"User-Agent": "BorderForce/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        blob = r.read()
    print(f"Downloaded {len(blob)/1024/1024:.1f} MB")

    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        stops = {r["stop_id"]: r for r in read_csv(zf, "stops.txt")}
        routes = {r["route_id"]: r for r in read_csv(zf, "routes.txt")}
        trips = {r["trip_id"]: r for r in read_csv(zf, "trips.txt")}
        calendars = {r["service_id"]: r for r in read_csv(zf, "calendar.txt")}
        exceptions = {}
        if "calendar_dates.txt" in zf.namelist():
            for r in read_csv(zf, "calendar_dates.txt"):
                exceptions[(r["service_id"], r["date"])] = r["exception_type"]

        nice_stop_ids = {sid for sid, s in stops.items() if NICE_RE.search(s.get("stop_name", ""))}

        candidate_trip_ids = set()
        for r in read_csv(zf, "stop_times.txt"):
            if r.get("stop_id") in nice_stop_ids:
                candidate_trip_ids.add(r["trip_id"])

        rows_by_trip = defaultdict(list)
        for r in read_csv(zf, "stop_times.txt"):
            if r["trip_id"] in candidate_trip_ids:
                rows_by_trip[r["trip_id"]].append(r)
        for rows in rows_by_trip.values():
            rows.sort(key=lambda x: int(x.get("stop_sequence") or 0))

        relevant_shape_ids = {
            trips[tid].get("shape_id", "")
            for tid in candidate_trip_ids
            if tid in trips and trips[tid].get("shape_id")
        }
        shapes = defaultdict(list)
        if "shapes.txt" in zf.namelist():
            for r in read_csv(zf, "shapes.txt"):
                sid = r.get("shape_id", "")
                if sid in relevant_shape_ids:
                    shapes[sid].append((int(r.get("shape_pt_sequence") or 0), float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))
        shape_polys = {sid: [(lat, lon) for _, lat, lon in sorted(pts)] for sid, pts in shapes.items()}

    today = date.today()
    dates = [today + timedelta(days=i) for i in range(DAYS)]
    out = []

    for trip_id, rows in rows_by_trip.items():
        trip = trips.get(trip_id)
        if not trip or len(rows) < 2:
            continue
        nice_idx = next((i for i, r in enumerate(rows) if r["stop_id"] in nice_stop_ids), None)
        if nice_idx is None or nice_idx <= 0:
            continue

        it_idx = None
        for i in range(nice_idx - 1, -1, -1):
            name = stops.get(rows[i]["stop_id"], {}).get("stop_name", "")
            if ITALY_RE.search(name):
                it_idx = i
                break
        if it_idx is None:
            continue

        r0, rn = rows[it_idx], rows[nice_idx]
        s0, sn = stops.get(r0["stop_id"], {}), stops.get(rn["stop_id"], {})
        t0 = gtfs_seconds(r0.get("departure_time") or r0.get("arrival_time") or "")
        t1 = gtfs_seconds(rn.get("arrival_time") or rn.get("departure_time") or "")
        if t0 is None or t1 is None or t1 <= t0:
            continue

        p0 = (float(s0["stop_lat"]), float(s0["stop_lon"]))
        pn = (float(sn["stop_lat"]), float(sn["stop_lon"]))
        poly = shape_polys.get(trip.get("shape_id", ""), [])

        ratio = None
        if len(poly) >= 2:
            d0 = project_distance(poly, p0)
            dt = project_distance(poly, TOLL)
            dn = project_distance(poly, pn)
            if None not in (d0, dt, dn) and dn > d0 and d0 < dt < dn:
                ratio = (dt - d0) / (dn - d0)

        if ratio is None:
            denom = hav_km(p0, pn)
            if denom <= 0:
                continue
            ratio = max(0.05, min(0.98, hav_km(p0, TOLL) / denom))

        eta_sec = round(t0 + (t1 - t0) * ratio)
        service_id = trip.get("service_id", "")
        route = routes.get(trip.get("route_id", ""), {})
        origin = stops.get(rows[0]["stop_id"], {}).get("stop_name", "")
        destination = stops.get(rows[-1]["stop_id"], {}).get("stop_name", "")
        line = route.get("route_short_name") or route.get("route_long_name") or trip.get("route_id", "")

        for d in dates:
            if not service_active(service_id, d, calendars, exceptions):
                continue
            dt = datetime(d.year, d.month, d.day, tzinfo=TZ) + timedelta(seconds=eta_sec)
            out.append({
                "id": f"flix:{trip_id}:{d.isoformat()}",
                "company": "FlixBus",
                "tripId": trip_id,
                "journeyRef": trip_id,
                "line": line,
                "origin": origin,
                "destination": destination,
                "lastItalianStop": s0.get("stop_name", ""),
                "nextFrenchStop": sn.get("stop_name", ""),
                "etaTurbieIso": dt.isoformat(),
                "etaTurbieDate": dt.strftime("%Y-%m-%d"),
                "etaTurbieTime": dt.strftime("%H:%M"),
                "etaTurbieDisplay": dt.strftime("%Hh%M"),
                "quality": "ESTIME_GTFS_SHAPE",
                "qualityLabel": "ESTIMÉ GTFS",
                "interpolationRatio": round(ratio, 4),
                "sourceUpdatedAt": datetime.now(TZ).isoformat(),
                "cancelled": False,
            })

    out.sort(key=lambda b: (b["etaTurbieDate"], b["etaTurbieTime"], b["line"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generatedAt": datetime.now(TZ).isoformat(), "buses": out}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} with {len(out)} bus passages")


if __name__ == "__main__":
    main()
