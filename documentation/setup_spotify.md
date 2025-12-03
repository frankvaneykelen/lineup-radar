# Footprints Festival Scraper - Setup Guide

The Footprints Festival scraper extracts artist lineups from two sources:

1. **Venue page HTML** (manually downloaded when blocked)
2. **Spotify playlist** (requires API credentials)

## Step 1: Handle 403 Blocked Pages

If the scraper encounters a **403 Forbidden** error when accessing the venue page:

1. **Open the festival URL** in your browser:
   - Example: `https://www.tivolivredenburg.nl/agenda/50573414/footprints-festival-21-02-2026`

2. **Save the page**:
   - Right-click anywhere on the page
   - Select **"Save As..."** (or press `Ctrl+S` / `Cmd+S`)
   - Save as: `Footprints Festival – TivoliVredenburg.html`
   - Place it in the project's root directory (same folder as `scrape_footprints.py`)

3. **Run the scraper again**:
   - The scraper will automatically detect and use the downloaded file
   - Artist names will be extracted from the accordion sections

> **Note**: This workaround is needed when websites block automated scraping. The scraper will prompt you with these instructions whenever it encounters a 403 error.

## Step 2: Get Spotify API Credentials

1. **Get Spotify API Credentials**:
   - Go to <https://developer.spotify.com/dashboard>
   - Log in with your Spotify account
   - Click "Create App"
   - Fill in:
     - App name: "LineupRadar"
     - App description: "Festival lineup extraction"
     - Redirect URI: `http://localhost:8888/callback`
   - Accept terms and create
   - Copy your **Client ID** and **Client Secret**

2. **Set Environment Variables**:

   **Windows PowerShell:**

   ```powershell
   $env:SPOTIPY_CLIENT_ID = "your_client_id_here"
   $env:SPOTIPY_CLIENT_SECRET = "your_client_secret_here"
   ```

   **Windows Command Prompt:**

   ```cmd
   set SPOTIPY_CLIENT_ID=your_client_id_here
   set SPOTIPY_CLIENT_SECRET=your_client_secret_here
   ```

   **Linux/Mac:**

   ```bash
   export SPOTIPY_CLIENT_ID="your_client_id_here"
   export SPOTIPY_CLIENT_SECRET="your_client_secret_here"
   ```

3. **Run the scraper again**:

   ```bash
   python scrape_footprints.py --year 2026
   ```

## Alternative: Manual Addition

If you prefer not to set up Spotify API, you can manually add artists to the config:

Edit `festival_helpers/config.py` and add more artists to the `manual_artists` list:

```python
'manual_artists': [
    'Gizmo Varillas',
    'Islandman',
    'Sessa',
    'Keshavara',
    'Derya Yıldırım & Grup Şimşek',
    # Add more artists from the Spotify playlist here
],
```

Then run `python scrape_footprints.py --year 2026` again.
