#!/usr/bin/env python3
"""
Generate an 'about' profile for a festival year.

Creates `about.json` with computed statistics and an AI-written profile (optional),
and a simple `about.html` page summarising the findings.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import json
import os
from datetime import datetime, timezone
import argparse

from festival_helpers import get_festival_config, generate_hamburger_menu
from festival_helpers.ai_client import enrich_with_ai
from festival_helpers.text_utils import markdown_to_html


def load_artists(csv_file: Path) -> list[dict]:
    artists = []
    with csv_file.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            artists.append(row)
    return artists


def safe_float(val):
    try:
        return float(val)
    except Exception:
        return None


def compute_stats(artists: list[dict]) -> dict:
    stats = {}
    stats['total_artists'] = len(artists)

    # Genres
    genre_counts = {}
    dj_count = 0
    for a in artists:
        g = (a.get('Genre') or '').strip()
        name = (a.get('Artist') or '').lower()
        bio = (a.get('Bio') or '')
        if 'dj' in (g.lower() if g else '') or 'dj' in name or 'b2b' in name or 'dj' in bio.lower():
            dj_count += 1
        if g:
            for part in [p.strip() for p in g.split('/') if p.strip()]:
                genre_counts[part] = genre_counts.get(part, 0) + 1

    stats['genre_counts'] = dict(sorted(genre_counts.items(), key=lambda kv: -kv[1]))
    stats['dj_count'] = dj_count

    # Countries
    country_counts = {}
    for a in artists:
        c = (a.get('Country') or '').strip()
        if c:
            for part in [p.strip() for p in c.split('/') if p.strip()]:
                country_counts[part] = country_counts.get(part, 0) + 1
    stats['country_counts'] = dict(sorted(country_counts.items(), key=lambda kv: -kv[1]))

    # Gender and POC
    gender_counts = {}
    poc_counts = {}
    for a in artists:
        gender = (a.get('Gender of Front Person') or 'Unknown').strip() or 'Unknown'
        poc = (a.get('Front Person of Color?') or 'Unknown').strip() or 'Unknown'
        gender_counts[gender] = gender_counts.get(gender, 0) + 1
        poc_counts[poc] = poc_counts.get(poc, 0) + 1
    stats['gender_counts'] = gender_counts
    stats['poc_counts'] = poc_counts

    # Ratings
    ratings = [safe_float(a.get('AI Rating')) for a in artists]
    rated = [r for r in ratings if r is not None]
    if rated:
        stats['average_rating'] = round(sum(rated) / len(rated), 2)
        # Distribution by ranges
        dist = {
            '9-10': 0,
            '8-9': 0,
            '7-8': 0,
            '6-7': 0,
            '5-6': 0
        }
        for r in rated:
            if r >= 9:
                dist['9-10'] += 1
            elif r >= 8:
                dist['8-9'] += 1
            elif r >= 7:
                dist['7-8'] += 1
            elif r >= 6:
                dist['6-7'] += 1
            elif r >= 5:
                dist['5-6'] += 1
        # Add unrated count
        unrated_count = len(artists) - len(rated)
        if unrated_count > 0:
            dist['Unrated'] = unrated_count
        # Remove zero entries
        stats['rating_counts'] = {k: v for k, v in dist.items() if v > 0}
    else:
        stats['average_rating'] = None
        stats['rating_counts'] = {'Unrated': len(artists)}

    # Other counts
    stats['has_spotify_links'] = sum(1 for a in artists if (a.get('Spotify link') or '').strip())

    return stats


def compare_with_previous(csv_path: Path, artists: list[dict]) -> dict:
    # Try to find previous year file and compute simple deltas for top genres and avg rating
    prev_stats = {}
    try:
        year = int(csv_path.stem)
    except Exception:
        return {}
    prev_file = csv_path.parent.parent / str(year - 1) / f"{year-1}.csv"
    if prev_file.exists():
        prev_artists = load_artists(prev_file)
        prev_stats_calc = compute_stats(prev_artists)
        current = compute_stats(artists)
        deltas = {}
        for g, cnt in list(current['genre_counts'].items())[:5]:
            prev_cnt = prev_stats_calc.get('genre_counts', {}).get(g, 0)
            deltas[g] = cnt - prev_cnt
        prev_stats = {'prev_year': year-1, 'deltas_top_genres': deltas, 'prev_average_rating': prev_stats_calc.get('average_rating')}
    return prev_stats


def generate_profile_text(config, stats: dict, prev: dict, use_ai: bool = False) -> str:
    # Build a prompt for AI summarization
    prompt_lines = []
    prompt_lines.append(f"Write a short festival profile for '{config.name}' {stats.get('year','')} based on the following statistics:")
    prompt_lines.append(json.dumps(stats, indent=2))
    if prev:
        prompt_lines.append("Compare to the previous year:")
        prompt_lines.append(json.dumps(prev, indent=2))
    prompt_lines.append("Focus on common ground between artists, notable trends, and diversity (gender, country, person-of-color measures). Keep it concise (approx 3 short paragraphs).")
    prompt = "\n\n".join(prompt_lines)
    if use_ai:
        try:
            return enrich_with_ai(prompt, temperature=0.6)
        except Exception as e:
            print(f"⚠️ AI generation failed: {e}")

    # Fallback to a simple template (used when --ai isn't provided or AI fails)
    top_genres = ', '.join(list(stats.get('genre_counts', {}).keys())[:3])
    
    # Format gender distribution
    gender_counts = stats.get('gender_counts', {})
    gender_parts = []
    if gender_counts.get('Male'):
        gender_parts.append(f"{gender_counts['Male']} male")
    if gender_counts.get('Female'):
        gender_parts.append(f"{gender_counts['Female']} female")
    if gender_counts.get('Mixed'):
        gender_parts.append(f"{gender_counts['Mixed']} mixed/group")
    if gender_counts.get('Non-binary'):
        gender_parts.append(f"{gender_counts['Non-binary']} non-binary")
    gender_text = ', '.join(gender_parts) if gender_parts else 'no gender data'
    
    # Format POC distribution
    poc_counts = stats.get('poc_counts', {})
    poc_yes = poc_counts.get('Yes', 0)
    poc_total = sum(poc_counts.values()) - poc_counts.get('Unknown', 0)
    poc_text = f"{poc_yes} artists of color" if poc_total > 0 else "no diversity data"
    
    return (
        f"{config.name} {stats.get('year','')} features {stats.get('total_artists')} artists. "
        f"Top genres include {top_genres}. Average user rating: {stats.get('average_rating')}. "
        f"The lineup includes {gender_text}, with {poc_text}."
    )



def write_outputs(output_dir: Path, about: dict, html_profile: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'about.json'
    html_path = output_dir / 'about.html'
    with json_path.open('w', encoding='utf-8') as f:
        json.dump(about, f, indent=2, ensure_ascii=False)
    with html_path.open('w', encoding='utf-8') as f:
        f.write(html_profile)
    print(f"✓ Wrote {json_path} and {html_path}")


def render_html(config, stats, profile_text, start_date=None, end_date=None):
    # Generate menu HTML (use escaped=False since we'll manually escape in the f-string)
    menu_html = generate_hamburger_menu(path_prefix="../../", escaped=False)
    
    # Format festival dates if available
    date_display = ''
    if start_date and end_date:
        # Convert from YYYY-MM-DD to human-readable format
        from datetime import datetime as dt
        try:
            start_dt = dt.strptime(start_date, '%Y-%m-%d')
            end_dt = dt.strptime(end_date, '%Y-%m-%d')
            if start_date == end_date:
                # Single day festival
                date_display = start_dt.strftime('%B %d, %Y')
            else:
                # Multi-day festival
                if start_dt.month == end_dt.month and start_dt.year == end_dt.year:
                    # Same month and year
                    date_display = f"{start_dt.strftime('%B %d')} - {end_dt.strftime('%d, %Y')}"
                elif start_dt.year == end_dt.year:
                    # Same year, different months
                    date_display = f"{start_dt.strftime('%B %d')} - {end_dt.strftime('%B %d, %Y')}"
                else:
                    # Different years
                    date_display = f"{start_dt.strftime('%B %d, %Y')} - {end_dt.strftime('%B %d, %Y')}"
        except ValueError:
            pass
    
    # Build formatted statistics tables
    genre_rows = ''.join([f'<tr><td>{genre}</td><td>{count}</td></tr>' 
                          for genre, count in list(stats.get('genre_counts', {}).items())[:10]])
    country_rows = ''.join([f'<tr><td>{country}</td><td>{count}</td></tr>' 
                            for country, count in list(stats.get('country_counts', {}).items())[:10]])
    gender_rows = ''.join([f'<tr><td>{gender}</td><td>{count}</td></tr>' 
                           for gender, count in stats.get('gender_counts', {}).items()])
    poc_rows = ''.join([f'<tr><td>{poc}</td><td>{count}</td></tr>' 
                        for poc, count in stats.get('poc_counts', {}).items()])
    rating_rows = ''.join([f'<tr><td>{rating}</td><td>{count}</td></tr>' 
                           for rating, count in sorted(stats.get('rating_distribution', {}).items(), key=lambda x: -int(x[0]))])
    
    title = f"{config.name} {stats.get('year','')} About - Frank's LineupRadar"
    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{title}</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <link rel=\"stylesheet\" href=\"../../shared/styles.css\">
    <style>
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }}
        .stat-card {{
            background: var(--card-bg, #ffffff);
            border: 1px solid var(--border-color, #dee2e6);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .stat-card h3 {{
            margin-top: 0;
            margin-bottom: 1rem;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--heading-color, #212529);
            border-bottom: 2px solid var(--primary-color, #0d6efd);
            padding-bottom: 0.5rem;
        }}
        .stat-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .stat-table td {{
            padding: 0.6rem 0.5rem;
            border-bottom: 1px solid var(--border-color, #e9ecef);
            font-size: 0.95rem;
        }}
        .stat-table tr:last-child td {{
            border-bottom: none;
        }}
        .stat-table td:first-child {{
            color: var(--text-color, #495057);
        }}
        .stat-table td:last-child {{
            text-align: right;
            font-weight: 600;
            color: var(--primary-color, #0d6efd);
        }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color, #0d6efd);
            line-height: 1;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9rem;
            color: var(--text-muted, #6c757d);
            margin-top: 0.25rem;
        }}
        .overview-stat {{
            margin-bottom: 1.5rem;
        }}
        .overview-stat:last-child {{
            margin-bottom: 0;
        }}
        .profile-text {{
            font-size: 1.05rem;
            line-height: 1.7;
            color: var(--text-color, #212529);
            margin-bottom: 2rem;
        }}
        body[data-theme=\"dark\"] .stat-card {{
            background: #2d2d2d;
            border-color: #444;
        }}
        body[data-theme=\"dark\"] .stat-table td {{
            border-bottom-color: #444;
        }}
        body[data-theme=\"dark\"] .stat-table td:first-child {{
            color: #adb5bd;
        }}
    </style>
</head>
<body>
    <div class=\"container-fluid\">
        <header class=\"artist-header lineup-header\">
            <div class=\"hamburger-menu\">
                <button id=\"hamburgerBtn\" class=\"btn btn-outline-light hamburger-btn\" title=\"Menu\">
                    <i class=\"bi bi-list\"></i>
                </button>
                <div id=\"dropdownMenu\" class=\"dropdown-menu-custom\">
                    <a href=\"../../index.html\" class=\"home-link\">
                        <i class=\"bi bi-house-door-fill\"></i> Home
                    </a>
{menu_html}
                </div>
            </div>
            <div class="page-header-content">
                <h1>About {config.name} {stats.get('year','')}</h1>
                {'<p class="festival-description" style="font-size: 0.95em; opacity: 0.85; margin-top: 0.5rem; max-width: 800px;">' + config.description + '</p>' if config.description else ''}
                {'<p class="festival-dates" style="font-size: 1.1em; font-weight: 600; margin-top: 0.75rem; color: var(--primary-color, #0d6efd);">' + date_display + '</p>' if date_display else ''}
                <p class="subtitle" style="font-size: 0.8em; opacity: 0.7; margin-top: 0.5rem;">
                    About page generated: {datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}
                    {' | <a href="' + config.lineup_url + '" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;">Festival Site</a>' if config.lineup_url else ''}
                </p>
            </div>
        </header>
        
        <div class="container-fluid" style="max-width: 1400px; padding: 2rem 1rem;">
            <section class="mb-5">
                <h2 style="margin-bottom: 1.5rem; font-size: 1.75rem; font-weight: 600;">Festival Profile</h2>
                <div class="profile-text">{markdown_to_html(profile_text)}</div>
            </section>
            
            <section>
                <h2 style=\"margin-bottom: 1rem; font-size: 1.75rem; font-weight: 600;\">Festival Statistics</h2>
                <div class=\"stats-grid\">
                    <div class=\"stat-card\">
                        <h3>Overview</h3>
                        <div class=\"overview-stat\">
                            <span class=\"stat-number\">{stats.get('total_artists', 0)}</span>
                            <div class=\"stat-label\">Total Artists</div>
                        </div>
                        <div class=\"overview-stat\">
                            <span class=\"stat-number\">{stats.get('average_rating', 'N/A')}</span>
                            <div class=\"stat-label\">Average Rating</div>
                        </div>
                        <div class=\"overview-stat\">
                            <span class=\"stat-number\">{stats.get('dj_count', 0)}</span>
                            <div class=\"stat-label\">DJs/Electronic Acts</div>
                        </div>
                        <div class=\"overview-stat\">
                            <span class=\"stat-number\">{stats.get('has_spotify_links', 0)}</span>
                            <div class=\"stat-label\">Artists with Spotify Links</div>
                        </div>
                    </div>
                    
                    <div class=\"stat-card\">
                        <h3>Top Genres</h3>
                        <table class=\"stat-table\">
                            {genre_rows if genre_rows else '<tr><td colspan=\"2\" style=\"text-align: center; color: #6c757d;\">No data</td></tr>'}
                        </table>
                    </div>
                    
                    <div class=\"stat-card\">
                        <h3>Top Countries</h3>
                        <table class=\"stat-table\">
                            {country_rows if country_rows else '<tr><td colspan=\"2\" style=\"text-align: center; color: #6c757d;\">No data</td></tr>'}
                        </table>
                    </div>
                </div>
                
                <div class=\"stats-grid\" style=\"margin-top: 1.5rem;\">
                    <div class=\"stat-card\">
                        <h3>Gender Distribution</h3>
                        <canvas id=\"genderChart\" width=\"300\" height=\"300\"></canvas>
                    </div>
                    
                    <div class=\"stat-card\">
                        <h3>Artists of Color</h3>
                        <canvas id=\"pocChart\" width=\"300\" height=\"300\"></canvas>
                    </div>
                    
                    <div class=\"stat-card\">
                        <h3>Rating Distribution</h3>
                        <canvas id=\"ratingChart\" width=\"300\" height=\"300\"></canvas>
                    </div>
                </div>
            </section>
        </div>
    </div>
    
    <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js\"></script>
    
    <footer style=\"background: #1a1a2e; color: #ccc; padding: 30px 20px; text-align: center; font-size: 0.9em; margin-top: 40px;\">
        <button class=\"dark-mode-toggle\" id=\"darkModeToggle\" title=\"Toggle dark mode\">
            <i class=\"bi bi-moon-fill\"></i>
        </button>
        <div>
            <p style=\"margin-bottom: 15px;\">
                <strong>Content Notice:</strong> These pages combine content scraped from the 
                <a href=\"{config.lineup_url or '#'}\" target=\"_blank\" style=\"color: #00d9ff; text-decoration: none;\">{config.name} festival website</a>
                with AI-generated content using <strong>Azure OpenAI GPT-4o</strong>.
            </p>
            <p style=\"margin-bottom: 15px;\">
                <strong>⚠️ Disclaimer:</strong> Information may be incomplete or inaccurate due to automated generation and web scraping. 
                Please verify critical details on official sources.
            </p>
            <p style=\"margin-bottom: 0;\">
                Generated with ❤️ • 
                <a href=\"https://github.com/frankvaneykelen/lineup-radar\" target=\"_blank\" style=\"color: #00d9ff; text-decoration: none;\">
                    <i class=\"bi bi-github\"></i> View on GitHub
                </a>
            </p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="../../shared/script.js"></script>
    <script>
        // Prepare data for charts
        const genderData = {json.dumps(dict(stats.get('gender_counts', {})))};
        const pocData = {json.dumps(dict(stats.get('poc_counts', {})))};
        const ratingData = {json.dumps(dict(stats.get('rating_counts', {})))};
        
        // Color schemes
        const genderColors = {{
            'Male': '#3b82f6',
            'Female': '#ec4899',
            'Non-binary': '#8b5cf6',
            'Mixed': '#10b981',
            'Unknown': '#6b7280'
        }};
        
        const pocColors = {{
            'Yes': '#f59e0b',
            'No': '#6b7280',
            'Unknown': '#d1d5db'
        }};
        
        const ratingColors = {{
            '9-10': '#10b981',
            '8-9': '#3b82f6',
            '7-8': '#8b5cf6',
            '6-7': '#f59e0b',
            '5-6': '#ef4444',
            'Unrated': '#6b7280'
        }};
        
        // Helper function to create pie chart
        function createPieChart(canvasId, data, colorMap) {{
            const ctx = document.getElementById(canvasId);
            if (!ctx) return;
            
            const labels = Object.keys(data);
            const values = Object.values(data);
            const colors = labels.map(label => colorMap[label] || '#6b7280');
            
            new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: labels,
                    datasets: [{{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: document.body.getAttribute('data-theme') === 'dark' ? '#1a1a2e' : '#ffffff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                color: document.body.getAttribute('data-theme') === 'dark' ? '#e0e0e0' : '#212529',
                                padding: 10,
                                font: {{
                                    size: 12
                                }}
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${{label}}: ${{value}} (${{percentage}}%)`;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Create charts
        createPieChart('genderChart', genderData, genderColors);
        createPieChart('pocChart', pocData, pocColors);
        createPieChart('ratingChart', ratingData, ratingColors);
        
        // Update chart colors when dark mode toggles
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {{
            darkModeToggle.addEventListener('click', function() {{
                setTimeout(() => {{
                    location.reload();
                }}, 100);
            }});
        }}
    </script>
</body>
</html>
"""
    return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--festival', required=True)
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--output', default='docs')
    parser.add_argument('--ai', action='store_true', help='Use Azure OpenAI to generate profile')
    args = parser.parse_args()

    config = get_festival_config(args.festival, args.year)
    csv_file = Path(f"docs/{config.slug}/{args.year}/{args.year}.csv")
    if not csv_file.exists():
        print(f"✗ CSV not found: {csv_file}")
        return

    artists = load_artists(csv_file)
    stats = compute_stats(artists)
    stats['year'] = args.year
    prev = compare_with_previous(csv_file, artists)

    # Try to read existing about.json to get start_date and end_date if they exist
    out_dir = Path(args.output) / config.slug / str(args.year)
    existing_about_file = out_dir / 'about.json'
    start_date = None
    end_date = None
    if existing_about_file.exists():
        try:
            with existing_about_file.open('r', encoding='utf-8') as f:
                existing_about = json.load(f)
                start_date = existing_about.get('start_date')
                end_date = existing_about.get('end_date')
        except Exception:
            pass

    profile_text = ''
    # Only call the networked AI when --ai is explicitly provided. Otherwise use fallback text.
    profile_text = generate_profile_text(config, stats, prev, use_ai=args.ai)

    about = {
        'festival': config.slug,
        'name': config.name,
        'year': args.year,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'config_properties': {k: v for k, v in config.__dict__.items() if not k.startswith('_')},
        'stats': stats,
        'previous_year_comparison': prev,
        'ai_profile': profile_text
    }
    
    # Preserve start_date and end_date if they exist
    if start_date:
        about['start_date'] = start_date
    if end_date:
        about['end_date'] = end_date

    html = render_html(config, stats, profile_text, start_date, end_date)
    write_outputs(out_dir, about, html)
    
    # Generate/update README for this festival edition
    try:
        from generate_festival_readme import generate_readme
        generate_readme(args.festival, args.year)
    except Exception:
        pass  # Silent fail - README is nice to have but not critical


if __name__ == '__main__':
    main()
