import os
import sqlite3
import json
from datetime import datetime
from typing import List, Optional

import requests
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from sklearn.cluster import KMeans

app = FastAPI(title="Roamly Itinerary API", version="2.1.0")

DB_NAME = "roamly.db"
# 👇 PASTE YOUR API KEY INSIDE THE QUOTES BELOW 👇
OPENTRIPMAP_API_KEY = "cb1_5b2n_1_ca5cd0fb2b674f01002479f2"

CITY_COORDS_FALLBACK = {
    "paris": (48.8566, 2.3522, "Paris, France"),
    "tokyo": (35.6762, 139.6503, "Tokyo, Japan"),
    "rome": (41.9028, 12.4964, "Rome, Italy"),
    "new york": (40.7128, -74.0060, "New York, USA"),
    "bali": (-8.5069, 115.2625, "Bali, Indonesia"),
    "london": (51.5074, -0.1278, "London, UK"),
    "dubai": (25.2048, 55.2708, "Dubai, UAE"),
}


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itineraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            days INTEGER NOT NULL,
            interests TEXT NOT NULL,
            pace TEXT NOT NULL,
            created_at TEXT NOT NULL,
            itinerary_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


class ItineraryRequest(BaseModel):
    destination: str
    days: int
    interests: List[str]
    pace: str = "Moderate"
    api_key: Optional[str] = ""


def geocode_destination(destination: str):
    clean_key = destination.split(",")[0].strip().lower()
    try:
        geolocator = Nominatim(user_agent="roamly_minimal_v2")
        location = geolocator.geocode(destination, timeout=8)
        if location:
            return location.latitude, location.longitude, location.address
    except Exception:
        pass

    if clean_key in CITY_COORDS_FALLBACK:
        return CITY_COORDS_FALLBACK[clean_key]
    raise ValueError(f"Could not locate destination: {destination}")


def fetch_places_opentripmap(lat: float, lon: float, interests: List[str], api_key: str) -> List[dict]:
    if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE":
        return []
    kind_map = {
        "Culture & History": "historic,cultural,museums",
        "Nature & Parks": "natural,gardens_and_parks",
        "Food & Cafes": "foods,cafes,restaurants",
        "Architecture": "architecture,monuments_and_memorials",
        "Entertainment & Shopping": "amusements,shops"
    }
    kinds = ",".join([kind_map.get(i, "interesting_places") for i in interests]) or "interesting_places"
    url = "https://api.opentripmap.com/0.1/en/places/radius"
    params = {
        "radius": 10000,
        "lon": lon,
        "lat": lat,
        "kinds": kinds,
        "format": "json",
        "limit": 60,
        "apikey": api_key
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        places = []
        for item in resp.json():
            name = item.get("name", "").strip()
            if name:
                places.append({
                    "name": name,
                    "lat": float(item["point"]["lat"]),
                    "lon": float(item["point"]["lon"]),
                    "category": item.get("kinds", "attraction").split(",")[0].replace("_", " ").title(),
                    "rating": round(min(5.0, max(3.8, float(item.get("rate", 4)) / 1.5 + 2.5)), 1)
                })
        return places
    except Exception:
        return []


def fetch_wikipedia_landmarks(lat: float, lon: float, interests: List[str]) -> List[dict]:
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": 10000,
        "gslimit": 50,
        "format": "json"
    }
    headers = {"User-Agent": "RoamlyMinimalApp/2.1"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code != 200:
            return []
        items = resp.json().get("query", {}).get("geosearch", [])
        places = []
        cats = interests if interests else ["Landmark"]
        for idx, item in enumerate(items):
            title = item.get("title", "")
            if any(s in title.lower() for s in ["station", "railway", "line", "arrondissement"]):
                continue
            places.append({
                "name": title,
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "category": cats[idx % len(cats)],
                "rating": round(4.3 + (hash(title) % 7) * 0.1, 1)
            })
        return places
    except Exception:
        return []


def order_route_by_distance(day_df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    if day_df.empty:
        return day_df, 0.0
    records = day_df.to_dict("records")
    ordered = [records.pop(0)]
    total_km = 0.0
    while records:
        last = ordered[-1]
        last_coord = (last["lat"], last["lon"])
        nearest_idx = min(
            range(len(records)),
            key=lambda i: geodesic(last_coord, (records[i]["lat"], records[i]["lon"])).km
        )
        nxt = records.pop(nearest_idx)
        dist = geodesic(last_coord, (nxt["lat"], nxt["lon"])).km
        nxt["distance_from_prev_km"] = round(dist, 2)
        total_km += dist
        ordered.append(nxt)
    ordered[0]["distance_from_prev_km"] = 0.0
    return pd.DataFrame(ordered), round(total_km, 2)


@app.post("/generate-itinerary")
def generate_itinerary(req: ItineraryRequest):
    try:
        center_lat, center_lon, full_address = geocode_destination(req.destination)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    active_key = (req.api_key or OPENTRIPMAP_API_KEY).strip()
    raw_places = fetch_places_opentripmap(center_lat, center_lon, req.interests, active_key)

    if len(raw_places) < req.days * 4:
        raw_places.extend(fetch_wikipedia_landmarks(center_lat, center_lon, req.interests))

    if not raw_places:
        raise HTTPException(status_code=404, detail="No attractions found for this city.")

    df = pd.DataFrame(raw_places)
    df["name_clean"] = df["name"].str.lower().str.strip()
    df = df.drop_duplicates(subset=["name_clean"]).drop(columns=["name_clean"])
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    df["dist_from_center_km"] = df.apply(
        lambda r: round(geodesic((center_lat, center_lon), (r["lat"], r["lon"])).km, 2),
        axis=1
    )
    df = df.sort_values(by=["rating", "dist_from_center_km"], ascending=[False, True]).reset_index(drop=True)

    places_per_day = {"Relaxed": 3, "Moderate": 4, "Packed": 6}.get(req.pace, 4)
    target_count = min(len(df), req.days * places_per_day)
    df = df.head(max(target_count, req.days)).copy()

    n_clusters = min(req.days, len(df))
    coords = df[["lat", "lon"]].to_numpy()
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["day_cluster"] = kmeans.fit_predict(coords)

    time_slots = ["09:30 AM", "11:30 AM", "02:00 PM", "04:15 PM", "06:30 PM", "08:30 PM"]
    days_output = []

    for cluster_id in range(n_clusters):
        day_slice = df[df["day_cluster"] == cluster_id].copy()
        ordered_df, total_day_km = order_route_by_distance(day_slice)
        stops = []
        for idx, (_, row) in enumerate(ordered_df.iterrows()):
            stops.append({
                "slot": time_slots[idx % len(time_slots)],
                "name": row["name"],
                "category": row["category"],
                "rating": row["rating"],
                "lat": row["lat"],
                "lon": row["lon"],
                "distance_from_prev_km": row["distance_from_prev_km"]
            })
        days_output.append({
            "day": cluster_id + 1,
            "total_distance_km": total_day_km,
            "stops": stops
        })

    result_payload = {
        "destination": req.destination.title(),
        "resolved_address": full_address,
        "center": {"lat": center_lat, "lon": center_lon},
        "days": req.days,
        "pace": req.pace,
        "interests": req.interests,
        "itinerary": days_output
    }

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO itineraries (destination, days, interests, pace, created_at, itinerary_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            req.destination.title(),
            req.days,
            ", ".join(req.interests),
            req.pace,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            json.dumps(result_payload)
        )
    )
    conn.commit()
    conn.close()

    return result_payload