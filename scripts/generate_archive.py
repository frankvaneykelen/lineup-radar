#!/usr/bin/env python3
"""
Generate the archive page (docs/archive.html).
This page lists all archived festivals grouped by year.
"""

import sys
import json
from pathlib import Path
from typing import List
from datetime import datetime
from itertools import groupby

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from helpers.config import get_festival_config, FESTIVALS
from helpers.menu import generate_hamburger_menu


def find_archived_festivals(docs_dir: Path) -> List[dict]:
    """Find all archived festival lineups."""
    lineups = []
    
    # Look for festival/year/index.html structure
    for festival_dir in docs_dir.iterdir():
        if festival_dir.is_dir() and not festival_dir.name.startswith('.'):
            for year_dir in festival_dir.iterdir():
                if year_dir.is_dir() and year_dir.name.isdigit():
                    settings_json = year_dir / "settings.json"
                    
                    # Check if festival is archived
                    try:
                        if settings_json.exists():
                            with open(settings_json, 'r', encoding='utf-8') as f:
                                settings_data = json.load(f)
                                if not settings_data.get('archived', False):
                                    continue  # Skip non-archived festivals
                        else:
                            continue  # Skip if no settings.json
                    except (OSError, json.JSONDecodeError):
                        continue
                    
                    if (year_dir / "index.html").exists():
                        # Read additional data from settings.json
                        start_date = None
                        end_date = None
                        description = ""
                        
                        try:
                            with open(settings_json, 'r', encoding='utf-8') as f:
                                settings_data = json.load(f)
                                start_date = settings_data.get('start_date')
                                end_date = settings_data.get('end_date')
                                description = settings_data.get('description', '')
                        except:
                            pass
                        
                        # Read tagline from about.json if available
                        tagline = description
                        about_json = year_dir / "about.json"
                        try:
                            if about_json.exists():
                                with open(about_json, 'r', encoding='utf-8') as f:
                                    about_data = json.load(f)
                                    if about_data.get('tagline'):
                                        tagline = about_data['tagline']
                        except:
                            pass
                        
                        lineups.append({
                            'festival': festival_dir.name,
                            'year': year_dir.name,
                            'path': f"{festival_dir.name}/{year_dir.name}/index.html",
                            'start_date': start_date,
                            'end_date': end_date,
                            'tagline': tagline
                        })
    
    # Sort by year (descending), then by start_date (descending), then by festival name
    def sort_key(lineup):
        year = int(lineup['year'])
        # If no start_date, use empty string to sort it last within its year
        date = lineup['start_date'] if lineup['start_date'] else ''
        return (-year, '' if not date else datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d'), lineup['festival'])
    
    return sorted(lineups, key=sort_key, reverse=True)


def generate_archive(docs_dir: Path):
    """Generate the archive page."""
    lineups = find_archived_festivals(docs_dir)
    
    # Get path prefix for menu (archive.html is at root, so empty prefix)
    path_prefix = ""
    
    title = "Festival Archive | Frank's LineupRadar"
    description = "Explore past festival lineups, artist bios, and ratings. Discover how indie festivals have evolved."
    url = "https://frankvaneykelen.github.io/lineup-radar/"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="festival archive, past lineups, music history, festival evolution">
    <meta name="author" content="Frank van Eykelen">
    <link rel="icon" type="image/png" sizes="16x16" href="shared/favicon_16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="shared/favicon_32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="shared/favicon_48x48.png">
    <link rel="apple-touch-icon" sizes="180x180" href="shared/favicon_180x180.png">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="shared/styles.css">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}archive.html">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{url}shared/opengraph.png">

    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{url}archive.html">
    <meta property="twitter:title" content="{title}">
    <meta property="twitter:description" content="{description}">
    <meta property="twitter:image" content="{url}shared/opengraph.png">
</head>
<body>
    <div class="container-fluid">
        <header class="artist-header lineup-header">
            <div class="hamburger-menu">
                <button id="hamburgerBtn" class="btn btn-outline-light hamburger-btn" title="Menu">
                    <i class="bi bi-list"></i>
                </button>
                <div id="dropdownMenu" class="dropdown-menu-custom">
                    <a href="index.html" class="home-link">
                        <i class="bi bi-house-door-fill"></i> Home
                    </a>
                    {generate_hamburger_menu(path_prefix)}
                </div>
            </div>
            <div class="artist-header-content">
                <h1>Festival Archive</h1>
                <p class="subtitle">Explore past festival lineups and their evolution</p>
            </div>
            <div style="width: 120px;"></div>
        </header>
        
        <div class="artist-content container-fluid">
            <div class="row justify-content-center">
                <div class="col-lg-10 col-md-12">
