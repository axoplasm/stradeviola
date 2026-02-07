#!/usr/bin/env python3
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from auth import get_authenticated_client

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide"}
DATA_FILE = Path(__file__).parent / "public" / "data.json"


def aggregate(activities):
    data = defaultdict(lambda: {"count": 0, "time": 0, "distance": 0.0, "elevation": 0.0})
    for a in activities:
        if a.type and a.type.root in RIDE_TYPES:
            year = str(a.start_date_local.year)
            y = data[year]
            y["count"] += 1
            y["time"] += int(a.moving_time) if a.moving_time else 0
            y["distance"] += float(a.distance) / 1000 if a.distance else 0
            y["elevation"] += float(a.total_elevation_gain) if a.total_elevation_gain else 0
    return dict(data)


def update_data():
    client = get_authenticated_client()
    current_year = str(datetime.now().year)

    if DATA_FILE.exists():
        saved = json.loads(DATA_FILE.read_text())
        print(f"Fetching {current_year} activities...", flush=True)
        fresh = aggregate(client.get_activities(after=datetime(int(current_year), 1, 1)))
        current = fresh.get(current_year, {"count": 0, "time": 0, "distance": 0.0, "elevation": 0.0})
        if saved.get(current_year) != current:
            saved[current_year] = current
            with open(DATA_FILE, "w") as f:
                json.dump(saved, f, indent=2)
            print(f"Updated {current_year} in {DATA_FILE}")
        else:
            print("Data is up to date.")
    else:
        print("Fetching all activities...", flush=True)
        saved = aggregate(client.get_activities())
        with open(DATA_FILE, "w") as f:
            json.dump(dict(sorted(saved.items())), f, indent=2)
        print(f"Saved data to {DATA_FILE}")


if __name__ == "__main__":
    update_data()
