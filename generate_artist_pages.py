#!/usr/bin/env python3
"""
Generate individual HTML pages for each artist with detailed information.
Fetches content from festival website including bio/blurb and images.
"""

import csv
import re
import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import urllib.parse
import json
import hashlib
from functools import cmp_to_key
import requests


def artist_name_to_slug(name: str) -> str:
    """Convert artist name to URL slug format for festival website."""
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


def escape_html(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def get_sort_name(artist_name: str) -> str:
    """Get sort name for artist, ignoring 'The' prefix."""
    name = artist_name.strip()
    if name.lower().startswith('the '):
        return name[4:]
    return name


def translate_text(text: str, from_lang: str = "Dutch", to_lang: str = "English") -> str:
    """Translate text using Azure OpenAI."""
    if not text or not text.strip():
        return ""
    
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    if not azure_key or not azure_endpoint:
        print(f"\n✗ ERROR: Azure OpenAI credentials not set!")
        print(f"  Please set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT environment variables")
        print(f"\n  Example:")
        print(f"    $env:AZURE_OPENAI_KEY = \"your-key\"")
        print(f"    $env:AZURE_OPENAI_ENDPOINT = \"https://your-resource.cognitiveservices.azure.com\"")
        print(f"    $env:AZURE_OPENAI_DEPLOYMENT = \"gpt-4o\"")
        sys.exit(1)
    
    endpoint = f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}/chat/completions?api-version=2024-12-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_key
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": f"You are a professional translator. Translate the following text from {from_lang} to {to_lang}. Preserve the tone and style. Return ONLY the translated text, nothing else."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "model": azure_deployment,
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        translated = result["choices"][0]["message"]["content"].strip()
        return translated
    except Exception as e:
        print(f"  ⚠️  Translation failed: {e}")
        return ""


def fetch_artist_page_content(artist_name: str) -> Dict[str, any]:
    """Fetch artist information from festival website."""
    slug = artist_name_to_slug(artist_name)
    url = f"https://downtherabbithole.nl/programma/{slug}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        # Extract Dutch bio from specific div class
        dutch_bio_pattern = r'<div[^>]*class="[^"]*column text-xl font-normal prose !max-w-none[^"]*"[^>]*>(.*?)</div>'
        dutch_bio_match = re.search(dutch_bio_pattern, html, re.DOTALL | re.IGNORECASE)
        festival_bio_nl = dutch_bio_match.group(1).strip() if dutch_bio_match else ""
        
        # Clean up HTML tags from bio but keep basic formatting
        festival_bio_nl = re.sub(r'<br\s*/?>', '\n', festival_bio_nl)
        festival_bio_nl = re.sub(r'<p[^>]*>', '\n', festival_bio_nl)
        festival_bio_nl = re.sub(r'</p>', '\n', festival_bio_nl)
        festival_bio_nl = re.sub(r'<[^>]+>', '', festival_bio_nl)
        festival_bio_nl = re.sub(r'\n\s*\n', '\n\n', festival_bio_nl).strip()
        
        # Also try the old description pattern as fallback
        festival_bio = ""
        if not festival_bio_nl:
            bio_pattern = r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>'
            bio_match = re.search(bio_pattern, html, re.DOTALL | re.IGNORECASE)
            festival_bio = bio_match.group(1).strip() if bio_match else ""
            festival_bio = re.sub(r'<br\s*/?>', '\n', festival_bio)
            festival_bio = re.sub(r'<p[^>]*>', '\n', festival_bio)
            festival_bio = re.sub(r'</p>', '\n', festival_bio)
            festival_bio = re.sub(r'<[^>]+>', '', festival_bio)
            festival_bio = re.sub(r'\n\s*\n', '\n\n', festival_bio).strip()
        
        # Extract image URLs - artist photos are in <picture> tags with srcset
        # Pattern: <source srcset="..." or <img srcset="..."
        srcset_pattern = r'srcset=["\']([^"\']+)["\']'
        all_srcsets = re.findall(srcset_pattern, html)
        
        artist_images = []
        for img_url in all_srcsets:
            img_lower = img_url.lower()
            
            # Look for the specific artist photo pattern
            # These are high-res cropped/fitted images from the festival site
            if 'cache/media_' in img_lower and ('crop_' in img_lower or 'fit_' in img_lower or 'widen_' in img_lower):
                # Skip sponsor/partner logos (they have different naming)
                if any(skip in img_lower for skip in ['rabobank', 'sponsor', 'woordmerk', 'rgb', 'logo']):
                    continue
                
                # Make absolute URLs
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = 'https://downtherabbithole.nl' + img_url
                
                # Avoid duplicates
                if img_url not in artist_images:
                    artist_images.append(img_url)
        
        # Only use the second image (index 1) - first is crop, third is video placeholder
        if len(artist_images) >= 2:
            artist_images = [artist_images[1]]
        elif artist_images:
            # If only one image, keep it
            artist_images = [artist_images[0]]
        else:
            artist_images = []
        
        # Translate Dutch bio to English if present
        festival_bio_en = ""
        if festival_bio_nl:
            print(f"  → Translating bio to English...")
            festival_bio_en = translate_text(festival_bio_nl, "Dutch", "English")
        
        return {
            'url': url,
            'festival_bio': festival_bio,
            'festival_bio_nl': festival_bio_nl,
            'festival_bio_en': festival_bio_en,
            'images': artist_images,
            'found': True
        }
        
    except Exception as e:
        print(f"  ⚠️  Could not fetch page for {artist_name}: {e}")
        return {
            'url': url,
            'festival_bio': '',
            'festival_bio_nl': '',
            'festival_bio_en': '',
            'images': [],
            'found': False
        }


