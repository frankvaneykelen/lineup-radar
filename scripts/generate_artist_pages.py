#!/usr/bin/env python3
"""
Generate individual HTML pages for each artist with detailed information.
Fetches content from festival website including bio/blurb and images.
"""

import sys
from pathlib import Path

# Add scripts directory to path for helpers module
import sys
sys.path.insert(0, str(Path(__file__).parent))

import csv
import re
import time
import os
from typing import Dict, List, Optional
import urllib.request
import urllib.parse
import json
import hashlib
from functools import cmp_to_key
import requests
from helpers import (
    artist_name_to_slug,
    translate_text,
    FestivalScraper,
    get_festival_config,
    generate_hamburger_menu
)
from helpers.slug import get_sort_name


def get_spotify_artist_image(artist_name: str) -> Optional[str]:
    """
    Fetch artist image from Spotify API as fallback when no festival images found.
    Uses public Spotify search endpoint without authentication.
    
    Args:
        artist_name: Name of the artist to search for
        
    Returns:
        URL of the largest artist image, or None if not found
    """
    try:
        # URL-encode the artist name for the search query
        query = urllib.parse.quote(artist_name)
        url = f"https://api.spotify.com/v1/search?q={query}&type=artist&limit=1"
        
        # Create request with timeout
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Fetch and parse response
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            artists = data.get('artists', {}).get('items', [])
            
            # Return largest image (first in array) if available
            if artists and artists[0].get('images'):
                images = artists[0]['images']
                if images:
                    return images[0]['url']
    except Exception as e:
        # Silently fail - this is a fallback mechanism
        pass
    
    return None


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
    Get artist information from CSV (festival data should be pre-fetched by fetch_festival_data.py).
    Does NOT scrape - that should be done by fetch_festival_data.py.
    """
    if config is None:
        config = get_festival_config()
    
    artist_name = artist.get('Artist', '')
    slug = artist_name_to_slug(artist_name)
    url = artist.get('Festival URL', '') or config.get_artist_url(slug)
    
    # Get data from CSV (pre-fetched by fetch_festival_data.py)
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
    
    # Images should be downloaded by fetch_festival_data.py
    # We'll find them from disk later in generate_all_artist_pages()
    artist_images = []
    
    # Return consolidated festival content
    return {
        'url': url,
        'festival_bio': festival_bio_nl or festival_bio_en,  # Prefer Dutch, fallback to English
        'festival_bio_nl': festival_bio_nl,
        'festival_bio_en': festival_bio_en,
        'images': artist_images,  # Will be populated from disk
        'social_links': social_links,
        'found': bool(festival_bio_nl or festival_bio_en or social_links)
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
    ai_summary = artist.get('AI Summary', '').strip()
    ai_rating = artist.get('AI Rating', '').strip()
    spotify_link = artist.get('Spotify Link', '').strip()
    num_people = artist.get('Number of People in Act', '').strip()
    gender_raw = artist.get('Gender of Front Person', '').strip().lower()
    # Tagline fallback logic: always provide a tagline
    tagline = artist.get('Tagline', '').strip()
    if not tagline:
        if bio:
            match = re.match(r'(.+?[.!?])\s', bio)
            if match:
                tagline = match.group(1).strip()
            else:
                tagline = bio[:120].strip()
        else:
            tagline = ''
    """Generate HTML page for a single artist."""
    artist_name = artist.get('Artist', '')
    genre = artist.get('Genre', '').strip()
    country = artist.get('Country', '').strip()
    bio = artist.get('Bio', '').strip()
    ai_summary = artist.get('AI Summary', '').strip()
    ai_rating = artist.get('AI Rating', '').strip()
    spotify_link = artist.get('Spotify Link', '').strip()
    num_people = artist.get('Number of People in Act', '').strip()
    gender_raw = artist.get('Gender of Front Person', '').strip().lower()
    # Normalize gender values
    gender_map = {
        'male': 'Male',
        'man': 'Male',
        'he': 'Male',
        'him': 'Male',
        'm': 'Male',
        'female': 'Female',
        'woman': 'Female',
        'she': 'Female',
        'her': 'Female',
        'f': 'Female',
        'non-binary': 'Non-binary',
        'nonbinary': 'Non-binary',
        'nb': 'Non-binary',
        'enby': 'Non-binary',
        'mixed': 'Mixed',
        'group': 'Mixed',
        'various': 'Mixed',
        'unknown': 'Unknown',
        '': ''
    }
    gender = gender_map.get(gender_raw, gender_raw.capitalize() if gender_raw else '')
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
    gender_emoji = gender_emoji_map.get(gender, '')
    gender_display = f"{gender_emoji} {gender}" if gender_emoji else gender
    
    # Generate previous/next links for header (with data attributes for keyboard navigation)
    if prev_artist:
        prev_slug = artist_name_to_slug(prev_artist.get('Artist', ''))
        prev_link = f'<a href="{prev_slug}.html" class="btn btn-outline-light" data-nav-prev="{prev_slug}.html" title="{escape_html(prev_artist.get("Artist", ""))}"><i class="bi bi-chevron-left"></i> Prev</a>'
        prev_link_footer = f'<a href="{prev_slug}.html" class="btn btn-primary" data-nav-prev="{prev_slug}.html" title="{escape_html(prev_artist.get("Artist", ""))}"><i class="bi bi-chevron-left"></i> Prev</a>'
    else:
        prev_link = '<button class="btn btn-outline-light" disabled><i class="bi bi-chevron-left"></i> Prev</button>'
        prev_link_footer = '<button class="btn btn-primary" disabled><i class="bi bi-chevron-left"></i> Prev</button>'
    
    if next_artist:
        next_slug = artist_name_to_slug(next_artist.get('Artist', ''))
        next_link = f'<a href="{next_slug}.html" class="btn btn-outline-light" data-nav-next="{next_slug}.html" title="{escape_html(next_artist.get("Artist", ""))}">Next <i class="bi bi-chevron-right"></i></a>'
        next_link_footer = f'<a href="{next_slug}.html" class="btn btn-primary" data-nav-next="{next_slug}.html" title="{escape_html(next_artist.get("Artist", ""))}">Next <i class="bi bi-chevron-right"></i></a>'
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
    title = f"{escape_html(artist_name)} - {config.name} {year} - Frank's LineupRadar"
    url = f"https://frankvaneykelen.github.io/lineup-radar/{config.slug}/{year}/artists/{artist_name_to_slug(artist_name)}.html"
    base_url = f"https://frankvaneykelen.github.io/lineup-radar/{config.slug}/{year}/artists/"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{escape_html(meta_description)}">
    <meta name="keywords" content="{escape_html(meta_keywords)}">
    <meta name="author" content="Frank van Eykelen">
    <link rel="icon" type="image/png" sizes="16x16" href="../../../shared/favicon_16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="../../../shared/favicon_32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="../../../shared/favicon_48x48.png">
    <link rel="apple-touch-icon" sizes="180x180" href="../../../shared/favicon_180x180.png">
    
    <!-- PWA Manifest -->
    <link rel="manifest" href="../../../manifest.json">
    <meta name="theme-color" content="#00d9ff">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="LineupRadar">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="../../../shared/styles.css">
    <link rel="stylesheet" href="../overrides.css">

    <!-- Open Graph (Facebook, LinkedIn) -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{base_url}{get_hero_image(images)}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{meta_description}">
    <meta name="twitter:image" content="{base_url}{get_hero_image(images)}">

    <!-- Canonical URL -->
    <link rel="canonical" href="{url}">

    <!-- Structured Data: MusicGroup -->
    <script type="application/ld+json">
{json.dumps({
    "@context": "https://schema.org",
    "@type": "MusicGroup",
    "name": artist_name,
    "url": url,
    "image": [base_url + img for img in images] if images else [],
    "description": meta_description,
    "genre": genres,
    "foundingLocation": {
        "@type": "Country",
        "name": countries[0] if countries else ""
    },
    "sameAs": social_links,
    "numberOfMembers": num_people if num_people else None,
    "member": [],
    "award": [],
    "album": [],
    "track": []
}, ensure_ascii=False, indent=4)}
    </script>
</head>
<body>
    <div class="container-fluid">
        <div class="artist-header">
            <div class="hamburger-menu">
                <button id="hamburgerBtn" class="btn btn-outline-light hamburger-btn" title="Menu">
                    <i class="bi bi-list"></i>
                </button>
                <div id="dropdownMenu" class="dropdown-menu-custom">
                    <a href="../../../index.html" class="home-link">
                        <i class="bi bi-house-door-fill"></i> Home
                    </a>
                    <a href="../index.html">
                        <i class="bi bi-arrow-left"></i> Back to Lineup
                    </a>
{generate_hamburger_menu(path_prefix="../../../")}
                </div>
            </div>
            <div class="artist-header-content">
                <h1>{escape_html(artist_name)} <span class="opacity-50">@ <a href="../index.html" style="color: inherit; text-decoration: none;">{config.name} {year}</a></span></h1>
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
                <div class="col-auto image-column" style="width: 450px;">
"""
    
    # IMAGE COLUMN: Hero Image/Carousel only
    
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
    else:
        # No images - show default logo
        html += f"""                <div class="hero-image">
                    <img src="../../../shared/lineup-radar-logo.png" alt="LineupRadar Logo" loading="lazy">
                </div>
"""
    
    html += """                </div>
                
                <div class="col ai-column">
"""
    
    # AI COLUMN: Bio, AI Summary, AI Rating
    
    # AI-generated Bio Section
    if bio:
        # Check if bio starts with the festival bio disclaimer
        disclaimer = "[using festival bio due to a lack of publicly available data] "
        if bio.startswith(disclaimer):
            bio_text = bio[len(disclaimer):]
            html += f"""                <div>
                    <h2>Bio</h2>
                    <p class="mb-2"><small class="fst-italic"><i class="bi bi-info-circle-fill"></i> Using festival bio due to a lack of publicly available data</small></p>
                    <p>{escape_html(bio_text)}</p>
                </div>
"""
        else:
            html += f"""                <div>
                    <h2>Bio</h2>
                    <p>{escape_html(bio)}</p>
                </div>
"""
    else:
        html += f"""                <div>
                    <h2>Bio</h2>
                    <p>There is no information about this artist yet. If you can supply this information, please 
                        <a href="https://github.com/frankvaneykelen/lineup-radar/issues/new?title=Artist%20Info:%20{urllib.parse.quote(artist_name)}" target="_blank" style="color: #00a8cc;">create an issue on the repo</a> with the relevant information like, in any language you like:</p>
                    <ul>
                        <li>Bio/background information</li>
                        <li>Official website / Instagram</li>
                        <li>Spotify artist link</li>
                        <li>Genres</li>
                    </ul>
                </div>
"""
    
    # AI Rating Section
    if ai_rating:
        html += f"""                <div>
                    <h2>AI Rating</h2>
                    <span class="badge bg-gradient fs-4 px-4 py-2 my-rating">{escape_html(ai_rating)}</span>
                </div>
"""
    
    # AI Summary Section
    if ai_summary:
        html += f"""                <div>
                    <h2>AI Summary</h2>
                    <p>{escape_html(ai_summary)}</p>
                </div>
"""
    
    html += """                </div>
                
                <div class="col festival-column">
"""
        
    # FESTIVAL COLUMN: Festival Bio, Details, Links
    # Only show festival_bio_en if not duplicating the AI bio disclaimer
    show_festival_bio = True
    disclaimer = "[using festival bio due to a lack of publicly available data] "
    if bio and bio.startswith(disclaimer):
        show_festival_bio = False

    if festival_bio_en and show_festival_bio:
        html += f"""                <div>
                    <h2>Festival Bio (English)</h2>
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
    # Dutch Bio Section (if no English or not showing English)
    elif festival_bio_nl and show_festival_bio:
        html += f"""                <div>
                    <h2>Festival Bio (Nederlands)</h2>
                    <p>{escape_html(festival_bio_nl)}</p>
                </div>
