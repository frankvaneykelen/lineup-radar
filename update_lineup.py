#!/usr/bin/env python3
"""
Update script for Down The Rabbit Hole Festival Program

Fetches current lineup from the website and updates CSV with new artists
while preserving user edits to "My take" and "My rating" fields.
"""

import re
import sys
from festival_tracker import FestivalTracker
import urllib.request
from typing import List, Dict


def fetch_artists_from_website() -> List[str]:
    """Fetch artist list from Down The Rabbit Hole website."""
    url = "https://downtherabbithole.nl/programma"
    
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
        
        # Extract artist URLs using regex
        pattern = r'programma/([a-z0-9-]+)'
        matches = re.findall(pattern, html)
        
        # Convert URL slugs to artist names
        artist_names = []
        for slug in sorted(set(matches)):
            # Convert slug to proper name
            name = slug.replace('-', ' ').title()
            
            # Handle special cases
            name_map = {
                'Florence The Machine': 'Florence + The Machine',
                'The Xx': 'The xx',
                'De Staat Becomes De Staat': 'De Staat Becomes De Staat',
                'Yenouukeur Yenuk1matu': '¥ØU$UK€ ¥UK1MAT$U',
                'Derya Yildirim Grup Simsek': 'Derya Yıldırım & Grup Şimşek',
                'Arp Frique The Perpetual Singers': 'Arp Frique & The Perpetual Singers',
                'Mall Grab B2B Narciss': 'Mall Grab b2b Narciss',
                'Kingongolo Kiniata': "Kin'Gongolo Kiniata",
                'Lumi': 'Lumï'
            }
            
            name = name_map.get(name, name)
            artist_names.append(name)
        
        print(f"✓ Found {len(artist_names)} artists on website")
        return artist_names
        
    except Exception as e:
        print(f"✗ Error fetching website: {e}")
        sys.exit(1)


def create_artist_dict(name: str) -> Dict:
    """Create a minimal artist dictionary for a new artist."""
    return {
        "Artist": name,
        "Genre": "",
        "Country": "",
        "Bio": "",
        "My take": "",
        "My rating": "",
        "Spotify link": "",
        "Number of People in Act": "",
        "Gender of Front Person": "",
        "Front Person of Color?": ""
    }


def main():
    """Main update process."""
    year = 2026
    
    print(f"\n=== Down The Rabbit Hole {year} - Update Script ===\n")
    
    # Initialize tracker
    tracker = FestivalTracker(year)
    
    # Step 1: Track current user edits
    print("Step 1: Tracking user edits...")
    tracker.track_user_edits()
    
    # Step 2: Fetch current lineup from website
    print("\nStep 2: Fetching lineup from website...")
    website_artists = fetch_artists_from_website()
    
    # Step 3: Load existing CSV
    print("\nStep 3: Checking for new artists...")
    headers, existing_rows = tracker._load_csv()
    existing_artist_names = {row.get("Artist", "") for row in existing_rows}
    
    # Step 4: Find new artists
    new_artists = []
    for artist_name in website_artists:
        if artist_name not in existing_artist_names:
            new_artists.append(create_artist_dict(artist_name))
    
    if new_artists:
        print(f"\n✓ Found {len(new_artists)} new artist(s):")
        for artist in new_artists:
            print(f"  - {artist['Artist']}")
        
        # Step 5: Update CSV
        print("\nStep 4: Adding new artists to CSV...")
        tracker.update_with_new_artists(new_artists)
        print(f"\n✓ Update complete!")
        print("\n💡 Next step: Run 'python enrich_artists.py' to fill in artist details")
        print("   Or use AI enrichment: 'python enrich_artists.py --ai' (requires setup)")
    else:
        print("\n✓ No new artists found. CSV is up to date!")
    
    print(f"\nTotal artists in {year}.csv: {len(existing_rows) + len(new_artists)}")


if __name__ == "__main__":
    main()
