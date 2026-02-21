"""Flask app serving the Strade Viola dashboard with per-user Strava OAuth."""
import json
import os
import time
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from dotenv import load_dotenv
from flask import Flask, redirect, request, send_from_directory, session, jsonify
from stravalib import Client

from build_site import aggregate

load_dotenv()

app = Flask(__name__, static_folder=None)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

CLIENT_ID = int(os.environ["STRAVA_CLIENT_ID"])
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPES = "read,activity:read_all"


def refresh_tokens(tokens):
    """Refreshes an expired Strava access token and returns the updated token dict."""
    data = urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
    }).encode()
    with urlopen(Request("https://www.strava.com/oauth/token", data=data)) as resp:
        fresh = json.loads(resp.read())
    return {
        "access_token": fresh["access_token"],
        "refresh_token": fresh["refresh_token"],
        "expires_at": fresh["expires_at"],
    }


def get_client():
    """Returns a stravalib Client with a valid access token from the session.

    Automatically refreshes the token if expired. Returns None if no tokens
    are stored in the session.
    """
    tokens = session.get("tokens")
    if not tokens:
        return None
    if tokens["expires_at"] <= time.time():
        tokens = refresh_tokens(tokens)
        session["tokens"] = tokens
    client = Client()
    client.access_token = tokens["access_token"]
    client.refresh_token = tokens["refresh_token"]
    client.token_expires = tokens["expires_at"]
    return client


PUBLIC = os.path.join(os.path.dirname(__file__), "public")


@app.route("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.route("/auth/strava")
def auth_strava():
    params = urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
    })
    return redirect(f"https://www.strava.com/oauth/authorize?{params}")


@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return f"Strava denied access: {error}", 403
    code = request.args.get("code")
    if not code:
        return "Authorization failed: no code received.", 400
    try:
        client = Client()
        tokens = client.exchange_code_for_token(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            code=code,
        )
        session["tokens"] = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_at": tokens["expires_at"],
        }
    except Exception as e:
        return f"Token exchange failed: {e}", 500
    return redirect("/")


@app.route("/api/status")
def api_status():
    return jsonify({"authenticated": "tokens" in session})


@app.route("/api/data")
def api_data():
    client = get_client()
    if not client:
        return jsonify({"error": "Not authenticated"}), 401
    athlete = client.get_athlete()
    athlete_info = {
        "name": f"{athlete.firstname} {athlete.lastname}",
        "id": athlete.id,
    }
    years = aggregate(client.get_activities())
    return jsonify({"athlete": athlete_info, "years": dict(sorted(years.items()))})


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(PUBLIC, filename)
