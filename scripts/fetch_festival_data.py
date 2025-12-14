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

import sys
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
import sys
sys.path.insert(0, str(Path(__file__).parent))

import csv
import json
import argparse
from typing import Dict, List, Optional
from helpers import (
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


def fetch_artist_festival_data(artist_name: str, scraper: FestivalScraper, config, existing_url: str = '') -> Dict[str, str]:
    """
    Fetch festival data for an artist.
    
    Args:
        artist_name: Name of the artist
        scraper: FestivalScraper instance
        config: Festival configuration
        existing_url: Existing Festival URL from CSV (if available)
    
    Returns:
        Dict with festival bio (NL/EN), URL, and social links
    """
    # Use existing URL if available, otherwise generate from slug
    if existing_url:
        festival_url = existing_url
    else:
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
        # Fetch HTML directly from the festival URL
        html = scraper.fetch_page(festival_url)
        if not html:
            print(f"  ⚠ Could not fetch page")
            return result
        
        # Extract bio from HTML
        bio = scraper.extract_bio(html, artist_name)
        if bio:
            print(f"  ✓ Fetched bio ({len(bio)} chars)")
            
            # Handle language-specific logic
            if config.bio_language == 'Dutch':
                result['Festival Bio (NL)'] = bio
                
                # Translate to English
                print(f"  → Translating bio to English...")
                bio_en = translate_text(bio, "Dutch", "English")
                if bio_en:
                    result['Festival Bio (EN)'] = bio_en
                    print(f"  ✓ Translated bio ({len(bio_en)} chars)")
            elif config.bio_language == 'English':
                # Bio is already in English
                result['Festival Bio (EN)'] = bio
                result['Festival Bio (NL)'] = ''  # No Dutch version
            else:
                # Unknown language - store as English
                result['Festival Bio (EN)'] = bio
                result['Festival Bio (NL)'] = ''
        else:
            print(f"  ⚠ No bio found on festival website")
        
        # Extract social links from the same HTML
        if html:
            social_links = extract_social_links(html)
            if social_links:
                result['Social Links'] = json.dumps(social_links)
                print(f"  ✓ Found {len(social_links)} social link(s)")
        
        # Extract and download images
        if html:
            image_urls = extract_images_from_html(html, config, artist_name)
            if image_urls:
                print(f"  → Found {len(image_urls)} image URL(s)")
                for url in image_urls:
                    print(f"     {url}")
                    
                slug = artist_name_to_slug(artist_name)
                # Create artist-specific image directory
                artist_images_dir = Path(f"docs/{config.slug}/{config.year}/artists/{slug}")
                artist_images_dir.mkdir(parents=True, exist_ok=True)
                
                downloaded_count = 0
                for img_url in image_urls:
                    filename = download_image(img_url, artist_images_dir, slug)
                    if filename:
                        downloaded_count += 1
                
                if downloaded_count > 0:
                    result['Images Scraped'] = 'Yes'
                    print(f"  ✓ Downloaded {downloaded_count} image(s)")
            else:
                print(f"  ⚠ No artist-specific images found")
        
        return result
        
    except Exception as e:
        print(f"  ✗ Error fetching data: {e}")
        return result


def download_image(img_url: str, output_dir: Path, artist_slug: str) -> Optional[str]:
    """Download an image and save it locally. Returns the local filename or None if failed."""
    try:
        # Create a hash of the URL to generate a unique filename
        url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
        
        # Get file extension from URL
        ext = '.png'
        if '.jpg' in img_url.lower() or '.jpeg' in img_url.lower():
            ext = '.jpg'
        elif '.webp' in img_url.lower():
            ext = '.webp'
        
        # Create filename: artist-slug_hash.ext
        filename = f"{artist_slug}_{url_hash}{ext}"
        local_path = output_dir / filename
        
        # Download if not already cached
        if not local_path.exists():
            req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                img_data = response.read()
            
            with open(local_path, 'wb') as f:
                f.write(img_data)
        
        # Return filename
        return filename
        
    except Exception as e:
        print(f"    ⚠️  Failed to download image: {e}")
        return None


def extract_images_from_html(html: str, config, artist_name: str = '') -> List[str]:
    """Extract artist image URLs from festival page HTML."""
    import re
    
    artist_images = []
    og_image_found = False
    
    try:
        # Try og:image meta tag first (Bospop, many WordPress sites) - HIGHEST PRIORITY
        og_image_pattern = r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']'
        og_images = re.findall(og_image_pattern, html)
        
        # Process og:image first (highest priority for Bospop)
        for img_url in og_images:
            img_lower = img_url.lower()
            
            # Check for Bospop images (WordPress uploads from bospopfestival.nl)
            is_bospop_image = 'wp-content/uploads' in img_lower and 'bospopfestival.nl' in config.base_url.lower()
            
            if is_bospop_image:
                # Skip logos, default images, and other non-artist images
                if any(skip in img_lower for skip in ['logo', 'icon', 'brand', 'sponsor', 'default', 'placeholder']):
                    continue
                
                # Skip thumbnails
                if '/thumbs/' in img_lower or '/thumb/' in img_lower:
                    continue
                
                # Skip images with generic year-only paths (likely defaults)
                if re.search(r'/20\d{2}/[^/]*\.(jpg|png|webp)$', img_lower):
                    continue
                
                if img_url not in artist_images:
                    artist_images.append(img_url)
                    og_image_found = True
        
        # If we found a good og:image, use ONLY that and skip other sources
        if og_image_found:
            return artist_images
        
        # Only continue to other sources if og:image wasn't found
        # Try srcset (DTRH, Pinkpop)
        srcset_pattern = r'srcset=["\']([^"\']+)["\']'
        all_srcsets = re.findall(srcset_pattern, html)
        
        # Also try regular img src (Rock Werchter, Bospop)
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        all_imgs = re.findall(img_pattern, html)
        
        # Process srcset
        for srcset in all_srcsets:
            # Parse srcset - it contains multiple URLs separated by commas
            urls = [url.strip().split()[0] for url in srcset.split(',') if url.strip()]
            if not urls:
                continue
                
            img_url = urls[-1]  # Use the largest size
            img_lower = img_url.lower()
            
            # Skip thumbnails
            if '/thumbs/' in img_lower or '/thumb/' in img_lower or 'thumbnail' in img_lower:
                continue
            
            # Check for Down The Rabbit Hole images
            is_dtrh_image = 'cache/media_' in img_lower and ('crop_' in img_lower or 'fit_' in img_lower or 'widen_' in img_lower)
            
            # Check for Pinkpop images (WordPress uploads with acts-header pattern)
            is_pinkpop_image = 'wp-content/uploads' in img_lower and 'acts-header' in img_lower
            
            # Check for Bospop images (WordPress uploads from bospopfestival.nl)
            is_bospop_image = 'wp-content/uploads' in img_lower and 'bospopfestival.nl' in config.base_url.lower()
            
            # Check for Rock Werchter images (cache/default_band or media/cache)
            is_rock_werchter_image = 'cache/default_band' in img_lower or ('media/cache' in img_lower and 'rockwerchter' in img_lower)
            
            if is_dtrh_image or is_pinkpop_image or is_bospop_image or is_rock_werchter_image:
                # Skip sponsor/logo images
                if any(skip in img_lower for skip in ['rabobank', 'sponsor', 'woordmerk', 'rgb', 'logo', 'brand', 'default', 'placeholder']):
                    continue
                
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = config.base_url.rstrip('/') + img_url
                
                if img_url not in artist_images:
                    artist_images.append(img_url)
        
        # Process regular img tags for Rock Werchter and Bospop
        for img_url in all_imgs:
            img_lower = img_url.lower()
            
            # Skip thumbnails
            if '/thumbs/' in img_lower or '/thumb/' in img_lower or 'thumbnail' in img_lower:
                continue
            
            # Check for Rock Werchter images
            is_rock_werchter_image = ('/media/cache/default_band/upload/' in img_lower or 
                                     'cache/default_band/upload/' in img_lower)
            
            # Check for Bospop images in regular img tags (WordPress uploads)
            is_bospop_image = ('wp-content/uploads' in img_lower and 'bospopfestival.nl' in config.base_url.lower())
            
            if is_rock_werchter_image or is_bospop_image:
                # Skip logos and other non-artist images
                if any(skip in img_lower for skip in ['logo', 'icon', 'brand', 'sponsor', 'default', 'placeholder']):
                    continue
                
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = config.base_url.rstrip('/') + img_url
                
                if img_url not in artist_images:
                    artist_images.append(img_url)
        
        # Use second image if available (first is often festival logo)
        if len(artist_images) >= 2:
            artist_images = [artist_images[1]]
        elif artist_images:
            artist_images = [artist_images[0]]
            
    except Exception as e:
        print(f"  ✗ Error extracting images: {e}")
    
    return artist_images


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
    parser.add_argument(
        "--artist",
        type=str,
        help="Fetch data for a single artist only"
    )
    
    args = parser.parse_args()
    
    # Get festival config and scraper
    config = get_festival_config(args.festival, args.year)
    scraper = FestivalScraper(config)
    
    # CSV file path - use festival-specific path
    # Try multiple locations
    csv_locations = [
        Path(f"docs/{config.slug}/{args.year}/{args.year}.csv"),
        Path(f"{config.slug}/{args.year}.csv")
    ]
    csv_path = None
    for loc in csv_locations:
        if loc.exists():
            csv_path = loc
            break
    
    # If CSV doesn't exist, create it with scraped lineup
    if not csv_path:
        csv_path = Path(f"docs/{config.slug}/{args.year}/{args.year}.csv")
        print(f"CSV not found. Creating new CSV at: {csv_path}")
        
        # Create directory structure
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Scrape lineup to create initial CSV
        print(f"Scraping lineup from {config.lineup_url}...")
        artists = scraper.scrape_lineup()
        
        if not artists:
            print("✗ No artists found")
            sys.exit(1)
        
        # Create CSV with basic structure
        import csv as csv_module
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv_module.DictWriter(f, fieldnames=[
                'Artist', 'Genre', 'Country', 'Bio', 'AI Summary', 'AI Rating',
                'Spotify link', 'Number of People in Act', 'Gender of Front Person',
                'Front Person of Color?', 'Festival URL', 'Festival Bio (NL)',
                'Festival Bio (EN)', 'Social Links', 'Images Scraped'
            ])
            writer.writeheader()
            for artist in artists:
                writer.writerow({
                    'Artist': artist['name'],
                    'Festival URL': artist.get('url', ''),
                    'Genre': '', 'Country': '', 'Bio': '', 'AI Summary': '', 'AI Rating': '',
                    'Spotify link': '', 'Number of People in Act': '',
                    'Gender of Front Person': '', 'Front Person of Color?': '',
                    'Festival Bio (NL)': '', 'Festival Bio (EN)': '',
                    'Social Links': '', 'Images Scraped': ''
                })
        
        print(f"✓ Created CSV with {len(artists)} artists")
    
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
    
    # Filter to single artist if specified
    all_rows = rows  # Keep reference to all rows for saving
    if args.artist:
        filtered_rows = [row for row in rows if row.get('Artist', '').strip().lower() == args.artist.lower()]
        if not filtered_rows:
            print(f"✗ Artist '{args.artist}' not found in CSV")
            sys.exit(1)
        print(f"Processing 1 artist: {filtered_rows[0].get('Artist')}\n")
        rows_to_process = filtered_rows
    else:
        print(f"Processing {len(rows)} artists...\n")
        rows_to_process = rows
    
    updated_count = 0
    skipped_count = 0
    
    for idx, row in enumerate(rows_to_process):
        artist_name = row.get('Artist', '').strip()
        if not artist_name:
            continue
        
        print(f"[{idx+1}/{len(rows_to_process)}] {artist_name}")
        
        # Check if needs data
        if not args.force and not needs_festival_data(row):
            print(f"  ✓ Already has festival data (use --force to re-fetch)")
            skipped_count += 1
            continue
        
        # Fetch festival data
        existing_url = row.get('Festival URL', '').strip()
        festival_data = fetch_artist_festival_data(artist_name, scraper, config, existing_url)
        
        # Update row
        for key, value in festival_data.items():
            if value:  # Only update if we got data
                row[key] = value
        
        updated_count += 1
        
        # Rate limit
        scraper.rate_limit_delay(1.0)
        print()
    
    # Save updated CSV (save all rows, not just filtered)
    save_csv(csv_path, headers, all_rows)
    
    print(f"\n✓ Festival data fetching complete!")
    print(f"  Updated: {updated_count} artist(s)")
    print(f"  Skipped: {skipped_count} artist(s)")
    print(f"\nNext steps:")
    print(f"  1. Run: python enrich_artists.py --ai  (if needed)")
    print(f"  2. Run: python generate_html.py --year {args.year}")
    print(f"  3. Run: python generate_artist_pages.py --year {args.year}")


if __name__ == "__main__":
    main()
