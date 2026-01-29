#!/usr/bin/env python3
"""
Generate festival timetable (blokkenschema) HTML page.
Shows a visual schedule grid with stages as rows and time slots as columns.
"""

import sys
from pathlib import Path
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import html

# Add scripts directory to path for helpers module
sys.path.insert(0, str(Path(__file__).parent))

from helpers import (
    artist_name_to_slug,
    get_festival_config,
    generate_hamburger_menu
)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return html.escape(str(text))


def parse_time(time_str: str) -> Optional[datetime]:
    """Parse time string in HH:MM format. Handles 24:00 as 00:00 next day."""
    if not time_str:
        return None
    try:
        # Handle 24:00 as midnight (00:00 of next day)
        if time_str == '24:00':
            return datetime.strptime('00:00', '%H:%M') + timedelta(days=1)
        return datetime.strptime(time_str, '%H:%M')
    except:
        return None


def generate_time_slots(start_hour: int, end_hour: int, granularity: int = 5) -> List[str]:
    """Generate time slots from start to end hour with given granularity in minutes."""
    slots = []
    current = datetime.strptime(f"{start_hour:02d}:00", '%H:%M')
    
    # Handle overnight events (end_hour might be less than start_hour or > 24)
    if end_hour <= start_hour:
        end_hour += 24
    
    end = datetime.strptime(f"{end_hour % 24:02d}:00", '%H:%M')
    if end_hour >= 24:
        end += timedelta(days=1)
    
    while current <= end:
        hour = current.hour
        if hour == 0 and current >= datetime.strptime("00:00", '%H:%M'):
            # Late night hours - keep as 00:xx, 01:xx etc
            slots.append(current.strftime('%H:%M'))
        else:
            slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=granularity)
    
    return slots