"""
    # # Festival Bio Section (fallback for old pattern)
    # elif festival_bio:
    #     html += f"""                <div>
    #                 <h2>Festival Bio</h2>
    #                 <p>{escape_html(festival_bio)}</p>
    #             </div>
# """
    
    # Info Grid - only show if there's data to display
    if num_people or gender or poc:
        html += """                <div>
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
                                    <p class="card-text fs-5">{escape_html(gender_display)}</p>
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
    html += """                <div>
                    <h2>Links</h2>
"""
    
    # Collect all available links
    has_links = False
    links_html = ""

    # Festival page first (only if URL exists)
    if festival_url and festival_url.strip():
        links_html += f'                        <a href="{escape_html(festival_url)}" target="_blank" class="btn btn-info"><i class="bi bi-globe"></i> Festival Page</a>\n'
        has_links = True

    # Then Spotify from CSV if available
    if spotify_link and spotify_link != "NOT ON SPOTIFY":
        links_html += f'                        <a href="{escape_html(spotify_link)}" target="_blank" class="btn btn-success"><i class="bi bi-spotify"></i> Listen on Spotify</a>\n'
        has_links = True

    # Add Website from CSV if present and not already in social_links
    website = artist.get('Website', '').strip()
    if website and website.lower() not in [s.lower() for s in social_links]:
        links_html += f'                        <a href="{escape_html(website)}" target="_blank" class="btn btn-info"><i class="bi bi-link-45deg"></i> Website</a>\n'
        has_links = True

    # Add social links from festival website
    for link in social_links:
        link_lower = link.lower()
        # Skip Spotify links - they're already shown separately above
        if 'spotify.com' in link_lower:
            continue
        # Skip Website if it's the same as the CSV Website
        if website and link_lower == website.lower():
            continue
        if 'instagram.com' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-primary"><i class="bi bi-instagram"></i> Instagram</a>\n'
        elif 'youtube.com' in link_lower or 'youtu.be' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-danger"><i class="bi bi-youtube"></i> YouTube</a>\n'
        elif 'facebook.com' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-primary"><i class="bi bi-facebook"></i> Facebook</a>\n'
        elif 'twitter.com' in link_lower or 'x.com' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-info"><i class="bi bi-twitter-x"></i> Twitter/X</a>\n'
        elif 'soundcloud.com' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-warning"><i class="bi bi-soundwave"></i> SoundCloud</a>\n'
        elif 'bandcamp.com' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-light"><i class="bi bi-disc"></i> Bandcamp</a>\n'
        elif 'tiktok.com' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-dark"><i class="bi bi-tiktok"></i> TikTok</a>\n'
        elif 'apple.com' in link_lower and 'music' in link_lower:
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-light"><i class="bi bi-music-note"></i> Apple Music</a>\n'
        else:
            # Generic website link
            links_html += f'                        <a href="{escape_html(link)}" target="_blank" class="btn btn-light"><i class="bi bi-link-45deg"></i> Website</a>\n'
        has_links = True

    if has_links:
        html += """                    <div class="d-flex gap-2 flex-wrap">