def generate_artist_page(artist: Dict, year: str, festival_content: Dict, 
                         prev_artist: Optional[Dict] = None, 
                         next_artist: Optional[Dict] = None) -> str:
    """Generate HTML page for a single artist."""
    artist_name = artist.get('Artist', '')
    genre = artist.get('Genre', '').strip()
    country = artist.get('Country', '').strip()
    bio = artist.get('Bio', '').strip()
    my_take = artist.get('My take', '').strip()
    my_rating = artist.get('My rating', '').strip()
    spotify_link = artist.get('Spotify link', '').strip()
    num_people = artist.get('Number of People in Act', '').strip()
    gender = artist.get('Gender of Front Person', '').strip()
    poc = artist.get('Front Person of Color?', '').strip()
    
    festival_url = festival_content['url']
    festival_bio = festival_content.get('festival_bio', '')
    festival_bio_nl = festival_content.get('festival_bio_nl', '')
    festival_bio_en = festival_content.get('festival_bio_en', '')
    images = festival_content['images']
    
    # Process genres and countries into badges
    genres = [g.strip() for g in genre.split('/')] if genre else []
    countries = [c.strip() for c in country.split('/')] if country else []
    
    # Gender emoji mapping
    gender_emoji_map = {
        'Male': '♂️',
        'Female': '♀️',
        'Mixed': '⚤',
        'Non-binary': '⚧️'
    }
    gender_display = gender_emoji_map.get(gender, gender)
    
    # Generate previous/next links for header
    if prev_artist:
        prev_slug = artist_name_to_slug(prev_artist.get('Artist', ''))
        prev_link = f'<a href="{prev_slug}.html" class="btn btn-outline-light" title="{escape_html(prev_artist.get("Artist", ""))}"><i class="bi bi-chevron-left"></i> Prev</a>'
        prev_link_footer = f'<a href="{prev_slug}.html" class="btn btn-primary" title="{escape_html(prev_artist.get("Artist", ""))}"><i class="bi bi-chevron-left"></i> Prev</a>'
    else:
        prev_link = '<button class="btn btn-outline-light" disabled><i class="bi bi-chevron-left"></i> Prev</button>'
        prev_link_footer = '<button class="btn btn-primary" disabled><i class="bi bi-chevron-left"></i> Prev</button>'
    
    if next_artist:
        next_slug = artist_name_to_slug(next_artist.get('Artist', ''))
        next_link = f'<a href="{next_slug}.html" class="btn btn-outline-light" title="{escape_html(next_artist.get("Artist", ""))}">Next <i class="bi bi-chevron-right"></i></a>'
        next_link_footer = f'<a href="{next_slug}.html" class="btn btn-primary" title="{escape_html(next_artist.get("Artist", ""))}">Next <i class="bi bi-chevron-right"></i></a>'
    else:
        next_link = '<button class="btn btn-outline-light" disabled>Next <i class="bi bi-chevron-right"></i></button>'
        next_link_footer = '<button class="btn btn-primary" disabled>Next <i class="bi bi-chevron-right"></i></button>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(artist_name)} - Down The Rabbit Hole {year}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <div class="container-fluid">
        <div class="artist-header">
            <a href="../index.html" class="btn btn-outline-light home-btn" title="Back to Lineup">
                <i class="bi bi-house-door-fill"></i>
            </a>
            <div class="artist-header-content">
                <h1>{escape_html(artist_name)}</h1>
                <div class="badges d-flex flex-wrap gap-2">