def get_performance_span(start_time: str, end_time: str, time_slots: List[str], granularity: int) -> tuple:
    """Calculate the column span and starting column for a performance."""
    if not start_time or not end_time:
        return (0, 0)
    
    try:
        # Find start column
        start_col = time_slots.index(start_time) if start_time in time_slots else -1
        if start_col == -1:
            return (0, 0)
        
        # Calculate duration in minutes
        start_dt = parse_time(start_time)
        end_dt = parse_time(end_time)
        
        if not start_dt or not end_dt:
            return (0, 0)
        
        # Handle overnight performances
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        span = max(1, duration_minutes // granularity)
        
        return (start_col, span)
    except:
        return (0, 0)


def generate_timetable_html(csv_file: Path, output_dir: Path, festival: str = 'alkmaarse-eigenste'):
    """Generate timetable HTML page."""
    
    # Read CSV data
    performances = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        performances = list(reader)
    
    # Get festival config
    year = csv_file.stem
    config = get_festival_config(festival, int(year))
    
    # Read settings.json for stage order
    settings_file = output_dir / festival / year / "settings.json"
    stages_order = []
    if settings_file.exists():
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings_data = json.load(f)
            stages_order = settings_data.get('stages', [])
    
    # Filter performances with schedule data and group by date
    scheduled_performances = {}
    for perf in performances:
        date = perf.get('Date', '').strip()
        stage = perf.get('Stage', '').strip()
        start_time = perf.get('Start Time', '').strip()
        
        if date and stage and start_time:
            if date not in scheduled_performances:
                scheduled_performances[date] = []
            scheduled_performances[date].append(perf)
    
    if not scheduled_performances:
        print("No schedule data found in CSV")
        return
    
    # Determine time range (find earliest and latest times)
    all_times = []
    for perfs in scheduled_performances.values():
        for perf in perfs:
            start = perf.get('Start Time', '').strip()
            end = perf.get('End Time', '').strip()
            if start:
                all_times.append(start)
            if end:
                all_times.append(end)
    
    # Parse times to determine range
    time_objects = [parse_time(t) for t in all_times if parse_time(t)]
    if not time_objects:
        print("No valid times found")
        return
    
    min_hour = min(t.hour for t in time_objects)
    max_hour = max(t.hour for t in time_objects)
    
    # Adjust for late-night events (handle 00:xx as 24:xx)
    if min_hour <= 6 and max_hour >= 19:
        # Likely overnight event
        start_hour = 19
        end_hour = 26  # 02:00 AM
    else:
        start_hour = min_hour
        end_hour = max_hour + 1
    
    # Generate time slots
    granularity = 5  # 5-minute intervals
    time_slots = generate_time_slots(start_hour, end_hour, granularity)
    
    # Stage colors - define colors for all festivals
    stage_colors = {
        # Alkmaarse Eigenste
        "Grote zaal": "#FF6B6B",      # Red
        "Kleine zaal": "#4ECDC4",     # Teal
        "Bezemhok": "#95E1D3",        # Light teal
        "Bus": "#FFE66D",             # Yellow
        "Overloop": "#C7CEEA",        # Lavender
        "Sluis": "#FF9A9E",           # Pink
        
        # Footprints Festival (colors from official poster design)
        "Pandora": "#FF8C42",         # Bright Orange
        "Hertz": "#00D4FF",           # Cyan
        "Cloud Nine": "#40E0D0",      # Turquoise
        "Club Nine": "#FFD93D",       # Yellow
        "Pandora Foyer": "#FF6B9D",   # Coral Pink
        "Park 6": "#8B7FD6"           # Purple
    }
    
    # Get unique stages and sort them according to stages_order
    unique_stages = set()
    for perfs in scheduled_performances.values():
        for perf in perfs:
            stage = perf.get('Stage', '').strip()
            if stage:
                unique_stages.add(stage)
    
    # Sort stages according to predefined order, put unknown stages at end
    sorted_stages = []
    for stage in stages_order:
        if stage in unique_stages:
            sorted_stages.append(stage)
    
    # Add any stages not in the predefined order
    for stage in sorted(unique_stages):
        if stage not in sorted_stages:
            sorted_stages.append(stage)
    
    # Create grid structure: stage -> time_slot -> performance (combine all dates)
    grid = {stage: {} for stage in sorted_stages}
    
    # Collect all performances from all dates into single grid
    all_perfs = []
    for date, perfs in scheduled_performances.items():
        all_perfs.extend(perfs)
    
    for perf in all_perfs:
        stage = perf.get('Stage', '').strip()
        start_time = perf.get('Start Time', '').strip()
        end_time = perf.get('End Time', '').strip()
        
        if stage in grid and start_time:
            start_col, span = get_performance_span(start_time, end_time, time_slots, granularity)
            if start_col >= 0 and span > 0:
                grid[stage][start_col] = {
                    'performance': perf,
                    'span': span
                }
    
    # Generate HTML
    title = f"{config.name} {year} - Timetable"
    url = f"https://frankvaneykelen.github.io/lineup-radar/{config.slug}/{year}/timetable.html"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(title)}</title>
    <meta name="description" content="Festival timetable for {escape_html(config.name)} {year}">
    <link rel="icon" type="image/png" sizes="16x16" href="../../shared/favicon_16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="../../shared/favicon_32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="../../shared/favicon_48x48.png">
    <link rel="apple-touch-icon" sizes="180x180" href="../../shared/favicon_180x180.png">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="../../shared/styles.css">
    <link rel="stylesheet" href="overrides.css">
    
    <meta property="og:title" content="{escape_html(title)}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    
    <style>
        .timetable-container {{
            width: 100%;
            max-width: 1900px;
            margin: 0 auto;
            overflow-x: auto;
            padding: 20px;
        }}
        
        .timetable {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 0.75rem;
        }}
        
        body.dark-mode .timetable {{
            background: #1a1a1a;
        }}
        
        .timetable th {{
            background: #333;
            color: white;
            padding: 8px 8px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            min-width: 120px;
            border-left: 1px solid white;
        }}
        
        .timetable th.stage-header {{
            background: #222;
            left: 0;
            z-index: 11;
            min-width: 120px;
            max-width: 120px;
            text-align: left;
            padding-left: 12px;
        }}
        
        .timetable td {{
            border: 1px solid #ddd;
            padding: 0;
            vertical-align: top;
            height: 90px;
            position: relative;
        }}
        
        body.dark-mode .timetable td {{
            border-color: #444;
        }}
        
        .timetable td.stage-name {{
            font-weight: 600;
            font-size: 1.1rem;
            padding: 12px;
            position: sticky;
            left: 0;
            z-index: 5;
            min-width: 120px;
            max-width: 120px;
        }}
        
        .timetable td.time-slot {{
            min-width: 20px;
        }}
        
        .performance {{
            position: absolute;
            top: 2px;
            left: 2px;
            right: 2px;
            bottom: 2px;
            padding: 6px;
            border-radius: 4px;
            border: 2px solid rgba(0,0,0,0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }}
        
        .performance:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 100;
            transform: scale(1.02);
            transition: all 0.2s;
        }}
        
        .performance-artist {{
            font-weight: 700;
            font-size: 0.85rem;
            margin-bottom: 2px;
            line-height: 1.2;
        }}
        
        .performance-artist a {{
            color: inherit;
            text-decoration: none;
        }}
        
        .performance-artist a:hover {{
            text-decoration: underline;
        }}
        
        .performance-time {{
            font-size: 0.7rem;
            opacity: 0.8;
            margin-bottom: 2px;
        }}
        
        .performance-tagline {{
            font-size: 0.7rem;
            font-style: italic;
            opacity: 0.75;
            line-height: 1.1;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
        
        /* Timetable-specific styles */
    </style>
</head>
<body>
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
                <h1>{escape_html(config.name)} {year} Timetable / Blokkenschema</h1>
                {'<p class="festival-description" style="font-size: 0.95em; opacity: 0.85; margin-top: 0.5rem; max-width: 800px;">' + config.description + '</p>' if config.description else ''}
                <p class="subtitle" style="font-size: 0.8em; opacity: 0.7; margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                    <a href="index.html" class="btn btn-primary btn-sm px-3 py-1" style="font-weight: 600;"><i class="bi bi-list-ul"></i> Lineup</a>
                    <a href="timetable.html" class="btn btn-primary btn-sm px-3 py-1 active" style="font-weight: 600;"><i class="bi bi-calendar3"></i> Timetable</a>
                    <a href="about.html" class="btn btn-primary btn-sm px-3 py-1" style="font-weight: 600;"><i class="bi bi-info-circle"></i> About</a>
                    {('<a href="' + config.lineup_url + '" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm px-3 py-1" style="font-weight: 600;">🎪 Festival Site</a>') if config.lineup_url else ''}
                    {('<a href="' + config.official_spotify_playlist + '" target="_blank" rel="noopener noreferrer" class="btn btn-outline-success btn-sm px-3 py-1" style="font-weight: 600;"><i class="bi bi-spotify"></i> Official Playlist</a>') if config.official_spotify_playlist else ''}
                    {('<a href="' + config.spotify_playlist_id + '" target="_blank" rel="noopener noreferrer" class="btn btn-success btn-sm px-3 py-1" style="font-weight: 600;"><i class="bi bi-spotify"></i> LineupRadar Playlist</a>') if config.spotify_playlist_id else ''}
                </p>
        </div>
    </header>
</div>

<div class="timetable-container">
    <table class="timetable">
        <thead>
            <tr>
                <th class="stage-header">Stage</th>
"""
    
    # Time headers
    for i, time_slot in enumerate(time_slots):
        # Show half-hour markers (every 6 slots = 30 minutes for 5-min granularity)
        if i % 6 == 0:
            html_content += f'                    <th colspan="6">{time_slot}</th>\n'
    
    html_content += """                </tr>
        </thead>
        <tbody>
"""
    
    # Generate rows for each stage
    for stage in sorted_stages:
        stage_color = stage_colors.get(stage, '#999999')
        
        html_content += f'                <tr>\n'
        html_content += f'                    <td class="stage-name" style="background-color: {stage_color};">{escape_html(stage)}</td>\n'
        
        # Track which columns are filled
        filled_cols = set()
        
        # Add performance cells
        col_index = 0
        while col_index < len(time_slots):
            if col_index in filled_cols:
                col_index += 1
                continue
            
            if col_index in grid[stage]:
                # Performance exists at this time slot
                perf_data = grid[stage][col_index]
                perf = perf_data['performance']
                span = perf_data['span']
                
                artist = perf.get('Artist', '')
                tagline = perf.get('Tagline', '')
                start_time = perf.get('Start Time', '')
                end_time = perf.get('End Time', '')
                slug = artist_name_to_slug(artist)
                
                # Mark columns as filled
                for i in range(col_index, min(col_index + span, len(time_slots))):
                    filled_cols.add(i)
                
                # Lighten the stage color for performance background
                perf_bg = stage_color + 'CC'  # Add transparency
                
                html_content += f'                    <td class="time-slot" colspan="{span}" style="position: relative;">\n'
                html_content += f'                        <div class="performance" style="background-color: {perf_bg};">\n'
                html_content += f'                            <div class="performance-artist"><a href="artists/{slug}.html">{escape_html(artist)}</a></div>\n'
                html_content += f'                            <div class="performance-time">{escape_html(start_time)} - {escape_html(end_time)}</div>\n'
                if tagline:
                    html_content += f'                            <div class="performance-tagline">{escape_html(tagline)}</div>\n'
                html_content += f'                        </div>\n'
                html_content += f'                    </td>\n'
                
                col_index += span
            else:
                # Empty slot
                html_content += f'                    <td class="time-slot"></td>\n'
                col_index += 1
        
        html_content += f'                </tr>\n'
    html_content += """            </tbody>
        </table>
    </div>
    
    <script src="../../shared/script.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    
    # Save file
    output_file = output_dir / festival / year / "timetable.html"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated timetable: {output_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate festival timetable HTML page"
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
        default="alkmaarse-eigenste",
        help="Festival identifier (default: alkmaarse-eigenste)"
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
    
    # Find CSV file
    csv_file = Path(f"docs/{config.slug}/{args.year}/{args.year}.csv")
    
    if not csv_file.exists():
        print(f"✗ CSV file not found: {csv_file}")
        sys.exit(1)
    
    print(f"\n=== Generating Timetable for {config.name} {args.year} ===\n")
    generate_timetable_html(csv_file, output_dir, args.festival)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