"""
        html += links_html
        html += """                    </div>
"""
    else:
        html += f"""                    <p>No links are available for this artist yet. If you can help, please 
                        <a href=\"https://github.com/frankvaneykelen/lineup-radar/issues/new?title=Artist%20Links:%20{urllib.parse.quote(artist_name)}\" target=\"_blank\" style=\"color: #00a8cc;\">create an issue on the repo</a> with links like:</p>
                    <ul>
                        <li>Official website</li>
                        <li>Spotify artist link</li>
                        <li>Instagram / Facebook / Twitter</li>
                        <li>YouTube / SoundCloud / Bandcamp</li>
                    </ul>
"""
    
    html += """                </div>
                </div>
            </div>
        </div>
        
        <div class="artist-nav-footer d-flex justify-content-between align-items-center" style="padding: 20px; background: #f8f9fa; border-top: 1px solid #dee2e6;">
"""
    
    html += f'            {prev_link_footer}\n'
    
    html += f'            {next_link_footer}\n'
    
    html += f"""        </div>
        
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
    <script defer src="https://frankvaneykelen-umami-app.azurewebsites.net/script.js" data-website-id="c10bb9a5-e39d-4286-a3d9-7c3ca9171d51"></script>
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

def get_hero_image(images, fallback="../../../shared/lineup-radar-logo.png"):
    """Return the best hero image for an artist page (for display and og:image)."""
    if images and len(images) > 0:
        return images[0]
    return fallback

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
    
    print(f"\n=== Generating Individual Artist Pages ===\n", flush=True)
    print(f"Processing {len(artists)} artists...\n", flush=True)
    
    for idx, artist in enumerate(artists):
        artist_name = artist.get('Artist', '').strip()
        if not artist_name:
            continue
        
        print(f"[{idx+1}/{len(artists)}] {artist_name}...", flush=True)
        
        # Download images and update paths
        local_images = []
        slug = artist_name_to_slug(artist_name)
        
        # Create artist-specific image directory
        artist_images_dir = artist_pages_dir / slug
        artist_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if images already exist locally (official + any manually added)
        official_images = list(artist_images_dir.glob(f"{slug}_*"))
        all_images = [f for f in artist_images_dir.glob("*") if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
        
        # Check if festival has individual artist pages
        has_artist_pages = bool(config.artist_path)
        
        # Check if we have any images (official or manually added)
        if all_images:
            # Use all images found in the directory (official scraped + manually added)
            print(f"  ✓ Using cached images ({len(all_images)} found)", flush=True)
            for img_path in sorted(all_images):
                local_images.append(f"{slug}/{img_path.name}")
            # Fetch content for bio/description only if festival has artist pages
            if has_artist_pages:
                festival_content = fetch_artist_page_content(artist, config)
            else:
                # Use CSV data directly for festivals without artist pages
                festival_content = {
                    'images': [],
                    'social_links': [],
                    'url': '',
                    'festival_bio_nl': artist.get('Festival Bio (NL)', '').strip(),
                    'festival_bio_en': artist.get('Festival Bio (EN)', '').strip()
                }
        else:
            # No images locally
            if has_artist_pages:
                # Try to fetch from website
                print(f"  → No cached images found, fetching from website...", flush=True)
                festival_content = fetch_artist_page_content(artist, config)
                
                for img_url in festival_content.get('images', []):
                    local_path = download_image(img_url, artist_images_dir, slug)
                    if local_path:
                        # Store relative path from artist page to image
                        local_images.append(f"{slug}/{local_path}")
                if local_images:
                    print(f"  ✓ Downloaded {len(local_images)} image(s)", flush=True)
            else:
                # Festival has no artist pages - use CSV data only
                print(f"  ℹ️  No images (festival has no artist pages - use search_artist_images.py)", flush=True)
                festival_content = {
                    'images': [],
                    'social_links': [],
                    'url': '',
                    'festival_bio_nl': artist.get('Festival Bio (NL)', '').strip(),
                    'festival_bio_en': artist.get('Festival Bio (EN)', '').strip()
                }
        
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
        
        print(f"  ✓ Saved: {output_file}", flush=True)
        
        # Be nice to the server
        time.sleep(0.5)
    
    print(f"\n✓ Generated {len(artists)} artist pages", flush=True)
    print(f"  Output directory: {artist_pages_dir}", flush=True)


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
    
    # Try multiple locations for CSV file (festival-specific paths)
    csv_locations = [
        Path(f"docs/{config.slug}/{args.year}/{args.year}.csv"),  # Docs location (primary)
        Path(f"{config.slug}/{args.year}.csv"),  # Festival directory (legacy)
        Path(f"{args.year}.csv"),  # Legacy root directory (for down-the-rabbit-hole)
        Path(f"docs/{args.year}/{args.year}.csv"),  # Docs subdirectory (legacy)
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
    
    print(f"\n=== Generating Artist Pages for {config.name} {args.year} ===\n", flush=True)
    generate_all_artist_pages(csv_file, output_dir, args.festival)
    print("\n✓ Done!", flush=True)


if __name__ == "__main__":
    main()
