#!/usr/bin/env python3
"""
Fetch Spotify links from festival artist pages or Spotify API.
Updates CSV with correct Spotify links from the official festival website or by searching Spotify.
"""

import sys
import os
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
from typing import Optional
import urllib.request
import urllib.parse
import json
import base64

from festival_helpers import FestivalScraper, get_festival_config


def get_spotify_token() -> Optional[str]:
    """
    Get Spotify API access token using client credentials flow.
    Requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.
    
    Returns:
        Access token or None if credentials not available
    """
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return None
    
    # Create authorization header
    auth_str = f"{client_id}:{client_secret}"
    auth_bytes = auth_str.encode('ascii')
    auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
    
    # Request access token
    url = "https://accounts.spotify.com/api/token"
    data = urllib.parse.urlencode({'grant_type': 'client_credentials'}).encode('ascii')
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('access_token')
    except Exception as e:
        print(f"  ⚠️  Error getting Spotify token: {e}")
        return None


def search_spotify_artist(artist_name: str, token: str) -> Optional[str]:
    """
    Search for an artist on Spotify and return their profile URL.
    
    Args:
        artist_name: Name of the artist to search
        token: Spotify API access token
        
    Returns:
        Spotify artist URL or None if not found
    """
    # Clean up artist name for search
    search_query = artist_name.strip()
    
    # URL encode the query
    encoded_query = urllib.parse.quote(f'artist:{search_query}')
    url = f"https://api.spotify.com/v1/search?q={encoded_query}&type=artist&limit=1"
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            artists = result.get('artists', {}).get('items', [])
            
            if artists:
                artist = artists[0]
                artist_id = artist.get('id')
                if artist_id:
                    return f"https://open.spotify.com/artist/{artist_id}"
    except Exception as e:
        print(f"  ⚠️  Error searching Spotify for {artist_name}: {e}")
    
    return None


def update_spotify_links(csv_path: Path, festival: str = 'down-the-rabbit-hole', year: int = None, use_spotify_api: bool = False):
    """
    Update Spotify links in CSV from festival website or Spotify API.
    
    Args:
        csv_path: Path to CSV file
        festival: Festival identifier
        year: Festival year
        use_spotify_api: If True, use Spotify API instead of scraping festival pages
    """
    # Get festival configuration
    if year is None:
        year = int(csv_path.stem)  # Get year from filename
    
    config = get_festival_config(festival, year)
    scraper = FestivalScraper(config)
    
    # Get Spotify token if using API
    spotify_token = None
    if use_spotify_api or festival == 'footprints':
        spotify_token = get_spotify_token()
        if not spotify_token:
            print("⚠️  Spotify API credentials not found. Please set:")
            print("   $env:SPOTIFY_CLIENT_ID = 'your-client-id'")
            print("   $env:SPOTIFY_CLIENT_SECRET = 'your-client-secret'")
            print("   Get credentials from: https://developer.spotify.com/dashboard")
            if use_spotify_api:
                return
            print("   Falling back to festival page scraping...\n")
    
    # Load CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = [h for h in reader.fieldnames if h is not None]  # Filter out None headers
        rows = []
        for row in reader:
            # Remove None key if it exists (from trailing commas)
            if None in row:
                del row[None]
            rows.append(row)
    
    source = "Spotify API" if (use_spotify_api or (festival == 'footprints' and spotify_token)) else f"{config.name} website"
    print(f"\n=== Updating Spotify Links from {source} ({year}) ===\n")
    print(f"Processing {len(rows)} artists...\n")
    
    updated_count = 0
    added_count = 0
    skipped_count = 0
    
    for row in rows:
        artist_name = row.get('Artist', '').strip()
        current_link = row.get('Spotify', '').strip()
        festival_url = row.get('Festival URL', '').strip()
        
        if not artist_name:
            continue
        
        print(f"Fetching: {artist_name}...")
        new_link = None
        
        # Decide which method to use
        if use_spotify_api or (festival == 'footprints' and spotify_token):
            # Use Spotify API
            new_link = search_spotify_artist(artist_name, spotify_token)
        else:
            # Scrape from festival page using the Festival URL from CSV if available
            if festival_url:
                # Fetch directly from the Festival URL in CSV
                html = scraper.fetch_page(festival_url)
                if html:
                    new_link = scraper.extract_spotify_link(html)
            else:
                # Fall back to constructing URL from artist name
                new_link = scraper.fetch_spotify_link(artist_name)
            
            # If scraping failed and we have Spotify token, try API as fallback
            if not new_link and spotify_token:
                print(f"  ℹ️  Trying Spotify API as fallback...")
                new_link = search_spotify_artist(artist_name, spotify_token)
        
        if new_link:
            if current_link and current_link != new_link:
                print(f"  ✓ Updated: {artist_name}")
                print(f"    Old: {current_link}")
                print(f"    New: {new_link}")
                updated_count += 1
            elif not current_link:
                print(f"  ✓ Added: {artist_name}")
                added_count += 1
            else:
                print(f"  ✓ Verified: {artist_name}")
            
            row['Spotify'] = new_link
        else:
            print(f"  ⚠️  Not found: {artist_name}")
            skipped_count += 1
        
        # Be nice to the servers
        scraper.rate_limit_delay(0.5)
    
    # Save updated CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Complete!")
    print(f"  - {added_count} link(s) added")
    print(f"  - {updated_count} link(s) updated")
    if skipped_count > 0:
        print(f"  - {skipped_count} artist(s) not found")
    print(f"  - CSV updated: {csv_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch Spotify links from festival pages"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Festival year (default: 2026)"
    )
    parser.add_argument(
        "--festival",
        type=str,
        default="down-the-rabbit-hole",
        help="Festival identifier (default: down-the-rabbit-hole)"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Use Spotify API instead of scraping festival pages (requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)"
    )
    
    args = parser.parse_args()
    
    # Use the docs/{festival}/{year}/{year}.csv file
    csv_path = Path(__file__).parent.parent / "docs" / args.festival / str(args.year) / f"{args.year}.csv"
    
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        sys.exit(1)
    
    update_spotify_links(csv_path, festival=args.festival, year=args.year, use_spotify_api=args.api)


if __name__ == "__main__":
    main()
