#!/usr/bin/env python3
from collections import defaultdict

from auth import get_authenticated_client

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide"}

client = get_authenticated_client()

years = defaultdict(lambda: {"count": 0, "time": 0, "distance": 0.0, "elevation": 0.0})

print("Fetching all activities...", flush=True)
for a in client.get_activities():
    if a.type and a.type.root in RIDE_TYPES:
        year = a.start_date_local.year
        y = years[year]
        y["count"] += 1
        y["time"] += int(a.elapsed_time) if a.elapsed_time else 0
        y["distance"] += float(a.distance) / 1000 if a.distance else 0
        y["elevation"] += float(a.total_elevation_gain) if a.total_elevation_gain else 0

header = f"{'Year':>6}  {'Rides':>7}  {'Time':>12}  {'Distance':>12}  {'Elevation':>12}"
print(header)
print("-" * len(header))

for year in sorted(years):
    y = years[year]
    h, rem = divmod(y["time"], 3600)
    m, s = divmod(rem, 60)
    print(
        f"{year:>6}  {y['count']:>7}  {h:>4}:{m:02d}:{s:02d}   {y['distance']:>9.1f} km  {y['elevation']:>9.0f} m"
    )
