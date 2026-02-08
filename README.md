# Strade Viola

A static dashboard showing yearly cycling stats from Strava. Fetches ride data via the Strava API, aggregates it by year, and generates a single-page HTML dashboard with an interactive chart and table in metric and US units.

See an example using [axoplasm’s](https://www.strava.com/athletes/56063) data at [stradeviola.axoplasm.com](https://stradeviola.axoplasm.com).

## Setup

1. Create a [Strava API application](https://www.strava.com/settings/api) and set the redirect URI to `http://localhost:8000/callback`.

2. Create a `.env` file:

   ```
   STRAVA_CLIENT_ID=your_id
   STRAVA_CLIENT_SECRET=your_secret
   ```

3. Install dependencies:

   ```bash
   $ python3 -m venv venv
   $ source venv/bin/activate
   (venv) $ pip install -r requirements.txt
   ```

3. Test the connection to the API by running `main.py`. This will fetch the 10 most recent cycling activities in your Strava profile.
   ```bash
   (venv) $ python main.py
   ```

4. Run the build script. On first run it will open a browser for Strava OAuth, then fetch all activities:

   ```bash
   (venv) $ python build_site.py
   ```

   On subsequent runs it only fetches the current year's activities and updates `public/data.json` if anything changed.

## Serving the site

Serve the `public/` directory with any static file server. For example:

```bash
(venv) python -m http.server -d public
```

## Files

- `auth.py` — Strava OAuth flow and token management (saved to `.tokens.json`)
- `build_site.py` — Fetches ride data, aggregates by year, writes `public/data.json`
- `yearly_stats.py` — CLI script that prints yearly stats to the terminal
- `main.py` — CLI script that prints recent activities
- `public/index.html` — Static dashboard with interactive chart and table
- `public/data.json` — Generated data file (not checked in)
- `.env` — Environment variables (not checked in). See __Setup__, above
- `.tokens.json` — Local copy of auth token (not checked in)
- `public/css/*` — reference css files. Selectors from these files can be copied into the `<style>` tag in `index.html`

## Cron

To keep the data fresh on a server, run `build_site.py` periodically, for example with a cron job that executes every hour:

```
0 * * * * /path/to/stradeviola/venv/bin/python /path/to/stradeviola/build_site.py >> /var/log/stradeviola.log 2>&1
```

The initial OAuth flow must be done interactively. After that, token refresh is automatic.
