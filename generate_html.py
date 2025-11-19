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

def generate_html(csv_file, output_dir):
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
    
    # Create output directory
    output_path = Path(output_dir) / year
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Down The Rabbit Hole {year} - Artist Lineup</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .controls {{
            padding: 30px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .search-box {{
            width: 100%;
            padding: 12px 20px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            transition: border-color 0.3s;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .filters {{
            display: flex;
            gap: 15px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        .filter-group {{
            flex: 1;
            min-width: 200px;
        }}
        
        .filter-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }}
        
        .filter-group select {{
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }}
        
        .table-container {{
            overflow-x: auto;
            padding: 0 40px 40px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}
        
        th:hover {{
            background: #5568d3;
        }}
        
        th.sortable::after {{
            content: ' ⇅';
            opacity: 0.5;
        }}
        
        th.sort-asc::after {{
            content: ' ↑';
            opacity: 1;
        }}
        
        th.sort-desc::after {{
            content: ' ↓';
            opacity: 1;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        tr.hidden {{
            display: none;
        }}
        
        .rating {{
            font-weight: 700;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .spotify-link {{
            display: inline-block;
            padding: 6px 12px;
            background: #1DB954;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            transition: background 0.3s;
        }}
        
        .spotify-link:hover {{
            background: #1ed760;
        }}
        
        .bio {{
            max-width: 400px;
            line-height: 1.5;
        }}
        
        .take {{
            max-width: 400px;
            font-style: italic;
            color: #555;
        }}
        
        .stats {{
            padding: 20px 40px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #666;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            background: #e9ecef;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            color: #495057;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            header {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 1.8em;
            }}
            
            .controls, .table-container {{
                padding: 20px;
            }}
            
            th, td {{
                padding: 8px 6px;
                font-size: 14px;
            }}
            
            .bio, .take {{
                max-width: 200px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎵 Down The Rabbit Hole {year}</h1>
            <p class="subtitle">Artist Lineup & Reviews</p>
        </header>
        
        <div class="controls">
            <input type="text" id="searchBox" class="search-box" placeholder="Search artists, genres, countries...">
            
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
                        <th data-column="Spotify link">Spotify</th>
                        <th class="sortable" data-column="Number of People in Act">Size</th>
                        <th class="sortable" data-column="Gender of Front Person">Gender</th>
                        <th class="sortable" data-column="Front Person of Color?">POC</th>
                    </tr>
                </thead>
                <tbody id="artistTableBody">
"""
    
    # Add table rows
    for artist in artists:
        spotify_link = artist.get('Spotify link', '').strip()
        spotify_html = f'<a href="{escape_html(spotify_link)}" target="_blank" class="spotify-link">🎧 Listen</a>' if spotify_link else ''
        
        rating = artist.get('My rating', '').strip()
        rating_html = f'<span class="rating">{escape_html(rating)}</span>' if rating else ''
        
        bio = escape_html(artist.get('Bio', ''))
        take = escape_html(artist.get('My take', ''))
        
        html_content += f"""                    <tr>
                        <td><strong>{escape_html(artist.get('Artist', ''))}</strong></td>
                        <td><span class="badge">{escape_html(artist.get('Genre', ''))}</span></td>
                        <td>{escape_html(artist.get('Country', ''))}</td>
                        <td class="bio" title="{bio}">{bio}</td>
                        <td class="take">{take}</td>
                        <td>{rating_html}</td>
                        <td>{spotify_html}</td>
                        <td>{escape_html(artist.get('Number of People in Act', ''))}</td>
                        <td>{escape_html(artist.get('Gender of Front Person', ''))}</td>
                        <td>{escape_html(artist.get('Front Person of Color?', ''))}</td>
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
        
        // Populate filter dropdowns
        const genres = [...new Set(artistsData.map(a => a.Genre).filter(Boolean))].sort();
        const countries = [...new Set(artistsData.map(a => a.Country).filter(Boolean))].sort();
        
        const genreSelect = document.getElementById('genreFilter');
        genres.forEach(genre => {{
            const option = document.createElement('option');
            option.value = genre;
            option.textContent = genre;
            genreSelect.appendChild(option);
        }});
        
        const countrySelect = document.getElementById('countryFilter');
        countries.forEach(country => {{
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            countrySelect.appendChild(option);
        }});
        
        // Search and filter functionality
        function filterTable() {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const genreFilter = document.getElementById('genreFilter').value;
            const countryFilter = document.getElementById('countryFilter').value;
            const ratingFilter = document.getElementById('ratingFilter').value;
            
            const rows = document.querySelectorAll('#artistTableBody tr');
            let visibleCount = 0;
            
            rows.forEach((row, index) => {{
                const artist = artistsData[index];
                const searchText = Object.values(artist).join(' ').toLowerCase();
                
                const matchesSearch = !searchTerm || searchText.includes(searchTerm);
                const matchesGenre = !genreFilter || artist.Genre === genreFilter;
                    const matchesCountry = !countryFilter || (artist.Country && artist.Country.toLowerCase().includes(countryFilter.toLowerCase()));
                const matchesRating = !ratingFilter || (artist['My rating'] && parseFloat(artist['My rating']) >= parseFloat(ratingFilter));
                
                if (matchesSearch && matchesGenre && matchesCountry && matchesRating) {{
                    row.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    row.classList.add('hidden');
                }}
            }});
            
            document.getElementById('visibleCount').textContent = visibleCount;
        }}
        
        // Sorting functionality
        function sortTable(column) {{
            const tbody = document.getElementById('artistTableBody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
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
            
            // Sort rows
            rows.sort((a, b) => {{
                const aIndex = rows.indexOf(a);
                const bIndex = rows.indexOf(b);
                const aValue = artistsData[aIndex][column] || '';
                const bValue = artistsData[bIndex][column] || '';
                
                // Handle numeric sorting for rating
                if (column === 'My rating' || column === 'Number of People in Act') {{
                    const aNum = parseFloat(aValue) || 0;
                    const bNum = parseFloat(bValue) || 0;
                    return currentSort.direction === 'asc' ? aNum - bNum : bNum - aNum;
                }}
                
                // String sorting
                const comparison = aValue.toString().localeCompare(bValue.toString());
                return currentSort.direction === 'asc' ? comparison : -comparison;
            }});
            
            // Reorder DOM
            rows.forEach(row => tbody.appendChild(row));
        }}
        
        // Event listeners
        document.getElementById('searchBox').addEventListener('input', filterTable);
        document.getElementById('genreFilter').addEventListener('change', filterTable);
        document.getElementById('countryFilter').addEventListener('change', filterTable);
        document.getElementById('ratingFilter').addEventListener('change', filterTable);
        
        document.querySelectorAll('th.sortable').forEach(th => {{
            th.addEventListener('click', () => {{
                sortTable(th.dataset.column);
            }});
        }});
    </script>
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
    if len(sys.argv) < 2:
        print("Usage: python generate_html.py <csv_file> [output_dir]")
        print("Example: python generate_html.py 2026.csv docs")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "docs"
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)
    
    print(f"\n=== Generating HTML from {csv_file} ===\n")
    generate_html(csv_file, output_dir)
    print("\n✓ HTML generation complete!")
    print(f"\nTo preview locally, open: {output_dir}/{Path(csv_file).stem}/index.html")
    print("To publish via GitHub Pages:")
    print("  1. Commit the generated files")
    print("  2. Enable GitHub Pages in repository settings")
    print(f"  3. Set source to 'main' branch, '/{output_dir}' folder")

if __name__ == "__main__":
    main()
