'''Library of helper functions for authentication to Strava API.'''
import json
import os
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
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
    """Writes token data (access_token, refresh_token, expires_at) to .tokens.json."""
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))


def load_tokens() -> dict | None:
    """Loads saved tokens from .tokens.json, or return None if the file doesn't exist."""
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def authorize_via_browser(client: Client) -> dict:
    """Runs the Strava OAuth flow interactively.

    Opens the authorization URL in a browser and starts a local HTTP server
    on port 8000 to receive the callback. Exchanges the authorization code
    for access and refresh tokens, saves them, and returns the token dict.
    """
    auth_url = client.authorization_url(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=["read", "activity:read_all"],
    )

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            if "code" in query:
                self.server.auth_code = query["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    b"Authorization successful. You can close this tab."
                )
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed: no code received.")

        def log_message(self, format, *args):
            pass

    print(f"Opening browser for Strava authorization...\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8000), CallbackHandler)
    server.auth_code = None
    server.handle_request()

    if not server.auth_code:
        raise SystemExit("No authorization code received.")

    access_info = client.exchange_code_for_token(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        code=server.auth_code,
    )
    return dict(access_info)


def get_authenticated_client() -> Client:
    """Returns a stravalib Client with a valid access token.

    Tries, in order: reuse a non-expired saved token, refresh an expired
    token, or run the full OAuth browser flow. Saves fresh tokens to disk.
    """
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
