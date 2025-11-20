#!/usr/bin/env python3
"""
Fetch Spotify links from Down The Rabbit Hole festival artist pages.
Updates CSV with correct Spotify links from the official festival website.
"""

import re
import sys
import csv
import time
from pathlib import Path
from typing import Dict, Optional
import urllib.request
import urllib.parse


def artist_name_to_slug(name: str) -> str:
    """Convert artist name to URL slug format."""
    # Special mappings for known artists
    special_cases = {
        'Florence + The Machine': 'florence-the-machine',
        'The xx': 'the-xx',
        '¥ØU$UK€ ¥UK1MAT$U': 'yenouukeur-yenuk1matu',
        'Derya Yıldırım & Grup Şimşek': 'derya-yildirim-grup-simsek',
        'Arp Frique & The Perpetual Singers': 'arp-frique-the-perpetual-singers',
        'Mall Grab b2b Narciss': 'mall-grab-b2b-narciss',
        "Kin'Gongolo Kiniata": 'kingongolo-kiniata',
        'Lumï': 'lumi',
        'De Staat Becomes De Staat': 'de-staat-becomes-de-staat'
    }
    
    if name in special_cases:
        return special_cases[name]
    
    # General conversion
    slug = name.lower()
    slug = slug.replace(' ', '-')
    slug = slug.replace('&', '')
    slug = slug.replace('+', '')
    slug = slug.replace("'", '')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def fetch_spotify_link_from_page(artist_name: str) -> Optional[str]:
    """Fetch Spotify link from the festival's artist page."""
    slug = artist_name_to_slug(artist_name)
    url = f"https://downtherabbithole.nl/programma/{slug}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        # Look for Spotify link in the HTML
        spotify_pattern = r'https://open\.spotify\.com/artist/[a-zA-Z0-9]+'
        match = re.search(spotify_pattern, html)
        
        if match:
            return match.group(0)
        else:
            print(f"  ⚠️  {artist_name}: No Spotify link found on page")
            return None
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  ⚠️  {artist_name}: Festival page not found (404)")
        else:
            print(f"  ⚠️  {artist_name}: HTTP error {e.code}")
        return None
    except Exception as e:
        print(f"  ⚠️  {artist_name}: Error - {e}")
        return None


def update_spotify_links(csv_path: Path):
    """Update Spotify links in CSV from festival website."""
    # Load CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    print(f"\n=== Updating Spotify Links from Festival Website ===\n")
    print(f"Processing {len(rows)} artists...\n")
    
    updated_count = 0
    added_count = 0
    
    for row in rows:
        artist_name = row.get('Artist', '').strip()
        current_link = row.get('Spotify link', '').strip()
        
        if not artist_name:
            continue
        
        # Fetch link from festival page
        print(f"Fetching: {artist_name}...")
        new_link = fetch_spotify_link_from_page(artist_name)
        
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
            
            row['Spotify link'] = new_link
        
        # Be nice to the server
        time.sleep(0.5)
    
    # Save updated CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Complete!")
    print(f"  - {added_count} link(s) added")
    print(f"  - {updated_count} link(s) updated")
    print(f"  - CSV updated: {csv_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch Spotify links from Down The Rabbit Hole festival pages"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Festival year (default: 2026)"
    )
    
    args = parser.parse_args()
    csv_path = Path(f"{args.year}.csv")
    
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        sys.exit(1)
    
    update_spotify_links(csv_path)


if __name__ == "__main__":
    main()
