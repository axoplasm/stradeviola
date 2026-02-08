#!/usr/bin/env python3
'''
Test script that authenticates to Strava API and returns the 10 most recent 
cycling activities.
'''
from auth import get_authenticated_client

client = get_authenticated_client()
athlete = client.get_athlete()
print(f"Authenticated as {athlete.firstname} {athlete.lastname}\n")

activities = client.get_activities(limit=10)
for a in activities:
    distance_km = float(a.distance) / 1000 if a.distance else 0
    elapsed = int(a.elapsed_time) if a.elapsed_time else 0
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
    print(f"  {a.start_date_local:%Y-%m-%d}  {a.type.root:<15} {distance_km:6.1f} km  {time_str:>9}  {a.name}")
