#!/usr/bin/env python3
"""Update Grauzone CSV with dates scraped from the festival homepage."""

import csv
import re
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup


def scrape_grauzone_dates(url="https://www.grauzonefestival.nl/"):
    """Scrape artist dates from Grauzone festival homepage.
    
    Returns a dict mapping artist URL slugs to dates.
    """
    
    print(f"Fetching {url}...")
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    slug_to_date = {}
    current_date = None
    
    # Find all links on the page
    all_links = soup.find_all('a', href=True)
    
    # Process the page content to find date sections
    page_html = str(soup)
    
    # Split by date headings to get sections
    date_pattern = r'(FRIDAY|SATURDAY|SUNDAY)\s+FEBRUARY\s+(\d+)'
    sections = re.split(date_pattern, page_html, flags=re.IGNORECASE)
    
    for i in range(1, len(sections), 3):
        if i+2 >= len(sections):
            break
            
        day_name = sections[i]
        day_num = sections[i+1]
        section_content = sections[i+2]
        
        current_date = f"2026-02-{day_num.zfill(2)}"
        print(f"\nProcessing date section: {current_date} ({day_name} FEBRUARY {day_num})")
        
        # Debug: show a snippet of the section
        snippet = section_content[:500] if len(section_content) > 500 else section_content
        print(f"Section snippet (first 500 chars): {snippet[:200]}...")
        
        # Find all artist URLs in this section - try multiple patterns
        artist_urls = []
        
        # Pattern 1: Full URLs
        artist_urls.extend(re.findall(r'https://www\.grauzonefestival\.nl/([a-z0-9\-]+)', section_content, re.IGNORECASE))
        
        # Pattern 2: Relative URLs
        artist_urls.extend(re.findall(r'href=["\']/?([a-z0-9\-]+)["\']', section_content, re.IGNORECASE))
        
        print(f"Found {len(artist_urls)} potential artist URLs")
        
        for slug in artist_urls:
            # Skip non-artist pages
            if slug in ['tickets', 'faq', 'shop', 'news', 'info', 'donate', 'policy', 'graukunst-3', 'cart', 'new-events', 'calendar']:
                continue
            
            if slug not in slug_to_date:
                slug_to_date[slug] = current_date
                print(f"  {slug} -> {current_date}")
    
    return slug_to_date


def update_csv_with_dates(csv_file, slug_to_date):
    """Update CSV file with scraped dates by matching Festival URLs."""
    
    # Read CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Update dates by matching Festival URL slugs
    updated_count = 0
    for row in rows:
        festival_url = row.get('Festival URL', '').strip()
        
        if festival_url:
            # Extract slug from Festival URL
            slug = festival_url.rstrip('/').split('/')[-1]
            
            if slug in slug_to_date:
                row['Date'] = slug_to_date[slug]
                updated_count += 1
                print(f"✓ Updated {row['Artist']}: {slug_to_date[slug]}")
    
    # Write back to CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Updated {updated_count} of {len(rows)} artists with dates")
    return updated_count


def main():
    """Main function."""
    
    # Find Grauzone CSV
    csv_file = Path(__file__).parent.parent.parent / 'docs' / 'grauzone' / '2026' / '2026.csv'
    
    if not csv_file.exists():
        print(f"Error: CSV file not found at {csv_file}")
        return 1
    
    print("=" * 60)
    print("Grauzone Festival - Date Updater")
    print("=" * 60)
    
    # Scrape dates from homepage
    slug_to_date = scrape_grauzone_dates()
    
    if not slug_to_date:
        print("\nError: No artist URLs found on homepage")
        return 1
    
    print(f"\nFound {len(slug_to_date)} artist URL slugs with dates")
    
    # Update CSV
    print("\nUpdating CSV...")
    update_csv_with_dates(csv_file, slug_to_date)
    
    print("\n✓ Done!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
