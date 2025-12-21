#!/usr/bin/env python3
"""
Generate HTML pages from festival CSV data for GitHub Pages.
Creates interactive tables with sorting and filtering.
"""

import sys
from pathlib import Path

# Add scripts directory to path for helpers module
import sys
sys.path.insert(0, str(Path(__file__).parent))

import csv
import os
import json
import re
from helpers import artist_name_to_slug, get_festival_config, generate_hamburger_menu
from helpers.slug import get_sort_name

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

def generate_html(csv_file, output_dir, config):
    """Generate HTML page from CSV file."""
    
    # Read CSV data
    artists = []
    headers = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            artists.append(row)
    
    if not artists:
        print(f"No data found in {csv_file}")
        return
    
    # Check if any artist has schedule data
    has_schedule_data = any(
        artist.get('Date', '').strip() or 
        artist.get('Start Time', '').strip() or 
        artist.get('End Time', '').strip() or 
        artist.get('Stage', '').strip()
        for artist in artists
    )
    
    # Get year from filename (e.g., 2026.csv -> 2026)
    year = Path(csv_file).stem
    
    title = f"{config.name} {year} Lineup - Frank's LineupRadar"
    description = f"Browse the complete {config.name} {year} lineup with artist ratings, genres, and bios. Discover hidden gems and plan your perfect festival schedule."
    base_url = "https://frankvaneykelen.github.io/lineup-radar/"
    url = f"{base_url}{config.slug}/{year}/index.html"
    
    # Get last modified time of CSV file in UTC
    from datetime import datetime, timezone
    csv_path = Path(csv_file)
    last_modified = datetime.fromtimestamp(csv_path.stat().st_mtime, tz=timezone.utc)
    last_updated_str = last_modified.strftime("%B %d, %Y %H:%M UTC")
    
    # Create output directory with festival name
    output_path = Path(output_dir) / config.slug / year
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Sort artists for table using the same rule as artist pages
    from helpers.slug import get_sort_name
    artists = sorted(artists, key=lambda a: get_sort_name(a.get('Artist', '')))
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{config.name}, {year} lineup, festival artists, music discovery, artist ratings, {config.name} {year}">
    <meta name="author" content="Frank van Eykelen">
    <link rel="icon" type="image/png" sizes="16x16" href="../../shared/favicon_16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="../../shared/favicon_32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="../../shared/favicon_48x48.png">
    <link rel="apple-touch-icon" sizes="180x180" href="../../shared/favicon_180x180.png">
    
    <!-- PWA Manifest -->
    <link rel="manifest" href="../../manifest.json">
    <meta name="theme-color" content="#00d9ff">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="LineupRadar">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="../../shared/styles.css">
    <link rel="stylesheet" href="overrides.css">

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
    <!-- Rotate device message for mobile portrait -->
    <div class="rotate-message" id="rotateMessage">
        <div class="rotate-content">
            <button class="rotate-close" id="rotateClose" aria-label="Close" title="Don't show again">&times;</button>
            <i class="bi bi-phone-landscape" style="font-size: 3rem; margin-bottom: 1rem;"></i>
            <p>For the best experience, please rotate your device to landscape mode when viewing the festival lineup pages</p>
        </div>
    </div>
    
    <div class="container-fluid">
        <header class="artist-header lineup-header">
            <div class="hamburger-menu">
                <button id="hamburgerBtn" class="btn btn-outline-light hamburger-btn" title="Menu">
                    <i class="bi bi-list"></i>
                </button>
                <div id="dropdownMenu" class="dropdown-menu-custom">
                    <a href="../../index.html" class="home-link">
                        <i class="bi bi-house-door-fill"></i> Home
                    </a>
{generate_hamburger_menu(path_prefix="../../")}
                </div>
            </div>
            <div class="page-header-content">
                <h1>{config.name} {year} Lineup</h1>
                {'<p class="festival-description" style="font-size: 0.95em; opacity: 0.85; margin-top: 0.5rem; max-width: 800px;">' + config.description + '</p>' if config.description else ''}
                <p class="subtitle" style="font-size: 0.8em; opacity: 0.7; margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                   <a href="about.html" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm px-3 py-1" style="font-weight: 600;">About</a>
                    {('<a href="' + config.lineup_url + '" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm px-3 py-1" style="font-weight: 600;">Festival Site</a>') if config.lineup_url else ''}
                    {('<a href="' + config.official_spotify_playlist + '" target="_blank" rel="noopener noreferrer" class="btn btn-outline-success btn-sm px-3 py-1" style="font-weight: 600;"><i class="bi bi-spotify"></i> Official Playlist</a>') if config.official_spotify_playlist else ''}
                    {('<a href="' + config.spotify_playlist_id + '" target="_blank" rel="noopener noreferrer" class="btn btn-success btn-sm px-3 py-1" style="font-weight: 600;"><i class="bi bi-spotify"></i> LineupRadar Playlist</a>') if config.spotify_playlist_id else ''}
                </p>
            </div>
        </header>
        
        <div class="controls">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <input type="text" id="searchBox" class="search-box" placeholder="Search artists, genres, countries..." style="flex: 1; margin: 0;">
                <div style="margin-left: 15px; color: #666; font-size: 14px; white-space: nowrap;">
                    Showing <strong><span id="visibleCountTop">{len(artists)}</span></strong> of <strong>{len(artists)}</strong> artists
                </div>
            </div>
            
            <div class="filters">
                {'<div class="filter-group"><label for="dateFilter">Filter by Date</label><select id="dateFilter"><option value="">All Dates</option></select></div>' if has_schedule_data else ''}
                {'<div class="filter-group"><label for="stageFilter">Filter by Stage</label><select id="stageFilter"><option value="">All Stages</option></select></div>' if has_schedule_data else ''}
                
                <div class="filter-group">
                    <label for="genreFilter">Filter by Genre</label>
                    <select id="genreFilter">
                        <option value="">All Genres</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="countryFilter">Filter by Country</label>
                    <select id="countryFilter">
                        <option value="">All Countries</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="ratingFilter">Filter by Rating</label>
                    <select id="ratingFilter">
                        <option value="">All Ratings</option>
                        <option value="9">9+ (Excellent)</option>
                        <option value="8">8+ (Very Good)</option>
                        <option value="7">7+ (Good)</option>
                        <option value="6">6+ (Above Average)</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label style="margin-bottom: 8px; display: block;">Gender of Front Person</label>
                    <div class="checkbox-group" id="genderFilters">
                        <label><input type="checkbox" value="Male" checked> ♂️ Male</label>
                        <label><input type="checkbox" value="Female" checked> ♀️ Female</label>
                        <label><input type="checkbox" value="Mixed" checked> ⚤ Mixed</label>
                        <label><input type="checkbox" value="Non-binary" checked> ⚧️ Non-binary</label>
                        <label><input type="checkbox" value="Unknown" checked> ❓ Unknown</label>
                    </div>
                </div>
                
                <div class="filter-group">
                    <label style="margin-bottom: 8px; display: block;">Front Person of Color?</label>
                    <div class="checkbox-group" id="pocFilters">
                        <label><input type="checkbox" value="Yes" checked> Yes</label>
                        <label><input type="checkbox" value="No" checked> No</label>
                        <label><input type="checkbox" value="Unknown" checked> ❓ Unknown</label>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="table-container">
            <table id="artistTable">
                <thead>
                    <tr>
                        <th class="sortable" data-column="Artist">Artist</th>
                        <th class="sortable" data-column="Tagline">Tagline</th>
                        {'<th class="sortable" data-column="Date">Schedule</th>' if has_schedule_data else ''}
                        <th class="sortable" data-column="Genre">Genre</th>
                        <th class="sortable" data-column="Country">Country</th>
                        <th class="sortable" data-column="AI Rating">Rating</th>
                        <th class="sortable" data-column="Number of People in Act">Size</th>
                        <th class="sortable" data-column="Gender of Front Person" title="Gender of Front Person">⚧️</th>
                        <th class="sortable" data-column="Front Person of Color?" title="Front Person of Color?">🌍</th>
                    </tr>
                </thead>
                <tbody id="artistTableBody">
