#!/usr/bin/env python3
"""
Generate HTML pages from festival CSV data for GitHub Pages.
Creates interactive tables with sorting and filtering.
"""

import csv
import os
import sys
from pathlib import Path
import json
import re
from festival_helpers import artist_name_to_slug, get_festival_config
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
    
    # Get year from filename (e.g., 2026.csv -> 2026)
    year = Path(csv_file).stem
    
    # Create output directory with festival name
    output_path = Path(output_dir) / config.slug / year
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.name} {year} - Frank's LineupRadar</title>
    <meta name="description" content="Browse the complete {config.name} {year} lineup with artist ratings, genres, and bios. Discover hidden gems and plan your perfect festival schedule.">
    <meta name="keywords" content="{config.name}, {year} lineup, festival artists, music discovery, artist ratings, {config.name} {year}">
    <meta name="author" content="Frank van Eykelen">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="../../shared/styles.css">
    <link rel="stylesheet" href="overrides.css">
</head>
<body>
    <!-- Rotate device message for mobile portrait -->
    <div class="rotate-message">
        <div class="rotate-content">
            <i class="bi bi-phone-landscape" style="font-size: 3rem; margin-bottom: 1rem;"></i>
            <p>For the best experience, please rotate your device to landscape mode</p>
        </div>
    </div>
    
    <div class="container-fluid">
        <header class="artist-header lineup-header">
            <a href="../../index.html" class="btn btn-outline-light home-btn" title="Home">
                <i class="bi bi-house-door-fill"></i>
            </a>
            <div class="artist-header-content">
                <h1>{config.name} {year}</h1>
                <p class="subtitle">Artist Lineup & Appraisals</p>
            </div>
            <div style="width: 120px;"></div>
        </header>
        
        <div class="controls">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <input type="text" id="searchBox" class="search-box" placeholder="Search artists, genres, countries..." style="flex: 1; margin: 0;">
                <div style="margin-left: 15px; color: #666; font-size: 14px; white-space: nowrap;">
                    Showing <strong><span id="visibleCountTop">{len(artists)}</span></strong> of <strong>{len(artists)}</strong> artists
                </div>
            </div>
            
            <div class="filters">
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
                    </div>
                </div>
                
                <div class="filter-group">
                    <label style="margin-bottom: 8px; display: block;">Front Person of Color?</label>
                    <div class="checkbox-group" id="pocFilters">
                        <label><input type="checkbox" value="Yes" checked> Yes</label>
                        <label><input type="checkbox" value="No" checked> No</label>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="table-container">
            <table id="artistTable">
                <thead>
                    <tr>
                        <th class="sortable" data-column="Artist">Artist</th>
                        <th class="sortable" data-column="Genre">Genre</th>
                        <th class="sortable" data-column="Country">Country</th>
                        <th data-column="Bio">Bio</th>
                        <th data-column="My take">My Take</th>
                        <th class="sortable" data-column="My rating">Rating</th>
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
        spotify_html = f'<a href="{escape_html(spotify_link)}" target="_blank" class="spotify-link">Spotify<span class="link-icon">🔗</span></a>' if spotify_link else ''
        
        rating = artist.get('My rating', '').strip()
        rating_html = f'<span class="rating">{escape_html(rating)}</span>' if rating else ''
        
        bio_text = artist.get('Bio', '').strip()
        bio = escape_html(bio_text)
        take = escape_html(artist.get('My take', ''))
        
        # Add Spotify link to bio if available
        if spotify_link:
            bio_with_link = f'{bio}<br><br><a href="{escape_html(spotify_link)}" target="_blank" style="white-space: nowrap; font-size: 0.85em; text-decoration: none;">Spotify<span class="link-icon">🔗</span></a>'
            bio_title = bio_text
        else:
            bio_with_link = bio
            bio_title = bio_text
        
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
        
        html_content += f"""                    <tr data-index="{idx}">
                        <td class="{artist_cell_class}" onclick="window.location.href='{artist_page_url}'"{artist_cell_style}>
                            <strong>{escape_html(artist_name)}</strong>
                        </td>
                        <td>{genre_html}</td>
                        <td>{country_html}</td>
                        <td class="bio" title="{bio_title}">{bio_with_link}</td>
                        <td class="take">{take}</td>
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
        let currentSort = {{ column: null, direction: 'asc' }};
        
        // Populate filter dropdowns with counts
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
        const ratingCounts = {{ '9': 0, '8': 0, '7': 0, '6': 0 }};
        artistsData.forEach(a => {{
            const rating = parseFloat(a['My rating']);
            if (rating >= 9) ratingCounts['9']++;
            if (rating >= 8) ratingCounts['8']++;
            if (rating >= 7) ratingCounts['7']++;
            if (rating >= 6) ratingCounts['6']++;
        }});
        
        // Update rating filter options with counts
        const ratingSelect = document.getElementById('ratingFilter');
        ratingSelect.innerHTML = `
            <option value="">All Ratings</option>
            <option value="9">9+ (Excellent) (${{ratingCounts['9']}})</option>
            <option value="8">8+ (Very Good) (${{ratingCounts['8']}})</option>
            <option value="7">7+ (Good) (${{ratingCounts['7']}})</option>
            <option value="6">6+ (Above Average) (${{ratingCounts['6']}})</option>
        `;
        
        // Count genders and POC
        const genderCounts = {{}};
        const pocCounts = {{}};
        artistsData.forEach(a => {{
            const gender = a['Gender of Front Person'] || '';
            const poc = a['Front Person of Color?'] || '';
            if (gender) genderCounts[gender] = (genderCounts[gender] || 0) + 1;
            if (poc) pocCounts[poc] = (pocCounts[poc] || 0) + 1;
        }});
        
        // Update gender checkboxes with counts
        document.querySelectorAll('#genderFilters label').forEach(label => {{
            const input = label.querySelector('input');
            const value = input.value;
            const count = genderCounts[value] || 0;
            const icon = label.textContent.split(' ')[0]; // Get emoji
            label.innerHTML = `${{input.outerHTML}} ${{icon}} ${{value}} (${{count}})`;
        }});
        
        // Update POC checkboxes with counts
        document.querySelectorAll('#pocFilters label').forEach(label => {{
            const input = label.querySelector('input');
            const value = input.value;
            const count = pocCounts[value] || 0;
            const icon = label.textContent.split(' ')[0]; // Get emoji
            label.innerHTML = `${{input.outerHTML}} ${{icon}} ${{value}} (${{count}})`;
        }});
        
        // Search and filter functionality
        function filterTable() {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const genreFilter = document.getElementById('genreFilter').value;
            const countryFilter = document.getElementById('countryFilter').value;
            const ratingFilter = document.getElementById('ratingFilter').value;
            
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
                const matchesRating = !ratingFilter || (artist['My rating'] && parseFloat(artist['My rating']) >= parseFloat(ratingFilter));
                const matchesGender = checkedGenders.length === 0 || checkedGenders.includes(artist['Gender of Front Person']);
                const matchesPOC = checkedPOC.length === 0 || checkedPOC.includes(artist['Front Person of Color?']);
                
                if (matchesSearch && matchesGenre && matchesCountry && matchesRating && matchesGender && matchesPOC) {{
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
                if (column === 'My rating' || column === 'Number of People in Act') {{
                    const aNum = parseFloat(aValue) || 0;
                    const bNum = parseFloat(bValue) || 0;
                    return currentSort.direction === 'asc' ? aNum - bNum : bNum - aNum;
                }}
                
                // String sorting with normalization for special characters
                const normalizeForSort = (str) => {{
                    let normalized = str.toString()
                        .replace(/¥/g, 'Y')
                        .replace(/Ø/g, 'O')
                        .replace(/\\$/g, 'S')
                        .replace(/€/g, 'E')
                        .replace(/1/g, 'I')
                        .normalize('NFD')
                        .replace(/[\\u0300-\\u036f]/g, ''); // Remove diacritics
                    
                    // Remove leading articles for sorting (The, De, etc.)
                    normalized = normalized.replace(/^(The|De|Le|La|Les|Los|Las|El|Il|Die|Der|Das)\\s+/i, '');
                    
                    return normalized;
                }};
                
                const aNormalized = normalizeForSort(aValue);
                const bNormalized = normalizeForSort(bValue);
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
                Generated with ❤️ • 
                <a href="https://github.com/frankvaneykelen/lineup-radar" target="_blank" style="color: #00d9ff; text-decoration: none;">
                    <i class="bi bi-github"></i> View on GitHub
                </a>
            </p>
        </div>
    </footer>
    <script src="../../shared/script.js"></script>
    <script src="overrides.js"></script>
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
        f"{config.slug}/{args.year}.csv",  # Festival directory
        f"{args.year}.csv",  # Legacy root directory (for down-the-rabbit-hole)
        f"docs/{args.year}/{args.year}.csv",  # Docs subdirectory
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
    print("\n✓ HTML generation complete!")
    print(f"\nTo preview locally, open: {args.output}/{config.slug}/{args.year}/index.html")
    print("To publish via GitHub Pages:")
    print("  1. Commit the generated files")
    print("  2. Enable GitHub Pages in repository settings")
    print(f"  3. Set source to 'main' branch, '/{args.output}' folder")

if __name__ == "__main__":
    main()
