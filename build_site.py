#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

from auth import get_authenticated_client

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide"}
DATA_FILE = Path(__file__).parent / "public" / "data.json"

# Load existing data
if DATA_FILE.exists():
    saved = json.loads(DATA_FILE.read_text())
else:
    saved = {}

# Fetch only current year
current_year = datetime.now().year
after = datetime(current_year, 1, 1)

client = get_authenticated_client()

print(f"Fetching {current_year} activities...", flush=True)
year_data = {"count": 0, "time": 0, "distance": 0.0, "elevation": 0.0}
for a in client.get_activities(after=after):
    if a.type and a.type.root in RIDE_TYPES:
        year_data["count"] += 1
        year_data["time"] += int(a.moving_time) if a.moving_time else 0
        year_data["distance"] += float(a.distance) / 1000 if a.distance else 0
        year_data["elevation"] += float(a.total_elevation_gain) if a.total_elevation_gain else 0

saved[str(current_year)] = year_data
DATA_FILE.write_text(json.dumps(saved, indent=2))
print(f"Saved data to {DATA_FILE}")