"""
    
    # Add table rows
    for idx, artist in enumerate(artists):
        spotify_link = artist.get('Spotify link', '').strip()
        
        # Only create link if it's a valid URL (not "NOT ON SPOTIFY")
        is_valid_spotify = spotify_link and spotify_link != 'NOT ON SPOTIFY'
        spotify_html = f'<a href="{escape_html(spotify_link)}" target="_blank" class="spotify-link">Spotify<span class="link-icon">🔗</span></a>' if is_valid_spotify else ''
        
        rating = artist.get('AI Rating', '').strip()
        rating_html = f'<span class="rating">{escape_html(rating)}</span>' if rating else ''
        
        bio_text = artist.get('Bio', '').strip()
        
        # Check if bio starts with the festival bio disclaimer
        disclaimer = "[using festival bio due to a lack of publicly available data] "
        if bio_text.startswith(disclaimer):
            bio_main = bio_text[len(disclaimer):]
            bio = f'<small class="text-muted fst-italic d-block mb-1"><i class="bi bi-info-circle-fill"></i> Using festival bio due to a lack of publicly available data</small>{escape_html(bio_main)}'
            bio_title = bio_main
        else:
            bio = escape_html(bio_text)
            bio_title = bio_text
        
        take = escape_html(artist.get('AI Summary', ''))
        
        # Add Spotify link to bio if available and valid
        if is_valid_spotify:
            bio_with_link = f'{bio}<br><br><a href="{escape_html(spotify_link)}" target="_blank" style="white-space: nowrap; font-size: 0.85em; text-decoration: none;">Spotify<span class="link-icon">🔗</span></a>'
        else:
            bio_with_link = bio
        
        # Process genres - split by / and create separate badges
        genre_str = artist.get('Genre', '').strip()
        bio_text_lower = bio_text.lower()
        artist_name_lower = artist.get('Artist', '').lower()
        
        # Check if artist is a DJ (by bio, artist name, or genre description)
        is_dj = ('dj' in bio_text_lower or 
                 'dj' in artist_name_lower or 
                 'b2b' in artist_name_lower or
                 'producer and dj' in bio_text_lower or
                 'dj and producer' in bio_text_lower or
                 'dj collective' in bio_text_lower)
        
        if genre_str:
            genres = [g.strip() for g in genre_str.split('/')]
            genre_badges = ''.join(f'<span class="badge rounded-pill bg-info text-dark me-1">{escape_html(g)}</span>' for g in genres)
            dj_badge = '<span class="badge rounded-pill bg-warning text-dark">DJ</span>' if is_dj else ''
            genre_html = f'{genre_badges}{dj_badge}'
        else:
            genre_html = ''
        
        # Process countries - split by / and create separate badges
        country_str = artist.get('Country', '').strip()
        if country_str:
            countries = [c.strip() for c in country_str.split('/')]
            country_html = ''.join(f'<span class="badge rounded-pill bg-primary me-1">{escape_html(c)}</span>' for c in countries)
        else:
            country_html = ''
        
        # Convert gender to emoji
        gender = artist.get('Gender of Front Person', '').strip()
        gender_emoji_map = {
            'Male': '♂️',
            'Female': '♀️',
            'Mixed': '⚤',
            'Non-binary': '⚧️'
        }
        gender_display = gender_emoji_map.get(gender, escape_html(gender))
        
        # Convert POC to emoji
        poc = artist.get('Front Person of Color?', '').strip()
        poc_emoji_map = {
            'Yes': '✓',
            'No': ''
        }
        poc_display = poc_emoji_map.get(poc, escape_html(poc))
        
        # Create link to individual artist page
        artist_name = artist.get('Artist', '')
        artist_slug = artist_name_to_slug(artist_name)
        artist_page_url = f"artists/{artist_slug}.html"
        
        # Get artist image if it exists
        artist_cell_class = 'artist-cell-clickable'
        artist_cell_style = ''
        
        # Check if there's an image for this artist in the artist directory
        import glob
        artist_dir = Path(output_dir) / config.slug / year / 'artists' / artist_slug
        if artist_dir.exists():
            # Look for any image file in the artist directory
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            all_images = []
            for ext in image_extensions:
                all_images.extend(artist_dir.glob(f"*{ext}"))
                all_images.extend(artist_dir.glob(f"*{ext.upper()}"))
            
            if all_images:
                # Use the first image (sorted alphabetically)
                image_file = sorted(all_images, key=lambda p: p.name.lower())[0].name
                artist_cell_class = 'artist-cell-clickable artist-cell-with-bg'
                artist_cell_style = f' style="background-image: url(\'artists/{artist_slug}/{image_file}\');"'
            else:
                # No artist photos, use default logo
                artist_cell_class = 'artist-cell-clickable artist-cell-with-bg'
                artist_cell_style = f' style="background-image: url(\'../../shared/lineup-radar-logo.png\');"'
        else:
            # Artist directory doesn't exist, use default logo
            artist_cell_class = 'artist-cell-clickable artist-cell-with-bg'
            artist_cell_style = f' style="background-image: url(\'../../shared/lineup-radar-logo.png\');"'
        
        # Get schedule info
        date = escape_html(artist.get('Date', ''))
        start_time = escape_html(artist.get('Start Time', ''))
        # Build schedule info if available
        schedule_parts = []
        date_val = artist.get('Date', '').strip()
        start_val = artist.get('Start Time', '').strip()
        end_val = artist.get('End Time', '').strip()
        stage_val = artist.get('Stage', '').strip()
        
        if date_val:
            schedule_parts.append(escape_html(date_val))
        if start_val and end_val:
            schedule_parts.append(f'{escape_html(start_val)}-{escape_html(end_val)}')
        elif start_val:
            schedule_parts.append(escape_html(start_val))
        if stage_val:
            schedule_parts.append(escape_html(stage_val))
        
        schedule_display = ' | '.join(schedule_parts) if schedule_parts else ''
        schedule_td = f'<td>{schedule_display}</td>' if has_schedule_data else ''
        
        tagline = escape_html(artist.get('Tagline', ''))
        
        # Prepare bio tooltip - use the clean bio text without HTML formatting
        bio_tooltip = escape_html(bio_title) if bio_title else ''
        
        html_content += f"""                    <tr data-index="{idx}">
                        <td class="{artist_cell_class}" onclick="window.location.href='{artist_page_url}'" {artist_cell_style} title="{bio_tooltip}">
                            <strong>{escape_html(artist_name)}</strong>
                        </td>
                        <td class="tagline">{tagline}</td>
                        {schedule_td}
                        <td>{genre_html}</td>
                        <td>{country_html}</td>
                        <td>{rating_html}</td>
                        <td>{escape_html(artist.get('Number of People in Act', ''))}</td>
                        <td title="{escape_html(gender)}">{gender_display}</td>
                        <td title="Front Person of Color: {escape_html(poc)}">{poc_display}</td>
                    </tr>
