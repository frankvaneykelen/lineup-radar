#!/usr/bin/env python3
"""
Fetch Festival Data Script

Scrapes festival website data for artists and stores in CSV:
- Festival bio (Dutch original)
- Festival bio (English translation)
- Festival page URL
- Social media links (JSON)
- Images scraped flag

Run this after update_lineup.py adds new artists and before generating pages.
"""

import csv
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List
from festival_helpers import (
    FestivalScraper,
    get_festival_config,
    artist_name_to_slug,
    translate_text
)


def load_csv(csv_path: Path) -> tuple[List[str], List[Dict]]:
    """Load CSV file and return headers and rows."""
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        sys.exit(1)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)
        rows = list(reader)
    return headers, rows


def save_csv(csv_path: Path, headers: List[str], rows: List[Dict]):
    """Save CSV file with UTF-8 encoding."""
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def needs_festival_data(row: Dict) -> bool:
    """Check if artist needs festival data fetched."""
    # Check if any festival data columns are missing or empty
    festival_fields = [
        'Festival Bio (NL)',
        'Festival Bio (EN)',
        'Festival URL'
    ]
    return any(not row.get(field, '').strip() for field in festival_fields)


def fetch_artist_festival_data(artist_name: str, scraper: FestivalScraper, config) -> Dict[str, str]:
    """
    Fetch festival data for an artist.
    
    Returns:
        Dict with festival bio (NL/EN), URL, and social links
    """
    slug = artist_name_to_slug(artist_name)
    festival_url = config.get_artist_url(slug)
    
    print(f"  → Fetching from {festival_url}")
    
    result = {
        'Festival URL': festival_url,
        'Festival Bio (NL)': '',
        'Festival Bio (EN)': '',
        'Social Links': '',
        'Images Scraped': 'No'
    }
    
    try:
        # Fetch bio
        bio_nl = scraper.fetch_artist_bio(artist_name)
        if bio_nl:
            result['Festival Bio (NL)'] = bio_nl
            print(f"  ✓ Fetched bio ({len(bio_nl)} chars)")
            
            # Translate to English
            print(f"  → Translating bio to English...")
            bio_en = translate_text(bio_nl, "Dutch", "English")
            if bio_en:
                result['Festival Bio (EN)'] = bio_en
                print(f"  ✓ Translated bio ({len(bio_en)} chars)")
        else:
            print(f"  ⚠ No bio found on festival website")
        
        # Fetch social links
        html = scraper.fetch_artist_page(artist_name)
        if html:
            social_links = extract_social_links(html)
            if social_links:
                result['Social Links'] = json.dumps(social_links)
                print(f"  ✓ Found {len(social_links)} social link(s)")
        
        return result
        
    except Exception as e:
        print(f"  ✗ Error fetching data: {e}")
        return result


def extract_social_links(html: str) -> Dict[str, str]:
    """Extract social media links from festival page HTML."""
    import re
    
    social_links = {}
    
    # Look for links in the "Meer weten over" section
    section_pattern = r'<div[^>]*class="[^"]*border p-8 mt-8[^"]*"[^>]*>(.*?)</div>'
    section_match = re.search(section_pattern, html, re.DOTALL | re.IGNORECASE)
    
    if section_match:
        section_content = section_match.group(1)
        link_pattern = r'<a[^>]*target="_blank"[^>]*href="([^"]+)"[^>]*>'
        potential_links = re.findall(link_pattern, section_content)
        
        for link in potential_links:
            link_lower = link.lower()
            
            # Exclude festival/mojo/livenation/newsletter links
            if any(exclude in link_lower for exclude in [
                'dtrh_festival', 'dtrh_fest', 'downtherabbithole',
                'mojo.nl', 'livenation', 'list-manage.com'
            ]):
                continue
            
            # Categorize social media links
            if 'facebook.com' in link_lower:
                social_links['Facebook'] = link
            elif 'instagram.com' in link_lower:
                social_links['Instagram'] = link
            elif 'twitter.com' in link_lower or 'x.com' in link_lower:
                social_links['Twitter'] = link
            elif 'youtube.com' in link_lower or 'youtu.be' in link_lower:
                social_links['YouTube'] = link
            elif 'soundcloud.com' in link_lower:
                social_links['SoundCloud'] = link
            elif 'bandcamp.com' in link_lower:
                social_links['Bandcamp'] = link
            elif 'spotify.com' in link_lower and '/artist/' in link_lower:
                social_links['Spotify'] = link
            else:
                # Generic website link
                social_links['Website'] = link
    
    return social_links


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch festival data for artists from festival website"
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
        "--force",
        action="store_true",
        help="Re-fetch data even if already present"
    )
    
    args = parser.parse_args()
    
    # Get festival config and scraper
    config = get_festival_config(args.festival, args.year)
    scraper = FestivalScraper(config)
    
    # CSV file path
    csv_path = Path(f"{args.year}.csv")
    
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Load CSV
    headers, rows = load_csv(csv_path)
    
    # Add new columns if they don't exist
    new_columns = [
        'Festival URL',
        'Festival Bio (NL)',
        'Festival Bio (EN)',
        'Social Links',
        'Images Scraped'
    ]
    
    for col in new_columns:
        if col not in headers:
            headers.append(col)
            print(f"✓ Added column: {col}")
            # Initialize empty values for existing rows
            for row in rows:
                row[col] = ''
    
    print(f"\n=== Fetching Festival Data for {config.name} {args.year} ===\n")
    print(f"Processing {len(rows)} artists...\n")
    
    updated_count = 0
    skipped_count = 0
    
    for idx, row in enumerate(rows):
        artist_name = row.get('Artist', '').strip()
        if not artist_name:
            continue
        
        print(f"[{idx+1}/{len(rows)}] {artist_name}")
        
        # Check if needs data
        if not args.force and not needs_festival_data(row):
            print(f"  ✓ Already has festival data (use --force to re-fetch)")
            skipped_count += 1
            continue
        
        # Fetch festival data
        festival_data = fetch_artist_festival_data(artist_name, scraper, config)
        
        # Update row
        for key, value in festival_data.items():
            if value:  # Only update if we got data
                row[key] = value
        
        updated_count += 1
        
        # Rate limit
        scraper.rate_limit_delay(1.0)
        print()
    
    # Save updated CSV
    save_csv(csv_path, headers, rows)
    
    print(f"\n✓ Festival data fetching complete!")
    print(f"  Updated: {updated_count} artist(s)")
    print(f"  Skipped: {skipped_count} artist(s)")
    print(f"\nNext steps:")
    print(f"  1. Run: python enrich_artists.py --ai  (if needed)")
    print(f"  2. Run: python generate_html.py --year {args.year}")
    print(f"  3. Run: python generate_artist_pages.py --year {args.year}")


if __name__ == "__main__":
    main()
