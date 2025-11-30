#!/usr/bin/env python3
"""
Fetch Spotify links from festival artist pages.
Updates CSV with correct Spotify links from the official festival website.
"""

import sys
import csv
from pathlib import Path
from typing import Optional

from festival_helpers import FestivalScraper, get_festival_config


def update_spotify_links(csv_path: Path, festival: str = 'down-the-rabbit-hole', year: int = None):
    """Update Spotify links in CSV from festival website."""
    # Get festival configuration
    if year is None:
        year = int(csv_path.stem)  # Get year from filename
    
    config = get_festival_config(festival, year)
    scraper = FestivalScraper(config)
    
    # Load CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    print(f"\n=== Updating Spotify Links from {config.name} {year} ===\n")
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
        new_link = scraper.fetch_spotify_link(artist_name)
        
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
        scraper.rate_limit_delay(0.5)
    
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
    
    args = parser.parse_args()
    
    # Use the docs/{year}/{year}.csv file
    csv_path = Path(__file__).parent / "docs" / str(args.year) / f"{args.year}.csv"
    
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        sys.exit(1)
    
    update_spotify_links(csv_path, festival=args.festival, year=args.year)


if __name__ == "__main__":
    main()