"""
    
    # Add genre badges
    for g in genres:
        html += f'                    <span class="badge rounded-pill bg-info text-dark">{escape_html(g)}</span>\n'
    
    # Add country badges
    for c in countries:
        html += f'                    <span class="badge rounded-pill bg-primary">{escape_html(c)}</span>\n'
    
    html += f"""                </div>
            </div>
            <div class="artist-nav d-flex gap-2">
                {prev_link}
                {next_link}
            </div>
        </div>
        
        <div class="artist-content container-fluid">
            <div class="row g-4">
                <div class="col-auto left-column" style="width: 670px;">
"""
    
    # LEFT COLUMN: Hero Image/Carousel, Background, My Take
    
    # Hero Image Section or Carousel
    if images:
        if len(images) == 1:
            # Single image - display as before
            img_url = images[0]
            html += f"""                <div class="hero-image">
                    <img src="{escape_html(img_url)}" alt="{escape_html(artist_name)}" loading="lazy">
                </div>
"""
        else:
            # Multiple images - create Bootstrap carousel
            carousel_id = f"carousel-{escape_html(artist_name_to_slug(artist_name))}"
            html += f"""                <div id="{carousel_id}" class="carousel slide hero-image" data-bs-ride="carousel">
                    <div class="carousel-indicators">
"""
            for i in range(len(images)):
                active = "active" if i == 0 else ""
                html += f"""                        <button type="button" data-bs-target="#{carousel_id}" data-bs-slide-to="{i}" class="{active}" aria-current="{'true' if i == 0 else 'false'}" aria-label="Slide {i + 1}"></button>
"""
            html += """                    </div>
                    <div class="carousel-inner">
"""
            for i, img_url in enumerate(images):
                active = "active" if i == 0 else ""
                html += f"""                        <div class="carousel-item {active}">
                            <img src="{escape_html(img_url)}" class="d-block w-100" alt="{escape_html(artist_name)} - Image {i + 1}" loading="lazy">
                        </div>
"""
            html += f"""                    </div>
                    <button class="carousel-control-prev" type="button" data-bs-target="#{carousel_id}" data-bs-slide="prev">
                        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Previous</span>
                    </button>
                    <button class="carousel-control-next" type="button" data-bs-target="#{carousel_id}" data-bs-slide="next">
                        <span class="carousel-control-next-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Next</span>
                    </button>
                </div>
"""
    
    # AI-generated Bio Section
    if bio:
        html += f"""                <div class="section">
                    <h2>Background</h2>
                    <div class="background-text">
                        <p>{escape_html(bio)}</p>
                    </div>
                </div>
"""
    
    # My Take Section
    if my_take:
        html += f"""                <div class="section">
                    <h2>My Take</h2>
                    <div class="my-take">
                        <p>{escape_html(my_take)}</p>
                    </div>
                </div>
"""
    
    html += """                </div>
                
                <div class="col right-column">
