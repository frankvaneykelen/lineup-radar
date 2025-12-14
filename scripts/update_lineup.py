#!/usr/bin/env python3
"""
Update script for Down The Rabbit Hole Festival Program

Fetches current lineup from the website and updates CSV with new artists
while preserving user edits to "AI Summary" and "AI Rating" fields.
"""

import sys
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
import sys
sys.path.insert(0, str(Path(__file__).parent))

import re
from festival_tracker import FestivalTracker
from helpers import FestivalScraper, get_festival_config
from typing import List, Dict


def fetch_artists_from_website(festival: str = 'down-the-rabbit-hole', year: int = 2026) -> List[str]:
    """Fetch artist list from festival website."""
    config = get_festival_config(festival, year)
    scraper = FestivalScraper(config)
    
    try:
        artist_names = scraper.fetch_lineup_artists()
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
        "AI Summary": "",
        "AI Rating": "",
        "Spotify link": "",
        "Number of People in Act": "",
        "Gender of Front Person": "",
        "Front Person of Color?": ""
    }


def main():
    """Main update process."""
    year = 2026
    festival = 'down-the-rabbit-hole'
    
    print(f"\n=== Down The Rabbit Hole {year} - Update Script ===\n")
    
    # Initialize tracker
    tracker = FestivalTracker(year)
    
    # Step 1: Track current user edits
    print("Step 1: Tracking user edits...")
    tracker.track_user_edits()
    
    # Step 2: Fetch current lineup from website
    print("\nStep 2: Fetching lineup from website...")
    website_artists = fetch_artists_from_website(festival, year)
    
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