"""
    
    if not lineups:
        html += """            <div class="alert alert-info text-center" role="alert">
                <i class="bi bi-info-circle"></i> No archived festivals yet. Check back later!
            </div>
"""
    else:
        # Helper function to render a festival card
        def render_festival_card(lineup):
            # Get festival config for proper name
            try:
                config = get_festival_config(lineup['festival'], int(lineup['year']))
                festival_display = config.name
            except:
                festival_display = lineup['festival'].replace('-', ' ').title()
            
            # Format dates
            festival_dates = "Dates TBA"
            if lineup['start_date'] and lineup['end_date']:
                start_dt = datetime.strptime(lineup['start_date'], '%Y-%m-%d')
                end_dt = datetime.strptime(lineup['end_date'], '%Y-%m-%d')
                if lineup['start_date'] == lineup['end_date']:
                    festival_dates = start_dt.strftime('%B %d, %Y')
                elif start_dt.month == end_dt.month:
                    festival_dates = f"{start_dt.strftime('%B')} {start_dt.day}-{end_dt.day}, {lineup['year']}"
                else:
                    festival_dates = f"{start_dt.strftime('%B %d')} - {end_dt.strftime('%B %d')}, {lineup['year']}"
            elif lineup['start_date']:
                start_dt = datetime.strptime(lineup['start_date'], '%Y-%m-%d')
                festival_dates = start_dt.strftime('%B %d, %Y')
            
            tagline = lineup['tagline'] or "Discover the lineup and artist details"
            
            return f"""                                <div class="col-md-6 col-lg-4">
                                    <div class="card h-100 shadow-sm">
                                        <div class="card-body d-flex flex-column">
                                            <h5 class="card-title text-primary">{festival_display}</h5>
                                            <p class="card-text mb-2">
                                                <small class="text-muted"><i class="bi bi-calendar-event"></i> {festival_dates}</small>
                                            </p>
                                            <p class="card-text flex-grow-1">{tagline}</p>
                                            <a href="{lineup['path']}" class="btn btn-primary mt-auto">
                                                View Lineup <i class="bi bi-arrow-right"></i>
                                            </a>
                                        </div>
                                    </div>
                                </div>
"""
        
        # Group by year
        for year, year_lineups in groupby(lineups, key=lambda x: x['year']):
            year_lineups = list(year_lineups)
            html += f"""            <h2 style="margin-top: 2rem; margin-bottom: 1.5rem; color: #00d9ff;">
                <i class="bi bi-calendar3"></i> {year}
            </h2>
            <div class="row g-4 mb-4">
"""
            for lineup in year_lineups:
                html += render_festival_card(lineup)
            
            html += """            </div>
"""
    
    html += """                </div>
            </div>
        </div>
        
        <footer style="background: #1a1a2e; color: #ccc; padding: 30px 20px; text-align: center; font-size: 0.9em; margin-top: 40px;">
            <button class="dark-mode-toggle" id="darkModeToggle" title="Toggle dark mode">
                <i class="bi bi-moon-fill"></i>
            </button>
            <div>
                <p style="margin-bottom: 15px;">
                    <strong>Content Notice:</strong> These pages combine content scraped from festival websites 
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
    <script src="shared/script.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script defer src="https://frankvaneykelen-umami-app.azurewebsites.net/script.js" data-website-id="c10bb9a5-e39d-4286-a3d9-7c3ca9171d51"></script>
</body>
</html>
"""
    
    # Write to archive.html
    output_file = docs_dir / "archive.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated archive: {output_file}")
    if lineups:
        print(f"   📦 Found {len(lineups)} archived festival(s)")
    else:
        print(f"   📦 No archived festivals")


if __name__ == "__main__":
    # Use docs directory
    docs_dir = Path(__file__).parent.parent / "docs"
    if not docs_dir.exists():
        print(f"❌ Error: docs directory not found at {docs_dir}")
        sys.exit(1)
    
    generate_archive(docs_dir)