"""
    
    # RIGHT COLUMN: Festival Bio, Rating, Details, Links
    
    # English Translation of Festival Bio (primary)
    if festival_bio_en:
        html += f"""                <div class="section">
                    <h2>About (from Festival)</h2>
                    <p>{escape_html(festival_bio_en)}</p>
                </div>
"""
    
    # Dutch Bio Section (collapsible/secondary)
    if festival_bio_nl:
        html += f"""                <div class="section">
                    <h2>Over (Nederlands)</h2>
                    <details>
                        <summary style="cursor: pointer; color: #00a8cc; font-weight: 600;">Show original Dutch text</summary>
                        <p style="margin-top: 10px;">{escape_html(festival_bio_nl)}</p>
                    </details>
                </div>
"""
    
    # Festival Bio Section (fallback for old pattern)
    if festival_bio and not festival_bio_nl and not festival_bio_en:
        html += f"""                <div class="section">
                    <h2>About (from Festival)</h2>
                    <p>{escape_html(festival_bio)}</p>
                </div>
"""
    
    # Rating Section
    if my_rating:
        html += f"""                <div class="section">
                    <h2>My Rating</h2>
                    <span class="badge bg-gradient fs-4 px-4 py-2 my-rating">{escape_html(my_rating)}</span>
                </div>
"""
    
    # Info Grid
    html += """                <div class="section">
                    <h2>Details</h2>
                    <div class="row g-3">
"""
    
    if num_people:
        html += f"""                        <div class="col-md-6">
                            <div class="card border-info">
                                <div class="card-body">
                                    <h6 class="card-subtitle mb-2 text-muted">Number in Act</h6>
                                    <p class="card-text fs-5 fw-bold">{escape_html(num_people)}</p>
                                </div>
                            </div>
                        </div>
"""
    
    if gender:
        html += f"""                        <div class="col-md-6">
                            <div class="card border-info">
                                <div class="card-body">
                                    <h6 class="card-subtitle mb-2 text-muted">Front Person Gender</h6>
                                    <p class="card-text fs-5">{gender_display} {escape_html(gender)}</p>
                                </div>
                            </div>
                        </div>
"""
    
    if poc:
        html += f"""                        <div class="col-md-6">
                            <div class="card border-info">
                                <div class="card-body">
                                    <h6 class="card-subtitle mb-2 text-muted">Front Person of Color</h6>
                                    <p class="card-text fs-5">{escape_html(poc)}</p>
                                </div>
                            </div>
                        </div>
"""
    
    html += """                    </div>
                </div>
"""
    
    # Links Section
    html += """                <div class="section">
                    <h2>Links</h2>
                    <div class="d-flex gap-2 flex-wrap">
"""
    
    if spotify_link:
        html += f'                        <a href="{escape_html(spotify_link)}" target="_blank" class="btn btn-success"><i class="bi bi-spotify"></i> Listen on Spotify</a>\n'
    
    html += f'                        <a href="{escape_html(festival_url)}" target="_blank" class="btn btn-info"><i class="bi bi-globe"></i> Festival Page</a>\n'
    
    html += """                    </div>
                </div>
                </div>
            </div>
        </div>
        
        <div class="artist-nav-footer d-flex justify-content-between align-items-center" style="padding: 20px; background: #f8f9fa; border-top: 1px solid #dee2e6;">
"""
    
    html += f'            {prev_link_footer}\n'
    
    html += f'            {next_link_footer}\n'
    
    html += """        </div>
        
        <footer style="background: #1a1a2e; color: #ccc; padding: 30px 20px; text-align: center; font-size: 0.9em;">
            <button class="dark-mode-toggle" id="darkModeToggle" title="Toggle dark mode">
                <i class="bi bi-moon-fill"></i>
            </button>
            <div>
                <p style="margin-bottom: 15px;">
                    <strong>Content Notice:</strong> These pages combine content scraped from the 
                    <a href="https://downtherabbithole.nl" target="_blank" style="color: #00d9ff; text-decoration: none;">Down The Rabbit Hole festival website</a>
                    with AI-generated content using <strong>Azure OpenAI GPT-4o</strong>.
                </p>
                <p style="margin-bottom: 15px;">
                    <strong>⚠️ Disclaimer:</strong> Information may be incomplete or inaccurate due to automated generation and web scraping. 
                    Please verify critical details on official sources.
                </p>
                <p style="margin-bottom: 0;">
                    Generated with ❤️ • 
                    <a href="https://github.com/frankvaneykelen/down-the-rabbit-hole" target="_blank" style="color: #00d9ff; text-decoration: none;">
                        <i class="bi bi-github"></i> View on GitHub
                    </a>
                </p>
            </div>
        </footer>
    </div>
    <script src="../script.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    
    return html


