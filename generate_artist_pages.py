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
from festival_helpers import (
    artist_name_to_slug,
    translate_text,
    FestivalScraper,
    get_festival_config
)
from festival_helpers.slug import get_sort_name


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


def fetch_artist_page_content(artist: Dict, config=None) -> Dict[str, any]:
    """
    Get artist information from CSV (festival data should be pre-fetched).
    Falls back to scraping if CSV data is missing.
    """
    if config is None:
        config = get_festival_config()
    
    artist_name = artist.get('Artist', '')
    slug = artist_name_to_slug(artist_name)
    url = artist.get('Festival URL', '') or config.get_artist_url(slug)
    
    # Try to get data from CSV first (pre-fetched)
    festival_bio_nl = artist.get('Festival Bio (NL)', '').strip()
    festival_bio_en = artist.get('Festival Bio (EN)', '').strip()
    social_links_json = artist.get('Social Links', '').strip()
    
    # Parse social links from JSON
    social_links = []
    if social_links_json:
        try:
            social_links_dict = json.loads(social_links_json)
            social_links = list(social_links_dict.values())
        except json.JSONDecodeError:
            pass
    
    # Check if we need to scrape (fallback for missing data)
    if not festival_bio_nl or not social_links:
        print(f"  ⚠ Missing festival data in CSV, fetching from website...")
        
        try:
            scraper = FestivalScraper(config)
            html = scraper.fetch_artist_page(artist_name)
            
            if html and not festival_bio_nl:
                # Extract bio using scraper
                bio_from_web = scraper.extract_bio(html)
                if bio_from_web:
                    festival_bio_nl = bio_from_web
                    # Translate
                    print(f"  → Translating bio to English...")
                    festival_bio_en = translate_text(festival_bio_nl, "Dutch", "English")
            
            if html and not social_links:
                # Extract social links
                social_links = extract_social_links_from_html(html)
        
        except Exception as e:
            print(f"  ✗ Error fetching from website: {e}")
    
    # Extract image URLs from website (always fetch, as these aren't in CSV yet)
    artist_images = []
    try:
        scraper = FestivalScraper(config)
        html = scraper.fetch_artist_page(artist_name)
        
        if html:
            import re
            srcset_pattern = r'srcset=["\']([^"\']+)["\']'
            all_srcsets = re.findall(srcset_pattern, html)
            
            for img_url in all_srcsets:
                img_lower = img_url.lower()
                
                if 'cache/media_' in img_lower and ('crop_' in img_lower or 'fit_' in img_lower or 'widen_' in img_lower):
                    if any(skip in img_lower for skip in ['rabobank', 'sponsor', 'woordmerk', 'rgb', 'logo']):
                        continue
                    
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = config.base_url.rstrip('/') + img_url
                    
                    if img_url not in artist_images:
                        artist_images.append(img_url)
            
            # Use second image if available
            if len(artist_images) >= 2:
                artist_images = [artist_images[1]]
            elif artist_images:
                artist_images = [artist_images[0]]
    
    except Exception as e:
        print(f"  ✗ Error fetching images: {e}")
    
    # Return consolidated festival content
    return {
        'url': url,
        'festival_bio': festival_bio_nl or festival_bio_en,  # Prefer Dutch, fallback to English
        'festival_bio_nl': festival_bio_nl,
        'festival_bio_en': festival_bio_en,
        'images': artist_images,
        'social_links': social_links,
        'found': bool(festival_bio_nl or festival_bio_en or artist_images or social_links)
    }


def extract_social_links_from_html(html: str) -> list:
    """Extract social media links from festival page HTML."""
    import re
    
    social_links = []
    section_pattern = r'<div[^>]*class="[^"]*border p-8 mt-8[^"]*"[^>]*>(.*?)</div>'
    section_match = re.search(section_pattern, html, re.DOTALL | re.IGNORECASE)
    
    if section_match:
        section_content = section_match.group(1)
        link_pattern = r'<a[^>]*target="_blank"[^>]*href="([^"]+)"[^>]*>'
        potential_links = re.findall(link_pattern, section_content)
        
        for link in potential_links:
            link_lower = link.lower()
            if any(exclude in link_lower for exclude in [
                'dtrh_festival', 'dtrh_fest', 'downtherabbithole',
                'mojo.nl', 'livenation', 'list-manage.com'
            ]):
                continue
            if any(domain in link_lower for domain in [
                'instagram.com', 'youtube.com', 'spotify.com', 
                'facebook.com', 'twitter.com', 'soundcloud.com',
                'bandcamp.com', 'tiktok.com', 'apple.com/music'
            ]) or (link.startswith('http') and 'rabobank' not in link_lower):
                if link not in social_links:
                    social_links.append(link)
    
    return social_links


