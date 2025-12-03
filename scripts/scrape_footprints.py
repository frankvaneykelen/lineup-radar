"""
Custom scraper for Footprints Festival.

This festival doesn't have a standard festival website with artist pages,
so we need to combine multiple sources:
1. Artists mentioned in the event description
2. Artists listed in the "Line-up" section on the venue page
3. Artists from the Spotify playlist
"""

import sys
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
import csv
import re
from festival_helpers.config import get_festival_config


def parse_book_csv(csv_path: str) -> list[dict]:
    """
    Parse the Book(Sheet1).csv file with pre-filled artist data.
    
    Args:
        csv_path: Path to Book(Sheet1).csv
        
    Returns:
        List of artist dictionaries with all data
    """
    artists = []
    
    try:
        print(f"  Reading from: {csv_path}")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row_count = 0
            for row in reader:
                row_count += 1
                # Map from Book CSV columns to our CSV format
                artist_name = row.get('Name', '').strip()
                print(f"    Row {row_count}: {artist_name}")
                
                artist_data = {
                    'Artist': artist_name,
                    'Genre': row.get('Genre', '').strip(),
                    'Country': row.get('Country', '').strip(),
                    'Bio': row.get('Bio', '').strip(),
                    'My take': row.get('Live Assessment', '').strip(),
                    'My rating': '',  # Will be filled by AI enrichment
                    'Spotify link': '',  # Will be filled by fetch_spotify_links
                    'Number of People in Act': row.get('# in Act', '').strip(),
                    'Gender of Front Person': row.get('Front Person Gender', '').strip(),
                    'Front Person of Color?': row.get('Front Person of Color?', '').strip(),
                    'Cancelled': '',
                    'Social Links': '',
                    'Images Scraped': 'No'
                }
                
                if artist_data['Artist']:
                    artists.append(artist_data)
                else:
                    print(f"      (skipped - no artist name)")
        
        print(f"✓ Parsed {len(artists)} artists from Book(Sheet1).csv")
        return artists
        
    except FileNotFoundError:
        print(f"⚠ Book(Sheet1).csv not found at {csv_path}")
        return []
    except Exception as e:
        print(f"⚠ Error parsing Book(Sheet1).csv: {e}")
        import traceback
        traceback.print_exc()
        return []


