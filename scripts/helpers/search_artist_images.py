#!/usr/bin/env python3
"""
Interactive artist image search and download helper.

For festivals without individual artist pages (like Footprints), this script:
1. Searches Google Images for artist official bio photos
2. Shows top results to the user
3. Downloads the selected image to the artist folder
"""

import sys
from pathlib import Path

# Add parent directory to sys.path
# helpers module is in the same directory

import csv
import requests
import urllib.parse
from typing import List, Dict, Optional
from helpers import artist_name_to_slug, get_festival_config


def search_artist_images_bing(artist_name: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for artist images using Bing Image Search (no API key required).
    Scrapes Bing image search results page.
    
    Args:
        artist_name: Name of the artist to search for
        num_results: Number of results to return (default: 5)
        
    Returns:
        List of dicts with 'url', 'title' keys
    """
    import re
    
    try:
        query = urllib.parse.quote(f"{artist_name} official press photo")
        url = f"https://www.bing.com/images/search?q={query}&qft=+filterui:photo-photo&FORM=IRFLTR"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract image URLs from page using regex
        # Bing embeds image data in JavaScript on the page
        pattern = r'"murl":"([^"]+)"'
        matches = re.findall(pattern, response.text)
        
        results = []
        for match in matches[:num_results]:
            # Unescape URL
            img_url = match.replace('\\u002f', '/').replace('\\/', '/')
            results.append({
                'url': img_url,
                'title': f"Image from Bing search",
            })
        
        return results
        
    except Exception as e:
        print(f"  ⚠️  Bing search failed: {e}")
        return []


def search_artist_images(artist_name: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for artist images using Google Custom Search API or Bing fallback.
    
    Note: Google API requires credentials:
    - GOOGLE_API_KEY: Your Google API key
    - GOOGLE_SEARCH_ENGINE_ID: Your Custom Search Engine ID
    
    Args:
        artist_name: Name of the artist to search for
        num_results: Number of results to return (default: 5)
        
    Returns:
        List of dicts with 'url', 'thumbnail', 'title' keys
    """
    import os
    
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    # Try Bing first (no API key required)
    print("  → Searching Bing Images...")
    results = search_artist_images_bing(artist_name, num_results)
    if results:
        return results
    
    # Try Google API if credentials available
    if api_key and search_engine_id:
        print("  → Searching Google Images with API...")
        return search_artist_images_google(artist_name, num_results, api_key, search_engine_id)
    
    # No results from any automated method
    return []


def search_artist_images_google(artist_name: str, num_results: int, api_key: str, search_engine_id: str) -> List[Dict[str, str]]:
    """Search using Google Custom Search API."""
    query = f"{artist_name} official bio photo"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'searchType': 'image',
        'num': num_results,
        'imgType': 'photo',
        'imgSize': 'large',
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('items', []):
            results.append({
                'url': item['link'],
                'thumbnail': item['image'].get('thumbnailLink', ''),
                'title': item.get('title', ''),
                'width': item['image'].get('width', 0),
                'height': item['image'].get('height', 0),
            })
        
        return results
        
    except Exception as e:
        print(f"  ⚠️  Google API search failed: {e}")
        return []
    
    # Build search query
    query = f"{artist_name} official bio photo"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'searchType': 'image',
        'num': num_results,
        'imgType': 'photo',
        'imgSize': 'large',
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('items', []):
            results.append({
                'url': item['link'],
                'thumbnail': item['image'].get('thumbnailLink', ''),
                'title': item.get('title', ''),
                'width': item['image'].get('width', 0),
                'height': item['image'].get('height', 0),
            })
        
        return results
        
    except Exception as e:
        print(f"⚠️  Search failed: {e}")
        return []


def download_image(url: str, output_path: Path, slug: str, index: int = 1) -> Optional[Path]:
    """
    Download image from URL to local file.
    
    Args:
        url: Image URL
        output_path: Directory to save image
        slug: Artist slug for filename
        index: Image index for filename (default: 1)
        
    Returns:
        Path to downloaded file, or None if failed
    """
    try:
        # Determine file extension from URL or content type
        ext = '.jpg'
        if url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            ext = Path(url).suffix.lower()
        
        # Download image
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'image/png' in content_type:
            ext = '.png'
        elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
            ext = '.jpg'
        elif 'image/webp' in content_type:
            ext = '.webp'
        
        # Save to file
        filename = f"{slug}_{index}{ext}"
        file_path = output_path / filename
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✓ Downloaded: {filename}")
        return file_path
        
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return None


def get_manual_image_url(artist_name: str) -> Optional[str]:
    """
    Prompt user to manually provide an image URL.
    Opens Google Images search in browser to help user find images.
    
    Args:
        artist_name: Name of the artist
        
    Returns:
        Image URL or None if user skips
    """
    import webbrowser
    
    # Open Google Images search in browser
    search_query = urllib.parse.quote(f"{artist_name} official press photo")
    search_url = f"https://www.google.com/search?q={search_query}&tbm=isch"
    
    print(f"\n→ Manual image search for: {artist_name}")
    print(f"  Opening browser to: {search_url}")
    
    try:
        webbrowser.open(search_url)
    except:
        print(f"  ⚠️  Could not open browser automatically")
        print(f"  Please open: {search_url}")
    
    print("\n  Instructions:")
    print("  1. Find a good official/press photo in the browser")
    print("  2. Right-click the image and select 'Copy image address'")
    print("  3. Paste the URL below")
    print("  4. Or press Enter to skip this artist")
    
    url = input("\nImage URL: ").strip()
    
    if not url:
        return None
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        print("  ⚠️  Invalid URL (must start with http:// or https://)")
        return None
    
    return url


def process_artist(artist: Dict, festival_dir: Path, config) -> bool:
    """
    Process a single artist: search for images and download with user confirmation.
    
    Args:
        artist: Artist dict from CSV
        festival_dir: Festival directory (e.g., docs/footprints/2026)
        config: Festival config
        
    Returns:
        True if image was downloaded, False otherwise
    """
    artist_name = artist.get('Artist', '').strip()
    if not artist_name:
        return False
    
    slug = artist_name_to_slug(artist_name)
    artist_dir = festival_dir / 'artists' / slug
    artist_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if images already exist
    existing_images = list(artist_dir.glob('*'))
    existing_images = [f for f in existing_images if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
    
    if existing_images:
        print(f"\n{artist_name}")
        print(f"  ℹ️  Already has {len(existing_images)} image(s): {', '.join(f.name for f in existing_images)}")
        overwrite = input("  Replace? (y/N): ").strip().lower()
        if overwrite != 'y':
            return False
    
    print(f"\n{'='*60}")
    print(f"Searching for: {artist_name}")
    print('='*60)
    
    # Try API search first
    results = search_artist_images(artist_name)
    
    if results:
        print(f"\nFound {len(results)} images:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Size: {result['width']}x{result['height']}")
            if result['thumbnail']:
                print(f"   Preview: {result['thumbnail']}")
        
        print("\nOptions:")
        print("  1-{}: Select image number".format(len(results)))
        print("  M: Enter URL manually")
        print("  S: Skip this artist")
        
        choice = input("\nChoice: ").strip().upper()
        
        if choice == 'S':
            return False
        elif choice == 'M':
            url = get_manual_image_url(artist_name)
            if url:
                return download_image(url, artist_dir, slug) is not None
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    url = results[idx]['url']
                    return download_image(url, artist_dir, slug) is not None
                else:
                    print("  ⚠️  Invalid choice")
            except ValueError:
                print("  ⚠️  Invalid choice")
    else:
        # No API results - fall back to manual entry
        url = get_manual_image_url(artist_name)
        if url:
            return download_image(url, artist_dir, slug) is not None
    
    return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Search and download artist images interactively"
    )
    parser.add_argument(
        "--festival",
        type=str,
        required=True,
        help="Festival identifier (e.g., footprints)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Festival year (default: 2026)"
    )
    parser.add_argument(
        "--artist",
        type=str,
        help="Process only a specific artist"
    )
    
    args = parser.parse_args()
    
    # Get festival config
    config = get_festival_config(args.festival, args.year)
    
    # Load CSV
    csv_path = Path(f"docs/{config.slug}/{args.year}/{args.year}.csv")
    if not csv_path.exists():
        print(f"✗ CSV not found: {csv_path}")
        sys.exit(1)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        artists = list(reader)
    
    # Filter by artist name if specified
    if args.artist:
        artists = [a for a in artists if args.artist.lower() in a.get('Artist', '').lower()]
        if not artists:
            print(f"✗ No artists found matching: {args.artist}")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"{config.name} {args.year} - Image Search")
    print(f"{'='*60}")
    print(f"\nProcessing {len(artists)} artist(s)")
    
    festival_dir = Path(f"docs/{config.slug}/{args.year}")
    downloaded_count = 0
    
    for artist in artists:
        if process_artist(artist, festival_dir, config):
            downloaded_count += 1
    
    print(f"\n{'='*60}")
    print(f"✓ Downloaded images for {downloaded_count}/{len(artists)} artist(s)")
    print('='*60)


if __name__ == "__main__":
    main()