def generate_artist_page(artist: Dict, year: str, festival_content: Dict, 
                         prev_artist: Optional[Dict] = None, 
                         next_artist: Optional[Dict] = None,
                         config = None) -> str:
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
    social_links = festival_content.get('social_links', [])
    
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
    
    # Create meta description from bio or festival bio
    meta_description = ""
    if bio:
        meta_description = bio[:160] + "..." if len(bio) > 160 else bio
    elif festival_bio_en:
        meta_description = festival_bio_en[:160] + "..." if len(festival_bio_en) > 160 else festival_bio_en
    elif festival_bio_nl:
        meta_description = festival_bio_nl[:160] + "..." if len(festival_bio_nl) > 160 else festival_bio_nl
    else:
        meta_description = f"{artist_name} performing at {config.name} {year}. Explore artist details, genres, and festival information."
    
    # Create keywords from genres and countries
    meta_keywords = f"{artist_name}, {config.name} {year}, " + ", ".join(genres[:5]) if genres else f"{artist_name}, {config.name} {year}"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(artist_name)} - {config.name} {year} - Frank's LineupRadar</title>
    <meta name="description" content="{escape_html(meta_description)}">
    <meta name="keywords" content="{escape_html(meta_keywords)}">
    <meta name="author" content="Frank van Eykelen">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="../../../shared/styles.css">
    <link rel="stylesheet" href="../overrides.css">
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
    else:
        html += """                <div class="section">
                    <h2>Background</h2>
                    <div class="background-text" style="color: #999; font-style: italic;">
                        <p>No information about this artist was found to generate a background.</p>
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
    else:
        html += """                <div class="section">
                    <h2>My Take</h2>
                    <div class="my-take" style="color: #999; font-style: italic;">
                        <p>No information about this artist was found to generate an appraisal.</p>
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
"""
        # Add collapsible Dutch text if available
        if festival_bio_nl:
            html += f"""                    <details style="margin-top: 15px;">
                        <summary style="cursor: pointer; color: #00a8cc; font-weight: 600;">Show original Dutch text</summary>
                        <p style="margin-top: 10px;">{escape_html(festival_bio_nl)}</p>
                    </details>
"""
        html += """                </div>
"""
    # Dutch Bio Section (if no English)
    elif festival_bio_nl:
        html += f"""                <div class="section">
                    <h2>Over (Nederlands)</h2>
                    <p>{escape_html(festival_bio_nl)}</p>
                </div>
"""
    # Festival Bio Section (fallback for old pattern)
    elif festival_bio:
        html += f"""                <div class="section">
                    <h2>About (from Festival)</h2>
                    <p>{escape_html(festival_bio)}</p>
                </div>
