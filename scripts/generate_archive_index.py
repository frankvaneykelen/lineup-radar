#!/usr/bin/env python3
"""
Generate the main archive index page (docs/index.html).
This page serves as the landing page linking to all yearly lineups.
"""

import sys
import json
from pathlib import Path
from typing import List
from itertools import groupby
from datetime import datetime, timezone

# Add parent directory to sys.path to import festival_helpers
import sys
sys.path.insert(0, str(Path(__file__).parent))
from helpers.config import get_festival_config, FESTIVALS
from helpers import generate_hamburger_menu


def find_festival_lineups(docs_dir: Path) -> List[dict]:
    """Find all festival lineups in the docs directory."""
    lineups = []
    
    # Look for festival/year/index.html structure
    for festival_dir in docs_dir.iterdir():
        if festival_dir.is_dir() and not festival_dir.name.startswith('.'):
            for year_dir in festival_dir.iterdir():
                if year_dir.is_dir() and year_dir.name.isdigit():
                    if (year_dir / "index.html").exists():
                        # Try to find the corresponding CSV file
                        csv_file = year_dir / f"{year_dir.name}.csv"
                        csv_mtime = None
                        try:
                            if csv_file.exists():
                                csv_mtime = csv_file.stat().st_mtime
                        except OSError:
                            # Handle permission issues or file access errors
                            pass
                        
                        # Try to read start_date from about.json
                        start_date = None
                        about_json = year_dir / "about.json"
                        try:
                            if about_json.exists():
                                with open(about_json, 'r', encoding='utf-8') as f:
                                    about_data = json.load(f)
                                    start_date = about_data.get('start_date')
                        except (OSError, json.JSONDecodeError):
                            pass
                        
                        lineups.append({
                            'festival': festival_dir.name,
                            'year': year_dir.name,
                            'path': f"{festival_dir.name}/{year_dir.name}/index.html",
                            'csv_mtime': csv_mtime,
                            'start_date': start_date
                        })
    
    # Sort by start_date (festivals with no date go last), then by festival name
    # Use a tuple for sorting: (year, date_or_large_value, festival_name)
    def sort_key(lineup):
        year = lineup['year']
        # If no start_date, use 9999-12-31 to sort it last within its year
        date = lineup['start_date'] if lineup['start_date'] else '9999-12-31'
        return (year, date, lineup['festival'])
    
    return sorted(lineups, key=sort_key)


def generate_archive_index(docs_dir: Path):
    """Generate the main archive index page."""
    lineups = find_festival_lineups(docs_dir)
    
    if not lineups:
        print("⚠️  No festival lineups found")
        print("   Generate lineups first with: python generate_html.py --year YYYY --festival FESTIVAL")
        sys.exit(1)
    
    title = "Frank's LineupRadar | Discover Festival Lineups & Hidden Gems"
    description = "Explore complete festival lineups, artist bios, ratings, and metadata. Discover emerging acts before the festival starts with Frank's LineupRadar."
    url = "https://frankvaneykelen.github.io/lineup-radar/"
    baseurl = url

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="festival lineup, indie festivals, artist discovery, setlist, music metadata, boutique festivals, lineup archive, music diversity">
    <meta name="author" content="Frank van Eykelen">
    <link rel="icon" type="image/png" sizes="16x16" href="shared/favicon_16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="shared/favicon_32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="shared/favicon_48x48.png">
    <link rel="apple-touch-icon" sizes="180x180" href="shared/favicon_180x180.png">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="shared/styles.css">
    
    <!-- Open Graph (Facebook, LinkedIn) -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{baseurl}shared/lineup-radar-logo.png">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{baseurl}shared/lineup-radar-logo.png">

    <!-- Canonical URL -->
    <link rel="canonical" href="{url}">
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
{generate_hamburger_menu(path_prefix="")}
                </div>
            </div>
            <div class="artist-header-content">
                <h1>Frank's LineupRadar</h1>
                <p class="subtitle">Your Artist Lineup Archive & Discovery Tool</p>
            </div>
            <div style="width: 120px;"></div>
        </header>
        
        <div class="artist-content container-fluid">
            <div class="row justify-content-center">
                <div class="col-lg-8 col-md-10">
                    <div class="section">
                        <h2 style="color: #00d9ff; margin-bottom: 1.5rem;">Never Miss the Acts Everyone Talks About</h2>
                        <p>Ever read post-festival reviews and realize you skipped the breakout artist everyone loved?</p>
                        <p><strong>LineupRadar</strong> helps you discover those hidden gems before the festival starts—so you can proudly say: <em>"I was there!"</em>
                        </p>
                        <p>Start exploring now and turn your festival experience into a discovery adventure.</p>                        
                        <div class="year-list">
