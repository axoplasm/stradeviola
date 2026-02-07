import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from stravalib import Client

load_dotenv()

CLIENT_ID = int(os.environ["STRAVA_CLIENT_ID"])
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8000/callback"
TOKEN_FILE = Path(__file__).parent / ".tokens.json"


def save_tokens(token_data: dict) -> None:
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))


def load_tokens() -> dict | None:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def authorize_via_browser(client: Client) -> dict:
    auth_url = client.authorization_url(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=["read", "activity:read_all"],
    )

    print(f"Open this URL in a browser and authorize:\n\n{auth_url}\n")
    print("After authorizing, paste the full redirect URL here:")
    redirect_url = input("> ").strip()

    query = parse_qs(urlparse(redirect_url).query)
    if "code" not in query:
        raise SystemExit("No authorization code found in URL.")

    access_info = client.exchange_code_for_token(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        code=query["code"][0],
    )
    return dict(access_info)


def get_authenticated_client() -> Client:
    client = Client()
    tokens = load_tokens()

    if tokens and tokens["expires_at"] > time.time():
        print("Using saved token.")
        client.access_token = tokens["access_token"]
        client.refresh_token = tokens["refresh_token"]
        client.token_expires = tokens["expires_at"]
        return client

    if tokens and tokens.get("refresh_token"):
        print("Token expired, refreshing...")
        fresh = client.refresh_access_token(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            refresh_token=tokens["refresh_token"],
        )
        tokens = dict(fresh)
        save_tokens(tokens)
        client.access_token = tokens["access_token"]
        client.refresh_token = tokens["refresh_token"]
        client.token_expires = tokens["expires_at"]
        return client

    print("No saved token found, starting OAuth flow...")
    tokens = authorize_via_browser(client)
    save_tokens(tokens)
    client.access_token = tokens["access_token"]
    client.refresh_token = tokens["refresh_token"]
    client.token_expires = tokens["expires_at"]
    return client