"""
    else:
        html += """                <div class="section">
                    <h2>About (from Festival)</h2>
                    <p style="color: #999; font-style: italic;">No information on this artist was found on the festival website.</p>
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
    
    # Festival page first
    html += f'                        <a href="{escape_html(festival_url)}" target="_blank" class="btn btn-info"><i class="bi bi-globe"></i> Festival Page</a>\n'
    
    # Then Spotify from CSV if available
    if spotify_link:
        html += f'                        <a href="{escape_html(spotify_link)}" target="_blank" class="btn btn-success"><i class="bi bi-spotify"></i> Listen on Spotify</a>\n'
    
    # Add social links from festival website
    for link in social_links:
        link_lower = link.lower()
        # Skip Spotify links if we already have one from CSV
        if 'spotify.com' in link_lower and spotify_link:
            continue
        if 'instagram.com' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-primary"><i class="bi bi-instagram"></i> Instagram</a>\n'
        elif 'youtube.com' in link_lower or 'youtu.be' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-danger"><i class="bi bi-youtube"></i> YouTube</a>\n'
        elif 'facebook.com' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-primary"><i class="bi bi-facebook"></i> Facebook</a>\n'
        elif 'twitter.com' in link_lower or 'x.com' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-info"><i class="bi bi-twitter-x"></i> Twitter/X</a>\n'
        elif 'soundcloud.com' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-warning"><i class="bi bi-soundwave"></i> SoundCloud</a>\n'
        elif 'bandcamp.com' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-secondary"><i class="bi bi-disc"></i> Bandcamp</a>\n'
        elif 'tiktok.com' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-dark"><i class="bi bi-tiktok"></i> TikTok</a>\n'
        elif 'apple.com' in link_lower and 'music' in link_lower:
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-secondary"><i class="bi bi-music-note"></i> Apple Music</a>\n'
        else:
            # Generic website link
            html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-outline-secondary"><i class="bi bi-link-45deg"></i> Website</a>\n'
    
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
                    <a href="{config.base_url}" target="_blank" style="color: #00d9ff; text-decoration: none;">{config.name} festival website</a>
                    with AI-generated content using <strong>Azure OpenAI GPT-4o</strong>.
                </p>
                <p style="margin-bottom: 15px;">
                    <strong>⚠️ Disclaimer:</strong> Information may be incomplete or inaccurate due to automated generation and web scraping. 
                    Please verify critical details on official sources.
                </p>
                <p style="margin-bottom: 0;">
                    Generated with ❤️ • 
                    <a href="https://github.com/frankvaneykelen/lineup-radar" target="_blank" style="color: #00d9ff; text-decoration: none;">
                        <i class="bi bi-github"></i> View on GitHub
                    </a>
                </p>
            </div>
        </footer>
    </div>
    <script src="../../../shared/script.js"></script>
    <script src="../overrides.js"></script>
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


def generate_all_artist_pages(csv_file: Path, output_dir: Path, festival: str = 'down-the-rabbit-hole'):
    """Generate individual pages for all artists."""
    # Read CSV data
    artists = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        artists = list(reader)
    
    # Sort artists alphabetically, ignoring "The" prefix
    artists = sorted(artists, key=lambda a: get_sort_name(a.get('Artist', '')))
    
    year = csv_file.stem
    config = get_festival_config(festival, int(year))
    artist_pages_dir = output_dir / festival / year / "artists"
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
            festival_content = fetch_artist_page_content(artist, config)
            
            for img_url in festival_content.get('images', []):
                local_path = download_image(img_url, artist_images_dir, slug)
                if local_path:
                    # Store relative path from artist page to image
                    local_images.append(f"{slug}/{local_path}")
        
        # If we didn't fetch content yet, do it now for bio/description
        if official_images:
            festival_content = fetch_artist_page_content(artist, config)
        
        # Update festival content with local image paths
        festival_content['images'] = local_images
        
        # Get previous and next artists for navigation
        prev_artist = artists[idx - 1] if idx > 0 else None
        next_artist = artists[idx + 1] if idx < len(artists) - 1 else None
        
        # Generate HTML
        html = generate_artist_page(artist, year, festival_content, prev_artist, next_artist, config)
        
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
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate individual HTML pages for each artist"
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
        "--output",
        type=str,
        default="docs",
        help="Output directory (default: docs)"
    )
    
    args = parser.parse_args()
    
    # Get festival config
    config = get_festival_config(args.festival, args.year)
    output_dir = Path(args.output)
    
    # Try multiple locations for CSV file
    csv_locations = [
        Path(f"{args.year}.csv"),  # Root directory
        Path(f"docs/{args.year}/{args.year}.csv"),  # Docs subdirectory
        Path(f"{args.output}/{args.year}/{args.year}.csv")  # Custom output directory
    ]
    
    csv_file = None
    for location in csv_locations:
        if location.exists():
            csv_file = location
            break
    
    if not csv_file:
        print(f"✗ CSV file not found. Tried:")
        for location in csv_locations:
            print(f"  - {location}")
        sys.exit(1)
    
    print(f"\n=== Generating Artist Pages for {config.name} {args.year} ===\n")
    generate_all_artist_pages(csv_file, output_dir, args.festival)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