"""
    
    # Get the most recent CSV modification time from all lineups
    csv_mtimes = [l['csv_mtime'] for l in lineups if l.get('csv_mtime') is not None]
    if csv_mtimes:
        most_recent_csv_mtime = max(csv_mtimes)
        most_recent_csv_datetime = datetime.fromtimestamp(most_recent_csv_mtime, tz=timezone.utc)
        timestamp = most_recent_csv_datetime.strftime("%B %d, %Y %H:%M UTC")
    else:
        # Fallback to current time if no CSV files found
        now = datetime.now()
        timestamp = now.strftime("%B %d, %Y at %I:%M %p")
    
    # Group lineups by year for better organization
    from itertools import groupby
    
    for year, year_lineups in groupby(lineups, key=lambda x: x['year']):
        year_lineups = list(year_lineups)
        html += f"""                            <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: #00d9ff;">{year}</h3>
                            <div class="row g-4">
"""
        # Card-based layout for festivals
        for lineup in year_lineups:
            # Skip festivals marked as hidden from navigation
            if FESTIVALS.get(lineup['festival'], {}).get('hide_from_navigation', False):
                continue
                
            # Get festival config for proper name and description
            try:
                config = get_festival_config(lineup['festival'], int(year))
                festival_display = config.name
                description = config.description
            except:
                # Fallback if config not found
                festival_display = lineup['festival'].replace('-', ' ').title()
                description = ""
            
            # Get festival dates from about.json
            festival_dates = "Dates TBA"
            tagline = description or "Discover the lineup and artist details"
            
            about_json = Path("docs") / lineup['festival'] / year / "about.json"
            try:
                if about_json.exists():
                    with open(about_json, 'r', encoding='utf-8') as f:
                        about_data = json.load(f)
                        start_date = about_data.get('start_date')
                        end_date = about_data.get('end_date')
                        
                        if start_date and end_date:
                            # Format dates nicely
                            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                            
                            if start_dt.month == end_dt.month:
                                # Same month: "June 14-16, 2026"
                                festival_dates = f"{start_dt.strftime('%B')} {start_dt.day}-{end_dt.day}, {year}"
                            else:
                                # Different months: "May 30 - June 1, 2026"
                                festival_dates = f"{start_dt.strftime('%B %d')} - {end_dt.strftime('%B %d')}, {year}"
                        elif start_date:
                            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                            festival_dates = start_dt.strftime('%B %d, %Y')
                        
                        # Get tagline from about.json if available
                        if about_data.get('tagline'):
                            tagline = about_data['tagline']
            except:
                pass
            
            html += f"""                                <div class="col-md-6 col-lg-4">
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
        html += """                            </div>
"""
    
    # Add Charts and FAQ buttons
    html += f"""
 
                       <h2 style="color: #00d9ff; margin-top: 2rem; margin-bottom: 1rem;">Why Use LineupRadar?</h2>
                        <ul style="font-size: 1.05em; line-height: 1.8; margin-bottom: 2rem;">
                            <li><strong>Explore Complete Festival Lineups:</strong> Browse curated tables with ratings, bios, and metadata for every act.</li>
                            <li><strong>Discover Emerging Artists:</strong> Find the next big names before they hit the main stage.</li>
                            <li><strong>Filter by Diversity & Style:</strong> Tired of endless guitar bands? Use filters to uncover unique sounds and diverse performers.</li>
                            <li><strong>Click Through for Details:</strong> Each artist has a dedicated page with background info, genre tags, and links.</li>
                            <li><strong>Plan Your Perfect Festival Schedule:</strong> Avoid clashes and make sure you catch the acts that matter.</li>
                        </ul>
                        
                        <h2 style="color: #00d9ff; margin-bottom: 1rem;">Ideal For</h2>
                        <ul style="font-size: 1.05em; line-height: 1.8; margin-bottom: 2rem;">
                            <li>Indie and boutique festival fans</li>
                            <li>Music bloggers and reviewers</li>
                            <li>Anyone who wants to go beyond the headliners</li>
                        </ul>
                        
                                                    
                            <h3 style="margin-top: 3rem; margin-bottom: 1rem; color: #00d9ff;">Explore & Learn</h3>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <a href="charts.html" class="btn btn-info btn-lg w-100" style="font-size: 1.3em; padding: 20px;">
                                        <i class="bi bi-bar-chart-fill"></i> Charts & Diversity Index →
                                    </a>
                                </div>
                                <div class="col-md-6">
                                    <a href="faq.html" class="btn btn-secondary btn-lg w-100" style="font-size: 1.3em; padding: 20px;">
                                        <i class="bi bi-question-circle-fill"></i> FAQ →
                                    </a>
                                </div>
                            </div>
                            
                            <p style="margin-top: 2rem; text-align: center; color: #888; font-size: 0.9em;">
                                <em>Last updated: {timestamp}</em>
                            </p>
                        </div>
                    </div>
                </div>
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
    
    output_file = docs_dir / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Generated archive index: {output_file}")
    print(f"  Found {len(lineups)} lineup(s) across {len(set(l['year'] for l in lineups))} year(s)")
    for lineup in lineups:
        print(f"    - {lineup['festival']} {lineup['year']}")


def main():
    """Main entry point."""
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")
    
    if not docs_dir.exists():
        print(f"✗ Docs directory not found: {docs_dir}")
        print("  Create it first or run generate_html.py")
        sys.exit(1)
    
    generate_archive_index(docs_dir)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