"""
    
    # Add JavaScript for interactivity
    artists_json = json.dumps([dict(row) for row in artists])
    
    html_content += f"""                </tbody>
            </table>
        </div>
        
        <div class="stats">
            <p>Showing <strong><span id="visibleCount">{len(artists)}</span></strong> of <strong>{len(artists)}</strong> artists</p>
        </div>
    </div>
    
    <script>
        const artistsData = {artists_json};
        let currentSort = {{ column: 'Artist', direction: 'asc' }};
        const hasScheduleData = {str(has_schedule_data).lower()};
        
        // Populate filter dropdowns with counts
        // Count dates and stages if schedule data exists
        if (hasScheduleData) {{
            const dateCounts = {{}};
            const stageCounts = {{}};
            
            artistsData.forEach(a => {{
                const date = a['Date'] || '';
                const stage = a['Stage'] || '';
                
                if (date) {{
                    dateCounts[date] = (dateCounts[date] || 0) + 1;
                }}
                if (stage) {{
                    stageCounts[stage] = (stageCounts[stage] || 0) + 1;
                }}
            }});
            
            const dates = Object.keys(dateCounts).sort();
            const stages = Object.keys(stageCounts).sort();
            
            const dateSelect = document.getElementById('dateFilter');
            if (dateSelect) {{
                dates.forEach(date => {{
                    const option = document.createElement('option');
                    option.value = date;
                    option.textContent = `${{date}} (${{dateCounts[date]}})`;
                    dateSelect.appendChild(option);
                }});
            }}
            
            const stageSelect = document.getElementById('stageFilter');
            if (stageSelect) {{
                stages.forEach(stage => {{
                    const option = document.createElement('option');
                    option.value = stage;
                    option.textContent = `${{stage}} (${{stageCounts[stage]}})`;
                    stageSelect.appendChild(option);
                }});
            }}
        }}
        
        // Count genres (split by / to handle multiple genres per artist)
        const genreCounts = {{}};
        artistsData.forEach(a => {{
            if (a.Genre) {{
                a.Genre.split('/').forEach(g => {{
                    const genre = g.trim();
                    genreCounts[genre] = (genreCounts[genre] || 0) + 1;
                }});
            }}
        }});
        const genres = Object.keys(genreCounts).sort();
        
        // Count countries (split by / to handle multiple countries per artist)
        const countryCounts = {{}};
        artistsData.forEach(a => {{
            if (a.Country) {{
                a.Country.split('/').forEach(c => {{
                    const country = c.trim();
                    countryCounts[country] = (countryCounts[country] || 0) + 1;
                }});
            }}
        }});
        const countries = Object.keys(countryCounts).sort();
        
        const genreSelect = document.getElementById('genreFilter');
        genres.forEach(genre => {{
            const option = document.createElement('option');
            option.value = genre;
            option.textContent = `${{genre}} (${{genreCounts[genre]}})`;
            genreSelect.appendChild(option);
        }});
        
        const countrySelect = document.getElementById('countryFilter');
        countries.forEach(country => {{
            const option = document.createElement('option');
            option.value = country;
            option.textContent = `${{country}} (${{countryCounts[country]}})`;
            countrySelect.appendChild(option);
        }});
        
        // Count ratings
        const ratingCounts = {{ '10': 0, '9': 0, '8': 0, '7': 0, '6': 0, '5': 0, '4': 0, '3': 0, '2': 0, '1': 0 }};
        artistsData.forEach(a => {{
            const rating = parseFloat(a['AI Rating']);
            if (rating === 10) ratingCounts['10']++;
            if (rating >= 9) ratingCounts['9']++;
            if (rating >= 8) ratingCounts['8']++;
            if (rating >= 7) ratingCounts['7']++;
            if (rating >= 6) ratingCounts['6']++;
            if (rating >= 5) ratingCounts['5']++;
            if (rating >= 4) ratingCounts['4']++;
            if (rating >= 3) ratingCounts['3']++;
            if (rating >= 2) ratingCounts['2']++;
            if (rating >= 1) ratingCounts['1']++;
        }});
        
        // Update rating filter options with counts
        const ratingSelect = document.getElementById('ratingFilter');
        ratingSelect.innerHTML = `
            <option value="">All Ratings</option>
            <option value="10">10 (Legendary) (${{ratingCounts['10']}})</option>
            <option value="9">9+ (Must-See) (${{ratingCounts['9']}})</option>
            <option value="8">8+ (Excellent) (${{ratingCounts['8']}})</option>
            <option value="7">7+ (Very Good) (${{ratingCounts['7']}})</option>
            <option value="6">6+ (Good) (${{ratingCounts['6']}})</option>
            <option value="5">5+ (Average) (${{ratingCounts['5']}})</option>
            <option value="4">4+ (Developing) (${{ratingCounts['4']}})</option>
            <option value="3">3+ (Below Average) (${{ratingCounts['3']}})</option>
            <option value="2">2+ (Poor) (${{ratingCounts['2']}})</option>
            <option value="1">1+ (All) (${{ratingCounts['1']}})</option>
        `;
        
        // Count genders and POC (treat empty as Unknown)
        const genderCounts = {{}};
        const pocCounts = {{}};
        artistsData.forEach(a => {{
            const gender = a['Gender of Front Person'] || 'Unknown';
            const poc = a['Front Person of Color?'] || 'Unknown';
            genderCounts[gender] = (genderCounts[gender] || 0) + 1;
            pocCounts[poc] = (pocCounts[poc] || 0) + 1;
        }});
        
        // Update gender checkboxes with counts and hide options with 0 artists
        document.querySelectorAll('#genderFilters label').forEach(label => {{
            const input = label.querySelector('input');
            const value = input.value;
            const count = genderCounts[value] || 0;
            const icon = label.textContent.split(' ')[0]; // Get emoji
            label.innerHTML = `${{input.outerHTML}} ${{icon}} ${{value}} (${{count}})`;
            
            // Hide options with 0 artists
            if (count === 0) {{
                label.style.display = 'none';
            }}
        }});
        
        // Update POC checkboxes with counts and hide options with 0 artists
        document.querySelectorAll('#pocFilters label').forEach(label => {{
            const input = label.querySelector('input');
            const value = input.value;
            const count = pocCounts[value] || 0;
            const icon = label.textContent.split(' ')[0]; // Get emoji
            label.innerHTML = `${{input.outerHTML}} ${{icon}} ${{value}} (${{count}})`;
            
            // Hide options with 0 artists
            if (count === 0) {{
                label.style.display = 'none';
            }}
        }});
        
        // Search and filter functionality
        function filterTable() {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const genreFilter = document.getElementById('genreFilter').value;
            const countryFilter = document.getElementById('countryFilter').value;
            const ratingFilter = document.getElementById('ratingFilter').value;
            const dateFilter = hasScheduleData ? document.getElementById('dateFilter').value : '';
            const stageFilter = hasScheduleData ? document.getElementById('stageFilter').value : '';
            
            // Get checked genders and POC values
            const checkedGenders = Array.from(document.querySelectorAll('#genderFilters input:checked')).map(cb => cb.value);
            const checkedPOC = Array.from(document.querySelectorAll('#pocFilters input:checked')).map(cb => cb.value);
            
            const rows = document.querySelectorAll('#artistTableBody tr');
            let visibleCount = 0;
            
            rows.forEach(row => {{
                const dataIndex = parseInt(row.getAttribute('data-index'));
                const artist = artistsData[dataIndex];
                const searchText = Object.values(artist).join(' ').toLowerCase();
                
                const matchesSearch = !searchTerm || searchText.includes(searchTerm);
                const matchesGenre = !genreFilter || (artist.Genre && artist.Genre.split('/').map(g => g.trim()).includes(genreFilter));
                const matchesCountry = !countryFilter || (artist.Country && artist.Country.split('/').map(c => c.trim()).includes(countryFilter));
                const matchesRating = !ratingFilter || (artist['AI Rating'] && parseFloat(artist['AI Rating']) >= parseFloat(ratingFilter));
                const matchesDate = !dateFilter || (artist['Date'] && artist['Date'] === dateFilter);
                const matchesStage = !stageFilter || (artist['Stage'] && artist['Stage'] === stageFilter);
                const matchesGender = checkedGenders.length === 0 || checkedGenders.includes(artist['Gender of Front Person'] || 'Unknown');
                const matchesPOC = checkedPOC.length === 0 || checkedPOC.includes(artist['Front Person of Color?'] || 'Unknown');
                
                if (matchesSearch && matchesGenre && matchesCountry && matchesRating && matchesDate && matchesStage && matchesGender && matchesPOC) {{
                    row.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    row.classList.add('hidden');
                }}
            }});
            
            document.getElementById('visibleCount').textContent = visibleCount;
            document.getElementById('visibleCountTop').textContent = visibleCount;
        }}
        
        // Sorting functionality
        function sortTable(column) {{
            const tbody = document.getElementById('artistTableBody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Create array of row-data pairs using data-index attribute
            const rowData = rows.map(row => ({{
                row: row,
                data: artistsData[parseInt(row.getAttribute('data-index'))]
            }}));
            
            // Toggle sort direction
            if (currentSort.column === column) {{
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            }} else {{
                currentSort.column = column;
                currentSort.direction = 'asc';
            }}
            
            // Update header styling
            document.querySelectorAll('th').forEach(th => {{
                th.classList.remove('sort-asc', 'sort-desc');
            }});
            
            const header = document.querySelector(`th[data-column="${{column}}"]`);
            header.classList.add(currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc');
            
            // Sort row-data pairs
            rowData.sort((a, b) => {{
                const aValue = a.data[column] || '';
                const bValue = b.data[column] || '';
                
                // Handle numeric sorting for rating
                if (column === 'AI Rating' || column === 'Number of People in Act') {{
                    const aNum = parseFloat(aValue) || 0;
                    const bNum = parseFloat(bValue) || 0;
                    return currentSort.direction === 'asc' ? aNum - bNum : bNum - aNum;
                }}
                
                // String sorting with normalization for special characters
                // Use shared normalization from docs/shared/script.js
                // (window.normalizeForSort is loaded globally)
                const aNormalized = window.normalizeForSort ? window.normalizeForSort(aValue) : aValue;
                const bNormalized = window.normalizeForSort ? window.normalizeForSort(bValue) : bValue;
                const comparison = aNormalized.localeCompare(bNormalized);
                return currentSort.direction === 'asc' ? comparison : -comparison;
            }});
            
            // Reorder DOM
            rowData.forEach(item => tbody.appendChild(item.row));
        }}
        
        // Event listeners
        document.getElementById('searchBox').addEventListener('input', filterTable);
        document.getElementById('genreFilter').addEventListener('change', filterTable);
        document.getElementById('countryFilter').addEventListener('change', filterTable);
        document.getElementById('ratingFilter').addEventListener('change', filterTable);
        
        // Add schedule filter listeners if they exist
        if (hasScheduleData) {{
            const dateFilter = document.getElementById('dateFilter');
            const stageFilter = document.getElementById('stageFilter');
            if (dateFilter) dateFilter.addEventListener('change', filterTable);
            if (stageFilter) stageFilter.addEventListener('change', filterTable);
        }}
        
        // Add listeners for gender and POC checkboxes
        document.querySelectorAll('#genderFilters input, #pocFilters input').forEach(checkbox => {{
            checkbox.addEventListener('change', filterTable);
        }});
        
        document.querySelectorAll('th.sortable').forEach(th => {{
            th.addEventListener('click', () => {{
                sortTable(th.dataset.column);
            }});
        }});
        
        // Sort by Artist name on page load
        sortTable('Artist');
        
        // Rotate message cookie handling
        function getCookie(name) {{
            const value = `; ${{document.cookie}}`;
            const parts = value.split(`; ${{name}}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
        }}
        
        function setCookie(name, value, days) {{
            const expires = new Date(Date.now() + days * 864e5).toUTCString();
            document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=/';
        }}
        
        // Check if user has dismissed the rotate message
        if (getCookie('hideRotateMessage') === 'true') {{
            const rotateMsg = document.getElementById('rotateMessage');
            if (rotateMsg) rotateMsg.style.display = 'none';
        }}
        
        // Handle close button
        const rotateCloseBtn = document.getElementById('rotateClose');
        if (rotateCloseBtn) {{
            rotateCloseBtn.addEventListener('click', function() {{
                const rotateMsg = document.getElementById('rotateMessage');
                if (rotateMsg) {{
                    rotateMsg.style.display = 'none';
                    setCookie('hideRotateMessage', 'true', 365); // Store for 1 year
                }}
            }});
        }}
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <footer style="background: #1a1a2e; color: #ccc; padding: 30px 20px; text-align: center; font-size: 0.9em; margin-top: 40px;">
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
                Last updated: {last_updated_str} • 
                Generated with ❤️ • 
                <a href="https://github.com/frankvaneykelen/lineup-radar" target="_blank" style="color: #00d9ff; text-decoration: none;">
                    <i class="bi bi-github"></i> View on GitHub
                </a> • 
                <a href="{year}.csv" download style="color: #00d9ff; text-decoration: none;">
                    <i class="bi bi-download"></i> Download CSV
                </a>
            </p>
        </div>
    </footer>
    <script src="../../shared/script.js"></script>
    <script src="overrides.js"></script>
    <script defer src="https://frankvaneykelen-umami-app.azurewebsites.net/script.js" data-website-id="c10bb9a5-e39d-4286-a3d9-7c3ca9171d51"></script>
</body>
</html>
"""
    
    # Write HTML file
    output_file = output_path / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated {output_file}")
    print(f"  {len(artists)} artists included")
    print(f"  Output directory: {output_path}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate HTML pages from festival CSV data"
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
    
    # Try multiple locations for CSV file (festival-specific paths)
    csv_locations = [
        f"docs/{config.slug}/{args.year}/{args.year}.csv",  # Docs location (primary)
        f"{config.slug}/{args.year}.csv",  # Festival directory (legacy)
        f"{args.year}.csv",  # Legacy root directory (for down-the-rabbit-hole)
        f"docs/{args.year}/{args.year}.csv",  # Docs subdirectory (legacy)
        f"{args.output}/{args.year}/{args.year}.csv"  # Custom output directory
    ]
    
    csv_file = None
    for location in csv_locations:
        if os.path.exists(location):
            csv_file = location
            break
    
    if not csv_file:
        print(f"Error: CSV file not found. Tried:")
        for location in csv_locations:
            print(f"  - {location}")
        sys.exit(1)
    
    print(f"\n=== Generating HTML for {config.name} {args.year} ===\n")
    generate_html(csv_file, args.output, config)
    
    # Generate README for the festival
    try:
        from generate_festival_readme import generate_readme
        generate_readme(config.slug, args.year)
    except Exception as e:
        print(f"⚠️  Could not generate README: {e}")
    
    print("\n✓ HTML generation complete!")
    print(f"\nTo preview locally, open: {args.output}/{config.slug}/{args.year}/index.html")
    print("To publish via GitHub Pages:")
    print("  1. Commit the generated files")
    print("  2. Enable GitHub Pages in repository settings")
    print(f"  3. Set source to 'main' branch, '/{args.output}' folder")

if __name__ == "__main__":
    main()
