#!/usr/bin/env python3
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from auth import get_authenticated_client

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide"}
DATA_FILE = Path(__file__).parent / "data.json"
OUTPUT_FILE = Path(__file__).parent / "index.html"

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

# Build HTML
rows = ""
for year in sorted(saved, key=int):
    y = saved[year]
    h, rem = divmod(y["time"], 3600)
    m, s = divmod(rem, 60)
    rows += f"""      <tr>
        <td>{year}</td>
        <td>{y['count']}</td>
        <td>{h}:{m:02d}:{s:02d}</td>
        <td>{y['distance']:.1f}</td>
        <td>{y['elevation']:.0f}</td>
      </tr>
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Yearly Cycling Stats</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ padding: 0.5rem 1rem; text-align: right; border-bottom: 1px solid #ddd; }}
    th {{ border-bottom: 2px solid #333; }}
    th:first-child, td:first-child {{ text-align: left; }}
  </style>
</head>
<body>
  <h1>Yearly Cycling Stats</h1>
  <table>
    <thead>
      <tr>
        <th>Year</th>
        <th>Rides</th>
        <th>Time</th>
        <th>Distance (km)</th>
        <th>Elevation (m)</th>
      </tr>
    </thead>
    <tbody>
{rows}    </tbody>
  </table>
</body>
</html>"""

OUTPUT_FILE.write_text(html)
print(f"Wrote {OUTPUT_FILE}")
