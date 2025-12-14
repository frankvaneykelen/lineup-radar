"""
Interactive script to manually enrich artist data in CSV files.
Prompts for official website first, then scrapes and uses AI to auto-fill fields.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
import shutil
import requests
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup

# Add parent directory to path to import festival_helpers
import sys
sys.path.insert(0, str(Path(__file__).parent))

from helpers import get_festival_config, artist_name_to_slug
from helpers.ai_client import call_azure_openai


def scrape_website(url):
    """Scrape text content from a website."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text(separator=' ', strip=True)
        # Limit to reasonable length for AI processing
        text = ' '.join(text.split()[:1000])  # ~1000 words
        
        return text
    except Exception as e:
        print(f"  ⚠️  Could not scrape website: {e}")
        return None


def analyze_artist_with_ai(artist_name, website_text):
    """Use AI to extract artist information from website content."""
    try:
        # Check if AI credentials are available
        if not os.getenv("AZURE_OPENAI_KEY") or not os.getenv("AZURE_OPENAI_ENDPOINT"):
            print(f"  ⚠️  Azure OpenAI credentials not set - skipping AI analysis")
            print(f"     Set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT to enable AI features")
            return None
        
        prompt = f"""Analyze the following website content for the artist/band "{artist_name}" and extract structured information.

Website content:
{website_text}

Please provide a JSON response with the following fields:
- genre: The musical genre (e.g., "Indie Rock", "Electronic", "Folk")
- country: The country of origin
- bio: A 2-3 sentence biography suitable for a festival program
- band_size: Estimated number of people in the act (integer, or null if unknown)
- gender: Gender of front person ("Male", "Female", "Non-Binary", or null if unknown/mixed gender band/no identifiable single front person)
- person_of_color: Is the front person a person of color? ("Yes", "No", or null if unknown)

Only include fields where you have confident information. Return valid JSON only. If there is no single front person or if it's a mixed-gender band, return null for gender."""

        messages = [
            {"role": "system", "content": "You are a music industry analyst extracting factual information about artists from their websites. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        result = call_azure_openai(messages, temperature=0.3, max_tokens=500)
        
        # Remove markdown code blocks if present
        result = result.strip()
        if result.startswith('```'):
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
            result = result.rsplit('```', 1)[0]
        
        return json.loads(result)
        
    except Exception as e:
        print(f"  ⚠️  AI analysis failed: {e}")
        return None


def download_image(url, save_path):
    """Download an image from a URL."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  ❌ Error downloading image: {e}")
        return False


def scrape_spotify_image(spotify_url):
    """Scrape the main artist image from a Spotify artist page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(spotify_url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for Open Graph image (og:image meta tag) - usually the main artist image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Look for artist profile images (not album covers)
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            # Only include artist profile images, not album covers
            if 'ab6761610000' in src and 'i.scdn.co/image/' in src:
                return src
        
        return None
    except Exception as e:
        print(f"  ⚠️  Could not scrape Spotify image: {e}")
        return None
        return None


def copy_local_image(source_path, dest_path):
    """Copy a local image file."""
    try:
        shutil.copy2(source_path, dest_path)
        return True
    except Exception as e:
        print(f"  ❌ Error copying image: {e}")
        return False


def get_input(prompt, default=None, allow_empty=True):
    """Get user input with optional default value."""
    if default:
        prompt = f"{prompt} [{default}]"
    prompt += ": "
    
    value = input(prompt).strip()
    
    if not value and default:
        return default
    
    if not value and allow_empty:
        return ""
    
    return value


def process_artist(artist_data, artists_dir, artist_name, csv_path, all_artists, fieldnames):
    """Prompt for artist data interactively."""
    
    # Create artist-specific directory
    from helpers import artist_name_to_slug as slug_func
    artist_slug = slug_func(artist_name)
    artist_dir = artists_dir / artist_slug
    artist_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Artist: {artist_name}")
    print(f"{'='*60}")
    
    # Show Google search link
    search_query = f'"{artist_name}" Alkmaar Eigenste Victorie Muziek'
    search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
    print(f"\n🔍 Google Search: {search_url}")
    
    # Show existing data if any
    if artist_data.get('Website'):
        print(f"  Current Website: {artist_data['Website']}")
    if artist_data.get('Genre'):
        print(f"  Current Genre: {artist_data['Genre']}")
    if artist_data.get('Country'):
        print(f"  Current Country: {artist_data['Country']}")
    if artist_data.get('Bio'):
        print(f"  Current Bio: {artist_data['Bio'][:100]}...")
    if artist_data.get('Spotify'):
        print(f"  Current Spotify: {artist_data['Spotify']}")
    
    print()
    
    def save_progress():
        """Save CSV after each field update."""
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_artists)
    
    # Step 1: Ask for website first
    website_url = None
    if not artist_data.get('Website') or artist_data.get('Website') == '':
        website_input = get_input("Official Website (press Enter to skip, or type 'no' if artist has no website)", allow_empty=True)
        if website_input:
            if website_input.lower() == 'no':
                artist_data['Website'] = 'HAS_NO_WEBSITE'
                save_progress()
            else:
                artist_data['Website'] = website_input
                website_url = website_input
                save_progress()
    elif artist_data.get('Website') == 'HAS_NO_WEBSITE':
        # Skip - already marked as having no website
        pass
    else:
        website_url = artist_data['Website']
    
    # Step 2: Try to scrape and analyze website with AI
    ai_data = None
    scrape_url = website_url
    
    # If no website, offer to use Spotify or social media for AI analysis
    if not scrape_url and not artist_data.get('Genre'):
        if artist_data.get('Spotify'):
            use_spotify = get_input(f"No website found. Use Spotify page for AI analysis? (y/n)", default="y")
            if use_spotify.lower() == 'y':
                scrape_url = artist_data['Spotify']
        else:
            alt_url = get_input("Enter Instagram/Facebook/Bandcamp URL for AI analysis (or press Enter to skip)", allow_empty=True)
            if alt_url:
                scrape_url = alt_url
    
    # Perform AI analysis if we have a URL and missing data
    if scrape_url and (not artist_data.get('Genre') or not artist_data.get('Bio')):
        print(f"\n  🤖 Scraping and analyzing with AI...")
        website_text = scrape_website(scrape_url)
        if website_text:
            ai_data = analyze_artist_with_ai(artist_name, website_text)
            if ai_data:
                print(f"  ✓ AI extracted information:")
                for key, value in ai_data.items():
                    if value:
                        print(f"    - {key}: {value}")
    
    # Step 3: Use AI data or prompt for missing fields
    if not artist_data.get('Genre'):
        if ai_data and ai_data.get('genre'):
            confirm = get_input(f"Genre: {ai_data['genre']} (press Enter to accept, or type different)", default="accept")
            artist_data['Genre'] = ai_data['genre'] if confirm == "accept" else confirm
        else:
            artist_data['Genre'] = get_input("Genre (lowercase, use / to separate multiple genres, e.g., indie rock/pop/electronic)")
        if artist_data['Genre']:
            save_progress()
    
    if not artist_data.get('Country'):
        if ai_data and ai_data.get('country'):
            confirm = get_input(f"Country: {ai_data['country']} (press Enter to accept, or type different)", default="accept")
            artist_data['Country'] = ai_data['country'] if confirm == "accept" else confirm
        else:
            artist_data['Country'] = get_input("Country", default="Netherlands")
        if artist_data['Country']:
            save_progress()
    
    if not artist_data.get('Bio'):
        if ai_data and ai_data.get('bio'):
            print(f"\nAI-generated Bio:\n{ai_data['bio']}")
            confirm = get_input("Use this bio? (y/n/edit)", default="y")
            if confirm == 'y':
                artist_data['Bio'] = ai_data['bio']
            elif confirm == 'edit':
                print("Enter your bio (multi-line, press Ctrl+D or Ctrl+Z when done):")
                bio_lines = []
                try:
                    while True:
                        line = input()
                        if line == "" and len(bio_lines) > 0:
                            break
                        bio_lines.append(line)
                except EOFError:
                    pass
                artist_data['Bio'] = " ".join(bio_lines).strip()
            # else: skip
        else:
            print("\nBio (multi-line, press Ctrl+D or Ctrl+Z when done):")
            print("(or enter a single line and press Enter)")
            bio_lines = []
            try:
                while True:
                    line = input()
                    if line == "" and len(bio_lines) > 0:
                        break
                    bio_lines.append(line)
            except EOFError:
                pass
            artist_data['Bio'] = " ".join(bio_lines).strip()
        if artist_data['Bio']:
            save_progress()
    
    if not artist_data.get('Spotify'):
        artist_data['Spotify link'] = get_input("Spotify link (full URL or just the artist ID)")
        if artist_data['Spotify']:
            save_progress()
    
    if not artist_data.get('Number of People in Act'):
        if ai_data and ai_data.get('band_size'):
            confirm = get_input(f"Band size: {ai_data['band_size']} (press Enter to accept, or type different)", default="accept")
            artist_data['Number of People in Act'] = str(ai_data['band_size']) if confirm == "accept" else confirm
        else:
            artist_data['Number of People in Act'] = get_input("Number of People in Act")
        if artist_data['Number of People in Act']:
            save_progress()
    
    if not artist_data.get('Gender of Front Person'):
        if ai_data and ai_data.get('gender'):
            confirm = get_input(f"Gender: {ai_data['gender']} (press Enter to accept, or type different)", default="accept")
            artist_data['Gender of Front Person'] = ai_data['gender'] if confirm == "accept" else confirm
        else:
            print("\nGender of Front Person:")
            print("  1 = Male")
            print("  2 = Female")
            print("  3 = Non-Binary")
            print("  4 = Band (mixed/no single front person)")
            gender_choice = get_input("Enter number")
            gender_map = {'1': 'Male', '2': 'Female', '3': 'Non-Binary', '4': 'Band'}
            artist_data['Gender of Front Person'] = gender_map.get(gender_choice, '')
        if artist_data['Gender of Front Person']:
            save_progress()
    
    if not artist_data.get('Front Person of Color?'):
        if ai_data and ai_data.get('person_of_color'):
            confirm = get_input(f"Person of Color: {ai_data['person_of_color']} (press Enter to accept, or type y/n)", default="accept")
            if confirm == "accept":
                artist_data['Front Person of Color?'] = ai_data['person_of_color']
            elif confirm.lower() == 'y':
                artist_data['Front Person of Color?'] = 'Yes'
            elif confirm.lower() == 'n':
                artist_data['Front Person of Color?'] = 'No'
        else:
            poc_choice = get_input("Front Person of Color? (y/n)", allow_empty=True)
            if poc_choice.lower() == 'y':
                artist_data['Front Person of Color?'] = 'Yes'
            elif poc_choice.lower() == 'n':
                artist_data['Front Person of Color?'] = 'No'
            else:
                artist_data['Front Person of Color?'] = ''
        if artist_data['Front Person of Color?']:
            save_progress()
    
    # Handle image
    # Check if images already exist in the directory
    existing_images = list(artist_dir.glob('*.jpg')) + list(artist_dir.glob('*.png')) + list(artist_dir.glob('*.jpeg'))
    
    if not artist_data.get('Images Scraped') or artist_data['Images Scraped'] != 'Yes':
        if existing_images:
            print(f"\n✓ Found {len(existing_images)} existing image(s) in {artist_dir.name}")
            for img in existing_images:
                print(f"  - {img.name}")
            mark_scraped = get_input("Mark as scraped? (y/n)", default="y")
            if mark_scraped.lower() == 'y':
                artist_data['Images Scraped'] = 'Yes'
                save_progress()
        
        # If not marked as scraped, offer Spotify or manual input
        if not artist_data.get('Images Scraped') or artist_data['Images Scraped'] != 'Yes':
            # Try to get image from Spotify first
            spotify_image_url = None
            if artist_data.get('Spotify'):
                try_spotify = get_input("Try to get image from Spotify? (y/n)", default="y")
                if try_spotify.lower() == 'y':
                    print(f"  🎵 Scraping Spotify for image...")
                    spotify_image_url = scrape_spotify_image(artist_data['Spotify'])
                    if spotify_image_url:
                        print(f"  ✓ Found Spotify image: {spotify_image_url}")
                        use_spotify_img = get_input("Use this Spotify image? (y/n)", default="y")
                        if use_spotify_img.lower() == 'y':
                            image_filename = f"{artist_name_to_slug(artist_name)}.jpg"
                            image_path = artist_dir / image_filename
                            print(f"  Downloading to {image_path}...")
                            if download_image(spotify_image_url, image_path):
                                print(f"  ✓ Image downloaded successfully")
                                artist_data['Images Scraped'] = 'Yes'
                                save_progress()
                            spotify_image_url = None  # Mark as handled
                    else:
                        print(f"  ⚠️  Could not find Spotify image")
            
            # If no Spotify image or user declined, ask for manual input
            if not artist_data.get('Images Scraped') or artist_data['Images Scraped'] != 'Yes':
                print("\nImage:")
                print("  Enter a URL to download, or")
                print("  Enter a local file path to copy, or")
                print("  Press Enter to skip")
                image_input = get_input("Image").strip()
                
                if image_input:
                    # Determine if URL or local path
                    if image_input.startswith('http://') or image_input.startswith('https://'):
                        # Download from URL
                        image_filename = f"{artist_name_to_slug(artist_name)}.jpg"
                        image_path = artist_dir / image_filename
                        print(f"  Downloading to {image_path}...")
                        if download_image(image_input, image_path):
                            print(f"  ✓ Image downloaded successfully")
                            artist_data['Images Scraped'] = 'Yes'
                            save_progress()
                    else:
                        # Copy local file
                        source_path = Path(image_input).resolve()
                        if source_path.exists():
                            # Keep original extension
                            ext = source_path.suffix or '.jpg'
                            image_filename = f"{artist_name_to_slug(artist_name)}{ext}"
                            image_path = artist_dir / image_filename
                            print(f"  Copying to {image_path}...")
                            if copy_local_image(source_path, image_path):
                                print(f"  ✓ Image copied successfully")
                                artist_data['Images Scraped'] = 'Yes'
                                save_progress()
                        else:
                            print(f"  ❌ File not found: {source_path}")
    
    return artist_data


def main():
    parser = argparse.ArgumentParser(
        description='Manually enrich artist data interactively'
    )
    parser.add_argument(
        '--festival',
        type=str,
        required=True,
        help='Festival slug (e.g., alkmaarse-eigenste)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2026,
        help='Festival year (default: 2026)'
    )
    parser.add_argument(
        '--artist',
        type=str,
        help='Process only this specific artist (optional)'
    )
    
    args = parser.parse_args()
    
    # Get festival config
    try:
        config = get_festival_config(args.festival, args.year)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    
    # Paths
    output_dir = Path(config.output_dir)
    csv_path = output_dir / f"{args.year}.csv"
    artists_dir = output_dir / "artists"
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return 1
    
    artists_dir.mkdir(parents=True, exist_ok=True)
    
    # Read CSV
    print(f"\n=== Manual Artist Enrichment ===")
    print(f"Festival: {config.name}")
    print(f"Year: {args.year}")
    print(f"CSV: {csv_path}")
    print()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        all_artists = list(reader)
    
    # Filter for specific artist if requested
    artists_to_process = all_artists
    if args.artist:
        artists_to_process = [a for a in all_artists if a['Artist'].lower() == args.artist.lower()]
        if not artists_to_process:
            print(f"❌ Artist not found: {args.artist}")
            return 1
    
    # Process each artist
    modified = False
    for i, artist_data in enumerate(artists_to_process, 1):
        artist_name = artist_data['Artist']
        
        # Skip if already complete (all essential fields filled AND images scraped)
        has_data = (
            artist_data.get('Genre') and 
            artist_data.get('Country') and 
            artist_data.get('Bio') and
            artist_data.get('Spotify') and
            artist_data.get('Website') and  # Includes URLs or "HAS_NO_WEBSITE"
            artist_data.get('Images Scraped') == 'Yes'
        )
        
        if has_data:
            print(f"[{i}/{len(artists_to_process)}] {artist_name} - Already complete, skipping")
            continue
        
        print(f"\n[{i}/{len(artists_to_process)}]")
        
        # Process this artist (modifies in place)
        process_artist(artist_data, artists_dir, artist_name, csv_path, all_artists, fieldnames)
        modified = True
        
        print(f"\n✓ All fields saved for {artist_name}")
        
        # Ask if user wants to continue
        if i < len(artists_to_process):
            continue_choice = get_input("\nContinue to next artist? (y/n)", default="y")
            if continue_choice.lower() != 'y':
                print("\n✓ Stopped. Progress has been saved.")
                break
    
    if modified:
        print(f"\n{'='*60}")
        print(f"✓ Artist enrichment complete!")
        print(f"  Updated CSV: {csv_path}")
        print(f"\nNext steps:")
        print(f"  1. Run: python scripts/generate_html.py --festival {args.festival} --year {args.year}")
        print(f"  2. Run: python scripts/generate_artist_pages.py --festival {args.festival} --year {args.year}")
    else:
        print("\n✓ No changes needed - all artists already have data")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