def download_image(img_url: str, output_dir: Path, artist_slug: str) -> Optional[str]:
    """Download an image and save it locally. Returns the local path or None if failed."""
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
            print(f"    Downloading: {filename}")
            req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                img_data = response.read()
            
            with open(local_path, 'wb') as f:
                f.write(img_data)
        
        # Return relative path for HTML
        return filename
        
    except Exception as e:
        print(f"    ⚠️  Failed to download image: {e}")
        return None


def generate_all_artist_pages(csv_file: Path, output_dir: Path):
    """Generate individual pages for all artists."""
    # Read CSV data
    artists = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        artists = list(reader)
    
    # Sort artists alphabetically, ignoring "The" prefix
    artists = sorted(artists, key=lambda a: get_sort_name(a.get('Artist', '')))
    
    year = csv_file.stem
    artist_pages_dir = output_dir / year / "artists"
    artist_pages_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== Generating Individual Artist Pages ===\n")
    print(f"Processing {len(artists)} artists...\n")
    
    for idx, artist in enumerate(artists):
        artist_name = artist.get('Artist', '').strip()
        if not artist_name:
            continue
        
        print(f"[{idx+1}/{len(artists)}] {artist_name}...")
        
        # Download images and update paths
        local_images = []
        slug = artist_name_to_slug(artist_name)
        
        # Create artist-specific image directory
        artist_images_dir = artist_pages_dir / slug
        artist_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if images already exist locally (official + any manually added)
        official_images = list(artist_images_dir.glob(f"{slug}_*"))
        all_images = [f for f in artist_images_dir.glob("*") if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
        
        if official_images:
            # Use all images found in the directory
            print(f"  ✓ Using cached images ({len(all_images)} found)")
            for img_path in sorted(all_images):
                local_images.append(f"{slug}/{img_path.name}")
        else:
            # Fetch festival content only if we need to download images
            print(f"  → Fetching from website...")
            festival_content = fetch_artist_page_content(artist_name)
            
            for img_url in festival_content.get('images', []):
                local_path = download_image(img_url, artist_images_dir, slug)
                if local_path:
                    # Store relative path from artist page to image
                    local_images.append(f"{slug}/{local_path}")
        
        # If we didn't fetch content yet, do it now for bio/description
        if official_images:
            festival_content = fetch_artist_page_content(artist_name)
        
        # Update festival content with local image paths
        festival_content['images'] = local_images
        
        # Get previous and next artists for navigation
        prev_artist = artists[idx - 1] if idx > 0 else None
        next_artist = artists[idx + 1] if idx < len(artists) - 1 else None
        
        # Generate HTML
        html = generate_artist_page(artist, year, festival_content, prev_artist, next_artist)
        
        # Save file
        slug = artist_name_to_slug(artist_name)
        output_file = artist_pages_dir / f"{slug}.html"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  ✓ Saved: {output_file}")
        
        # Be nice to the server
        time.sleep(0.5)
    
    print(f"\n✓ Generated {len(artists)} artist pages")
    print(f"  Output directory: {artist_pages_dir}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_artist_pages.py <csv_file> [output_dir]")
        print("Example: python generate_artist_pages.py 2026.csv docs")
        sys.exit(1)
    
    csv_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("docs")
    
    if not csv_file.exists():
        print(f"✗ CSV file not found: {csv_file}")
        sys.exit(1)
    
    generate_all_artist_pages(csv_file, output_dir)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
