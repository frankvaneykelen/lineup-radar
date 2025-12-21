#!/usr/bin/env python3
"""
Generate FAQ page dynamically from festival configuration and CSV data.
"""

import csv
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys
# helpers module is in the same directory

from menu import FESTIVALS, YEAR, generate_hamburger_menu


def count_artists_in_csv(csv_path: str) -> int:
    """Count the number of artists in a CSV file."""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return sum(1 for _ in reader)
    except FileNotFoundError:
        return 0


def get_csv_last_modified(csv_path: str) -> str:
    """Get the last modified date of a CSV file."""
    try:
        timestamp = os.path.getmtime(csv_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    except FileNotFoundError:
        return 'Unknown'


def generate_festival_list_html() -> str:
    """Generate the dynamic festival list with artist counts and timestamps."""
    festival_items = []
    
    # Import here to avoid circular dependency
    import json
    from pathlib import Path
    
    # Build a list of (start_date, festival_slug, festival_config)
    festival_list = []
    for festival_slug, festival_config in FESTIVALS.items():
        # Skip festivals hidden from navigation
        if festival_config.get('hide_from_navigation', False):
            continue
        
        # Get festival start date from about.json
        about_path = Path(f'docs/{festival_slug}/{YEAR}/about.json')
        start_date = '9999-12-31'  # Default for festivals without dates
        if about_path.exists():
            try:
                with open(about_path, 'r', encoding='utf-8') as f:
                    about_data = json.load(f)
                    start_date = about_data.get('start_date', '9999-12-31')
            except Exception:
                pass
        
        festival_list.append((start_date, festival_slug, festival_config))
    
    # Sort by start_date (ascending)
    festival_list.sort(key=lambda x: x[0])
    
    # Generate festival items in date order
    for start_date, festival_slug, festival_config in festival_list:
        # Construct CSV path
        csv_path = f'docs/{festival_slug}/{YEAR}/{YEAR}.csv'
        
        # Get artist count and last modified date
        artist_count = count_artists_in_csv(csv_path)
        last_modified = get_csv_last_modified(csv_path)
        
        # Get festival name from config
        festival_name = festival_config.get('name', festival_slug)
        
        # Generate HTML for this festival
        festival_items.append(
            f'<li><strong>{festival_name} {YEAR}:</strong> {artist_count} artists <i>(last updated: {last_modified})</i></li>'
        )
    
    return '\n                        '.join(festival_items)


def generate_faq_html() -> str:
    """Generate the complete FAQ HTML page."""
    
    # Get dynamic content
    menu_html = generate_hamburger_menu(path_prefix="", escaped=False)
    festival_list_html = generate_festival_list_html()
    # Count only festivals not hidden from navigation
    festival_count = sum(1 for config in FESTIVALS.values() if not config.get('hide_from_navigation', False))
    
    title = "FAQ - Frank's LineupRadar"
    description = "Frequently Asked Questions about Frank's LineupRadar, the ultimate festival lineup tracking tool."
    url = "https://frankvaneykelen.github.io/lineup-radar/faq.html"     
    base_url = "https://frankvaneykelen.github.io/lineup-radar/"    
    
    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FAQ - Frank's LineupRadar</title>
    <link rel="icon" type="image/png" sizes="16x16" href="shared/favicon_16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="shared/favicon_32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="shared/favicon_48x48.png">
    <link rel="apple-touch-icon" sizes="180x180" href="shared/favicon_180x180.png">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="shared/styles.css">
    
    <!-- Open Graph (Facebook, LinkedIn) -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{base_url}shared/lineup-radar-logo.png">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{base_url}shared/lineup-radar-logo.png">

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
                    {menu_html}
                </div>
            </div>
            <div class="artist-header-content">
                <h1>FAQ</h1>
                <p class="subtitle">Frequently Asked Questions</p>
            </div>
            <div style="width: 120px;"></div>
        </header>

        <div class="artist-content container-fluid">
            <div class="row justify-content-center">
                <div class="col-lg-8 col-md-10">
                    <div class="section">
                        
                        <!-- Table of Contents -->
                        <div style="margin-bottom: 3rem;">
                            <h2 style="color: #00d9ff; margin-top: 0; margin-bottom: 1.5rem;">Table of Contents</h2>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                                <div>
                                    <a href="#general" style="color: #00d9ff; text-decoration: none; font-weight: bold;">
                                        <i class="bi bi-info-circle"></i> General Questions
                                    </a>
                                </div>
                                <div>
                                    <a href="#features" style="color: #00d9ff; text-decoration: none; font-weight: bold;">
                                        <i class="bi bi-gear"></i> Features & Functionality
                                    </a>
                                </div>
                                <div>
                                    <a href="#data" style="color: #00d9ff; text-decoration: none; font-weight: bold;">
                                        <i class="bi bi-database"></i> Data & Updates
                                    </a>
                                </div>
                                <div>
                                    <a href="#technical" style="color: #00d9ff; text-decoration: none; font-weight: bold;">
                                        <i class="bi bi-code-slash"></i> Technical
                                    </a>
                                </div>
                                <div>
                                    <a href="#contact" style="color: #00d9ff; text-decoration: none; font-weight: bold;">
                                        <i class="bi bi-envelope"></i> Contact & Feedback
                                    </a>
                                </div>
                            </div>
                        </div>
                        
                        <!-- General Questions -->
                        <h2 id="general" style="color: #00d9ff; margin-top: 2rem; margin-bottom: 1.5rem;">General Questions</h2>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">What is LineupRadar?</h3>
                            <p>LineupRadar is a comprehensive festival lineup tracking tool that helps music lovers discover and explore festival lineups. It combines scraped festival data with AI-generated artist information to provide a rich, searchable database of festival artists.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Which festivals are currently tracked?</h3>
                            <p>We currently track {festival_count} festivals, both major and local:</p>
                            <ul>
                                {festival_list_html}
                            </ul>
                            <p>New festivals are added regularly based on data availability and community requests.</p>
                        </div>
                        
                        <!-- Features & Functionality -->
                        <h2 id="features" style="color: #00d9ff; margin-top: 3rem; margin-bottom: 1.5rem;">Features & Functionality</h2>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">How do I filter the lineup?</h3>
                            <p>Use the search box at the top of each festival page to filter artists by name, genre, or country. The filtering is instant and case-insensitive.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Can I sort the lineup differently?</h3>
                            <p>Yes! Click on any column header to sort by that field. Click again to reverse the sort order. You can sort by artist name, day, time, genre, country, and more.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">What information is available for each artist?</h3>
                            <p>Each artist entry includes:</p>
                            <ul>
                                <li>Basic info: name, day, time, stage/location</li>
                                <li>Genre and country of origin</li>
                                <li>AI-generated biography and analysis</li>
                                <li>Links to Spotify, official website, and social media</li>
                            </ul>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">What are the festival statistics?</h3>
                            <p>Each festival's About page includes:</p>
                            <ul>
                                <li>Overview statistics (total artists, countries, genres)</li>
                                <li>Top genres and countries represented</li>
                                <li>Gender distribution analysis</li>
                                <li>People of Color (POC) representation</li>
                                <li>Personal rating distribution (if provided)</li>
                                <li>AI-generated festival profile and analysis</li>
                            </ul>
                        </div>
                        
                        <!-- Data & Updates -->
                        <h2 id="data" style="color: #00d9ff; margin-top: 3rem; margin-bottom: 1.5rem;">Data & Updates</h2>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Where does the data come from?</h3>
                            <p>Festival lineup data is scraped from official festival websites. Artist biographies, descriptions, and analysis are generated using Azure OpenAI GPT-4o. Spotify links and some metadata are fetched from the Spotify API.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">How often is the data updated?</h3>
                            <p>Data is updated as festival lineups are announced and modified. The last update time for each festival is shown in the festival list above. You can also check the individual festival pages for the most recent update timestamp.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Is the data accurate?</h3>
                            <p>While we strive for accuracy, this site combines automated web scraping with AI-generated content. Information may be incomplete or inaccurate. Always verify critical details (like performance times and stages) on the official festival websites.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">What if an artist cancels?</h3>
                            <p>When artists cancel their performance, we mark them as "Cancelled" in the lineup rather than removing them. This helps maintain a complete record of announced lineups and changes.</p>
                        </div>
                        
                        <!-- Technical -->
                        <h2 id="technical" style="color: #00d9ff; margin-top: 3rem; margin-bottom: 1.5rem;">Technical</h2>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">What technologies power LineupRadar?</h3>
                            <p>LineupRadar is built with:</p>
                            <ul>
                                <li>Python for web scraping and data processing</li>
                                <li>Azure OpenAI GPT-4o for AI-generated content</li>
                                <li>Spotify API for music links and metadata</li>
                                <li>Bootstrap 5 for responsive design</li>
                                <li>Chart.js for data visualizations</li>
                                <li>GitHub Pages for hosting</li>
                            </ul>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Does LineupRadar work on mobile?</h3>
                            <p>Yes! LineupRadar is fully responsive and works great on phones, tablets, and desktops. The interface adapts to your screen size for optimal readability.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Can I link directly to a specific artist?</h3>
                            <p>Yes! Each artist has their own dedicated page with a permanent URL that you can share or bookmark.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Is the source code available?</h3>
                            <p>Yes! LineupRadar is open source. You can view the code and contribute on <a href="https://github.com/frankvaneykelen/lineup-radar" target="_blank" style="color: #00d9ff;">GitHub</a>.</p>
                        </div>
                        
                        <!-- Contact & Feedback -->
                        <h2 id="contact" style="color: #00d9ff; margin-top: 3rem; margin-bottom: 1.5rem;">Contact & Feedback</h2>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">I found an error. How do I report it?</h3>
                            <p>Please report issues on our <a href="https://github.com/frankvaneykelen/lineup-radar/issues" target="_blank" style="color: #00d9ff;">GitHub Issues page</a>. We appreciate your help in improving the accuracy of the data!</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">Can you add my favorite festival?</h3>
                            <p>Festival requests can be made via <a href="https://github.com/frankvaneykelen/lineup-radar/issues" target="_blank" style="color: #00d9ff;">GitHub Issues</a>. We prioritize indie and boutique festivals with publicly available lineup data.</p>
                        </div>
                        
                        <div class="faq-item" style="margin-bottom: 2rem;">
                            <h3 style="color: #00a8cc; font-size: 1.2em; margin-bottom: 0.5rem;">How can I support this project?</h3>
                            <p>The best way to support LineupRadar is to:</p>
                            <ul>
                                <li>Share it with fellow festival-goers</li>
                                <li>Report issues or inaccuracies you find</li>
                                <li>Star the project on <a href="https://github.com/frankvaneykelen/lineup-radar" target="_blank" style="color: #00d9ff;">GitHub</a></li>
                                <li>Contribute code improvements or new features</li>
                            </ul>
                        </div>
                        
                        <!-- Back to Home -->
                        <div style="margin-top: 3rem; margin-bottom: 2rem; text-align: center;">
                            <a href="index.html" class="btn btn-primary btn-lg" style="font-size: 1.2em; padding: 15px 30px;">
                                <i class="bi bi-arrow-left"></i> Back to Home
                            </a>
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
</html>'''
    
    return html


def main():
    """Main function to generate FAQ page."""
    print("Generating FAQ page...")
    
    # Generate HTML
    html_content = generate_faq_html()
    
    # Write to file
    output_path = Path(__file__).parent.parent.parent / 'docs' / 'faq.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ FAQ page generated: {output_path}")


if __name__ == '__main__':
    main()