def find_downloaded_html_file() -> str:
    """
    Look for manually downloaded HTML file in common locations.
    
    Returns:
        Path to the HTML file if found, None otherwise
    """
    import os
    from pathlib import Path
    
    # Check specific paths
    possible_paths = [
        'Footprints Festival – TivoliVredenburg.html',
        'docs/footprints/2026/Footprints Festival – TivoliVredenburg.html',
        os.path.join(os.getcwd(), 'Footprints Festival – TivoliVredenburg.html'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Also check for any HTML file in the footprints folder
    footprints_dir = Path('docs/footprints/2026')
    if footprints_dir.exists():
        for html_file in footprints_dir.glob('*.html'):
            if 'TivoliVredenburg' in html_file.name:
                return str(html_file)
    
    return None


def scrape_local_html_file(file_path: str) -> list[dict]:
    """
    Scrape artist names and bios from a locally saved HTML file.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        List of dictionaries with 'name' and 'bio' keys
    """
    artists = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for artist names and bios in accordion items
        accordions = soup.find_all('div', class_='js-accordion accordion')
        for accordion in accordions:
            title_div = accordion.find('div', class_='js-accordion-trigger accordion__title')
            if title_div:
                h2 = title_div.find('h2')
                if h2:
                    artist_name = h2.text.strip()
                    # Filter out the U-pas entry
                    if 'u-pas' not in artist_name.lower() and artist_name:
                        # Get the bio from the accordion content
                        content_div = accordion.find('div', class_='js-accordion-target')
                        bio = ''
                        if content_div:
                            # Extract text but skip iframe/embed content
                            paragraphs = content_div.find_all('p')
                            bio_parts = []
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                # Skip empty paragraphs and iframe-related text
                                if text and not text.startswith('Je cookie'):
                                    bio_parts.append(text)
                            bio = ' '.join(bio_parts)
                        elif not content_div:
                            # Debug: content div not found
                            print(f"  ! No content div found for {artist_name}")
                        
                        artists.append({
                            'name': artist_name,
                            'bio': bio
                        })
        
        print(f"✓ Found {len(artists)} artists with bios from local HTML file")
        
    except Exception as e:
        print(f"⚠ Error reading local HTML file: {e}")
    
    return artists


def scrape_venue_page(url: str) -> list[dict]:
    """
    Scrape artist names and bios from the TivoliVredenburg venue page.
    If the page returns 403, prompts user to download it manually.
    
    Args:
        url: URL to the event page
        
    Returns:
        List of dictionaries with 'name' and 'bio' keys
    """
    artists = []
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for artist names and bios in accordion items
        accordions = soup.find_all('div', class_='js-accordion accordion')
        for accordion in accordions:
            title_div = accordion.find('div', class_='js-accordion-trigger accordion__title')
            if title_div:
                h2 = title_div.find('h2')
                if h2:
                    artist_name = h2.text.strip()
                    # Filter out the U-pas entry
                    if 'u-pas' not in artist_name.lower() and artist_name:
                        # Get the bio from the accordion content
                        content_div = accordion.find('div', class_='js-accordion-target')
                        bio = ''
                        if content_div:
                            paragraphs = content_div.find_all('p')
                            bio_parts = []
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if text and not text.startswith('Je cookie'):
                                    bio_parts.append(text)
                            bio = ' '.join(bio_parts)
                        
                        artists.append({
                            'name': artist_name,
                            'bio': bio
                        })
        
        print(f"✓ Found {len(artists)} artists with bios from venue page")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"⚠ The venue page returned a 403 Forbidden error.")
            print(f"\n📥 Please download the page manually:")
            print(f"   1. Open {url} in your browser")
            print(f"   2. Right-click and select 'Save As...' or use Ctrl+S")
            print(f"   3. Save as 'Footprints Festival – TivoliVredenburg.html'")
            print(f"   4. Place it in the current directory\n")
            
            # Try to find the file in common locations
            html_file = find_downloaded_html_file()
            if html_file:
                print(f"✓ Found downloaded HTML file: {html_file}")
                return scrape_local_html_file(html_file)
            else:
                print(f"⚠ No local HTML file found. Skipping venue page scraping.")
        else:
            print(f"⚠ Error scraping venue page: {e}")
    except Exception as e:
        print(f"⚠ Error scraping venue page: {e}")
    
    return artists


def get_spotify_playlist_artists(playlist_url: str) -> list[str]:
    """
    Extract artist names from Spotify playlist URL.
    
    Uses Spotify API (no authentication required for public playlists).
    
    Args:
        playlist_url: Spotify playlist URL
        
    Returns:
        List of artist names from playlist
    """
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    
    artists = []
    
    try:
        # Extract playlist ID from URL
        # URL format: https://open.spotify.com/playlist/2Qt2F5Mwnsd56LFfzagivS?si=...
        playlist_id = playlist_url.split('/playlist/')[-1].split('?')[0]
        
        # Initialize Spotify client with credentials from environment
        import os
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            print("  ⚠ Spotify API requires credentials")
            print("  Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables")
            print("  Get credentials from: https://developer.spotify.com/dashboard")
            return []
        
        # Create Spotify client with proper authentication
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Fetch playlist tracks
        results = sp.playlist_tracks(playlist_id)
        
        # Extract unique artist names
        artist_set = set()
        
        while results:
            for item in results['items']:
                if item['track'] and item['track']['artists']:
                    for artist in item['track']['artists']:
                        artist_name = artist['name']
                        artist_set.add(artist_name)
            
            # Check for more tracks
            if results['next']:
                results = sp.next(results)
            else:
                results = None
        
        artists = list(artist_set)
        print(f"✓ Found {len(artists)} unique artists from Spotify playlist")
        
    except Exception as e:
        print(f"⚠ Error accessing Spotify playlist: {e}")
        print("  Continuing with manual artists only...")
    
    return artists


def create_footprints_csv(year: int = 2026):
    """
    Create CSV file for Footprints Festival.
    
    Args:
        year: Festival year
    """
    config = get_festival_config('footprints', year)
    
    print(f"\n=== Creating lineup for {config.name} {year} ===\n")
    
    # Check for Book(Sheet1).csv first (preferred method)
    book_csv_path = Path(config.output_dir) / "Book(Sheet1).csv"
    
    if book_csv_path.exists():
        print(f"✓ Found Book(Sheet1).csv - using pre-filled data")
        artist_data_list = parse_book_csv(str(book_csv_path))
        
        if artist_data_list:
            # Create output CSV directly from parsed data
            output_dir = Path(config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_path = output_dir / config.csv_filename
            
            headers = [
                'Artist', 'Genre', 'Country', 'Bio', 'My take', 'My rating',
                'Spotify link', 'Number of People in Act', 'Gender of Front Person',
                'Front Person of Color?', 'Festival URL', 'Festival Bio (NL)', 
                'Festival Bio (EN)', 'Social Links', 'Images Scraped'
            ]
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for artist_data in artist_data_list:
                    # Ensure all headers are present
                    row = {header: artist_data.get(header, '') for header in headers}
                    writer.writerow(row)
            
            print(f"\n✓ Created CSV: {csv_path}")
            print(f"  {len(artist_data_list)} artists with pre-filled data")
            print("\nNext steps:")
            print(f"  1. Run: python fetch_spotify_links.py --festival footprints --year {year}")
            print(f"  2. Run: python generate_html.py --festival footprints --year {year}")
            print(f"  3. Run: python generate_artist_pages.py --festival footprints --year {year}")
            return
        else:
            print("  ⚠ Book(Sheet1).csv was empty or couldn't be parsed")
            print("  Falling back to scraping method...\n")
    
    # Fallback: Collect artists from all sources (original scraping method)
    all_artists = set()
    
    # 1. Manual artists from config
    from festival_helpers.config import FESTIVALS
    manual_artists = FESTIVALS.get('footprints', {}).get('manual_artists', [])
    
    print(f"📝 Manual artists from config: {len(manual_artists)}")
    all_artists.update(manual_artists)
    
    # 2. Scrape venue page
    print("\n🔍 Scraping venue page...")
    venue_artists_data = scrape_venue_page(config.lineup_url)
    
    # Create a dictionary to store artist bios
    artist_bios = {}
    for artist_data in venue_artists_data:
        if isinstance(artist_data, dict):
            artist_bios[artist_data['name']] = artist_data.get('bio', '')
            all_artists.add(artist_data['name'])
        else:
            # Legacy string format
            all_artists.add(artist_data)
    
    print(f"  Extracted {len(artist_bios)} bios from venue page")
    if artist_bios:
        print(f"  Sample bio keys: {list(artist_bios.keys())[:3]}")
    
    # 3. Get Spotify playlist artists (if implemented)
    from festival_helpers.config import FESTIVALS
    spotify_url = FESTIVALS.get('footprints', {}).get('spotify_playlist')
    if spotify_url:
        print("\n🎵 Checking Spotify playlist...")
        spotify_artists = get_spotify_playlist_artists(spotify_url)
        all_artists.update(spotify_artists)
    
    # Clean up artist names
    cleaned_artists = []
    for artist in all_artists:
        artist = artist.strip()
        # Remove common false positives
        if len(artist) < 3 or artist.lower() in ['en', 'and', 'the', 'de', 'het']:
            continue
        # Remove leading/trailing non-alphanumeric chars
        artist = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9\s&]+$', '', artist)
        if artist:
            cleaned_artists.append(artist)
    
    # Remove duplicates and sort
    unique_artists = sorted(set(cleaned_artists), key=str.lower)
    
    print(f"\n✓ Total unique artists found: {len(unique_artists)}")
    print("\nArtists:")
    for artist in unique_artists:
        print(f"  - {artist}")
    
    # Create output directory
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create CSV
    csv_path = output_dir / config.csv_filename
    
    headers = [
        'Artist', 'Genre', 'Country', 'Bio', 'My take', 'My rating',
        'Spotify link', 'Number of People in Act', 'Gender of Front Person',
        'Front Person of Color?', 'Cancelled', 'Social Links', 'Images Scraped'
    ]
    
    # Debug: show which artists have bios
    print(f"\n  Matching bios to final artist list...")
    print(f"  Final artist list ({len(unique_artists)} total):")
    for i, artist in enumerate(unique_artists):
        has_bio = 'YES' if artist in artist_bios else 'NO'
        print(f"    {i+1}. {artist} [{has_bio}]")
    
    print(f"\n  Bio dictionary ({len(artist_bios)} entries):")
    for key in list(artist_bios.keys())[:5]:
        bio_len = len(artist_bios[key])
        preview = artist_bios[key][:50] if bio_len > 0 else "(empty)"
        print(f"    - '{key}': {bio_len} chars - {preview}...")
    
    artists_with_bios = [name for name in unique_artists if artist_bios.get(name)]
    if artists_with_bios:
        print(f"\n  ✓ Found {len(artists_with_bios)} artists with bios")
    else:
        print(f"\n  ⚠ No matching artist names found!")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for artist in unique_artists:
            # Get bio if available from venue page
            bio = artist_bios.get(artist, '')
            if bio:  # Debug: print when we find a match
                print(f"    ✓ Writing bio for {artist} ({len(bio)} chars)")
            # Write row with artist name and bio, rest empty
            row = [artist, '', '', bio] + [''] * (len(headers) - 4)
            writer.writerow(row)
    
    print(f"\n✓ Created CSV: {csv_path}")
    print(f"  {len(unique_artists)} artists listed")
    print("\nNext steps:")
    print(f"  1. Review and edit {csv_path} to remove any false positives")
    print(f"  2. Add any missing artists manually")
    print(f"  3. Run: python enrich_artists.py --festival footprints --year {year} --ai")
    print(f"  4. Run: python generate_html.py --festival footprints --year {year}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Footprints Festival lineup')
    parser.add_argument('--year', type=int, default=2026, help='Festival year')
    
    args = parser.parse_args()
    
    create_footprints_csv(args.year)
