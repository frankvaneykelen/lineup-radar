#!/usr/bin/env python3
"""
Generate festival timetable (blokkenschema) HTML page.
Shows a visual schedule grid with stages as rows and time slots as columns.
"""

import sys
from pathlib import Path
import csv
import json
from datetime import date, datetime, timedelta
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


def parse_date(date_str: str) -> Optional[date]:
    """Parse date string in YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_schedule_datetime(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse schedule date+time into datetime. Handles 24:00 as next day 00:00."""
    base_date = parse_date(date_str)
    if not base_date or not time_str:
        return None

    if time_str == '24:00':
        return datetime.combine(base_date, datetime.min.time()) + timedelta(days=1)

    try:
        parsed_time = datetime.strptime(time_str, '%H:%M').time()
        return datetime.combine(base_date, parsed_time)
    except ValueError:
        return None


def floor_to_minutes(dt: datetime, step_minutes: int) -> datetime:
    """Floor a datetime to the nearest lower step in minutes."""
    floored_minutes = (dt.minute // step_minutes) * step_minutes
    return dt.replace(minute=floored_minutes, second=0, microsecond=0)


def ceil_to_minutes(dt: datetime, step_minutes: int) -> datetime:
    """Ceil a datetime to the nearest upper step in minutes."""
    floored = floor_to_minutes(dt, step_minutes)
    if floored == dt.replace(second=0, microsecond=0):
        return floored
    return floored + timedelta(minutes=step_minutes)


def generate_time_slots(start_dt: datetime, end_dt: datetime, granularity: int = 5) -> List[datetime]:
    """Generate timeline slots between start and end datetimes at granularity minutes."""
    slots = []
    current = start_dt

    while current < end_dt:
        slots.append(current)
        current += timedelta(minutes=granularity)

    return slots


def get_performance_span(
    perf_start: datetime,
    perf_end: datetime,
    timeline_start: datetime,
    time_slots_count: int,
    granularity: int
) -> tuple:
    """Calculate starting column and span for a performance on the full timeline."""
    if perf_end <= perf_start:
        return (0, 0)

    start_minutes = int((perf_start - timeline_start).total_seconds() // 60)
    duration_minutes = int((perf_end - perf_start).total_seconds() // 60)

    start_col = start_minutes // granularity
    span = max(1, duration_minutes // granularity)

    if start_col < 0 or start_col >= time_slots_count:
        return (0, 0)

    span = min(span, time_slots_count - start_col)
    return (start_col, span)


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
    
    # Build absolute datetimes per performance so days do not overlap on the grid
    timeline_performances = []
    for perfs in scheduled_performances.values():
        for perf in perfs:
            perf_date = perf.get('Date', '').strip()
            perf_end_date = perf.get('End Date', '').strip() or perf_date
            start_time = perf.get('Start Time', '').strip()
            end_time = perf.get('End Time', '').strip()

            perf_start = parse_schedule_datetime(perf_date, start_time)
            perf_end = parse_schedule_datetime(perf_end_date, end_time)

            # Fallback for overnight sets where End Date is missing/incorrect
            if perf_start and perf_end and perf_end <= perf_start:
                perf_end += timedelta(days=1)

            if not perf_start or not perf_end:
                continue

            timeline_performances.append((perf, perf_start, perf_end))

    if not timeline_performances:
        print("No valid schedule datetimes found")
        return

    raw_start = min(start for _, start, _ in timeline_performances)
    raw_end = max(end for _, _, end in timeline_performances)

    # Keep columns aligned to the 30-minute headers
    timeline_start = floor_to_minutes(raw_start, 30)
    timeline_end = ceil_to_minutes(raw_end, 30)

    # Generate time slots
    granularity = 5  # 5-minute intervals
    time_slots = generate_time_slots(timeline_start, timeline_end, granularity)
    
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
        "Park 6": "#8B7FD6",           # Purple
        
        # Down The Rabbit Hole (colors inspired by official branding)
        "Hotot": "#FF7A66",            # Coral
        "Teddy Widder": "#6BCB77",     # Fresh Green
        "Fuzzy Lop": "#4D96FF",        # Sky Blue
        "Rex": "#FFD166",              # Warm Yellow
        "The Bizarre": "#9B5DE5",      # Violet
        "Bossa Nova": "#F15BB5",       # Magenta
        "the CROQUE Madame": "#00CC99",# Mint
        "Holding": "#FFB4A2",          # Peach
        "Radiate VI": "#00A6FB",       # Bright Cyan
        "Idyllische Veldje": "#BDFAC1" # Soft Lime

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
    
    # Create grid structure: stage -> time_slot -> performance (full multi-day timeline)
    grid = {stage: {} for stage in sorted_stages}

    for perf, perf_start, perf_end in timeline_performances:
        stage = perf.get('Stage', '').strip()

        if stage in grid:
            start_col, span = get_performance_span(
                perf_start,
                perf_end,
                timeline_start,
                len(time_slots),
                granularity,
            )
            if start_col >= 0 and span > 0:
                grid[stage][start_col] = {
                    'performance': perf,
                    'span': span,
                    'start_dt': perf_start,
                    'end_dt': perf_end,
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

        .timetable thead tr.day-row th {{
            top: 0;
            z-index: 12;
        }}

        .timetable thead tr.time-row th {{
            top: 36px;
            z-index: 11;
        }}

        .timetable th.day-header {{
            background: linear-gradient(90deg, #1f1f1f, #2f2f2f);
            text-align: center;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        .timetable th.day-header.day-even {{
            background: linear-gradient(90deg, #1f1f1f, #2f2f2f);
        }}

        .timetable th.day-header.day-odd {{
            background: linear-gradient(90deg, #252525, #353535);
        }}

        .timetable th.time-header {{
            background: #3a3a3a;
            font-weight: 500;
            text-align: center;
        }}

        .timetable th.time-header.day-even {{
            background: #3a3a3a;
        }}

        .timetable th.time-header.day-odd {{
            background: #464646;
        }}

        .timetable td.time-slot.day-even {{
            background-color: rgba(0, 0, 0, 0.02);
        }}

        .timetable td.time-slot.day-odd {{
            background-color: rgba(0, 0, 0, 0.05);
        }}

        .timetable th.day-boundary,
        .timetable td.day-boundary {{
            border-left: 3px solid rgba(0, 0, 0, 0.35) !important;
        }}

        body.dark-mode .timetable th.day-header {{
            background: linear-gradient(90deg, #2a2a2a, #383838);
        }}

        body.dark-mode .timetable th.day-header.day-even {{
            background: linear-gradient(90deg, #2a2a2a, #383838);
        }}

        body.dark-mode .timetable th.day-header.day-odd {{
            background: linear-gradient(90deg, #313131, #404040);
        }}

        body.dark-mode .timetable th.time-header {{
            background: #323232;
        }}

        body.dark-mode .timetable th.time-header.day-even {{
            background: #323232;
        }}

        body.dark-mode .timetable th.time-header.day-odd {{
            background: #3a3a3a;
        }}

        body.dark-mode .timetable td.time-slot.day-even {{
            background-color: rgba(255, 255, 255, 0.03);
        }}

        body.dark-mode .timetable td.time-slot.day-odd {{
            background-color: rgba(255, 255, 255, 0.06);
        }}

        body.dark-mode .timetable th.day-boundary,
        body.dark-mode .timetable td.day-boundary {{
            border-left-color: rgba(255, 255, 255, 0.4) !important;
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
            <tr class="day-row">
                <th class="stage-header">Stage</th>
"""
    
    # Day header row
    current_day = None
    day_start_col = 0
    slots_per_half_hour = 30 // granularity
    day_boundary_cols = set()
    day_parity_by_col = {}
    current_day_index = 0

    for i, slot_dt in enumerate(time_slots):
        if i > 0 and slot_dt.date() != time_slots[i - 1].date():
            current_day_index += 1
        day_parity_by_col[i] = 'day-even' if current_day_index % 2 == 0 else 'day-odd'

    current_day_index = 0

    for i, slot_dt in enumerate(time_slots):
        if current_day is None:
            current_day = slot_dt.date()
            day_start_col = i
            continue

        if slot_dt.date() != current_day:
            day_span = i - day_start_col
            day_label = datetime.combine(current_day, datetime.min.time()).strftime('%a %d %b')
            day_parity_class = 'day-even' if current_day_index % 2 == 0 else 'day-odd'
            day_classes = f'day-header {day_parity_class} day-boundary' if day_start_col > 0 else f'day-header {day_parity_class}'
            html_content += f'                    <th class="{day_classes}" colspan="{day_span}">{day_label}</th>\n'
            day_boundary_cols.add(i)
            current_day = slot_dt.date()
            day_start_col = i
            current_day_index += 1

    if current_day is not None:
        day_span = len(time_slots) - day_start_col
        day_label = datetime.combine(current_day, datetime.min.time()).strftime('%a %d %b')
        day_parity_class = 'day-even' if current_day_index % 2 == 0 else 'day-odd'
        day_classes = f'day-header {day_parity_class} day-boundary' if day_start_col > 0 else f'day-header {day_parity_class}'
        html_content += f'                    <th class="{day_classes}" colspan="{day_span}">{day_label}</th>\n'

    html_content += """                </tr>
            <tr class=\"time-row\">
                <th class=\"stage-header\">Stage</th>
"""

    # Time headers (half-hour markers)
    for i, slot_dt in enumerate(time_slots):
        if i % slots_per_half_hour == 0:
            parity_class = day_parity_by_col.get(i, 'day-even')
            time_classes = f'time-header {parity_class} day-boundary' if i in day_boundary_cols else f'time-header {parity_class}'
            html_content += f'                    <th class="{time_classes}" colspan="{slots_per_half_hour}">{slot_dt.strftime("%H:%M")}</th>\n'
    
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
                start_dt = perf_data['start_dt']
                end_dt = perf_data['end_dt']
                slug = artist_name_to_slug(artist)
                
                # Mark columns as filled
                for i in range(col_index, min(col_index + span, len(time_slots))):
                    filled_cols.add(i)
                
                # Lighten the stage color for performance background
                perf_bg = stage_color + 'CC'  # Add transparency
                parity_class = day_parity_by_col.get(col_index, 'day-even')
                cell_class = f'time-slot {parity_class} day-boundary' if col_index in day_boundary_cols else f'time-slot {parity_class}'
                
                html_content += f'                    <td class="{cell_class}" colspan="{span}" style="position: relative;">\n'
                html_content += f'                        <div class="performance" style="background-color: {perf_bg};">\n'
                html_content += f'                            <div class="performance-artist"><a href="artists/{slug}.html">{escape_html(artist)}</a></div>\n'
                html_content += f'                            <div class="performance-time">{escape_html(start_dt.strftime("%a %H:%M"))} - {escape_html(end_dt.strftime("%H:%M"))}</div>\n'
                if tagline:
                    html_content += f'                            <div class="performance-tagline">{escape_html(tagline)}</div>\n'
                html_content += f'                        </div>\n'
                html_content += f'                    </td>\n'
                
                col_index += span
            else:
                # Empty slot
                parity_class = day_parity_by_col.get(col_index, 'day-even')
                cell_class = f'time-slot {parity_class} day-boundary' if col_index in day_boundary_cols else f'time-slot {parity_class}'
                html_content += f'                    <td class="{cell_class}"></td>\n'
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
