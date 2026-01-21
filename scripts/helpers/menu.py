"""
Shared menu generation functions for consistent navigation across all pages.
"""

from typing import Literal
import json
import csv
from pathlib import Path

# Handle both direct execution and package import
try:
    from .config import FESTIVALS
except ImportError:
    from config import FESTIVALS

YEAR = "2026"


def has_schedule_data(slug: str, year: str) -> bool:
    """
    Check if a festival has complete schedule data (Date, Start Time, End Time, Stage).
    
    Returns:
        True if at least one artist has all schedule fields populated
    """
    csv_path = Path(f"docs/{slug}/{year}/{year}.csv")
    if not csv_path.exists():
        # Fallback for scripts running from scripts directory
        csv_path = Path(f"../docs/{slug}/{year}/{year}.csv")
    
    try:
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row.get('Date', '').strip() and 
                        row.get('Start Time', '').strip() and 
                        row.get('End Time', '').strip() and 
                        row.get('Stage', '').strip()):
                        return True
    except (OSError, csv.Error):
        pass
    
    return False


def get_festival_start_date(slug: str, year: str) -> str:
    """
    Get the start date for a festival from its about.json file.
    
    Returns:
        Start date string in YYYY-MM-DD format, or '9999-12-31' if not found
    """
    # Try to find the about.json file
    about_path = Path(f"docs/{slug}/{year}/about.json")
    if not about_path.exists():
        # Fallback for scripts running from scripts directory
        about_path = Path(f"../docs/{slug}/{year}/about.json")
    
    try:
        if about_path.exists():
            with open(about_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('start_date', '9999-12-31')
    except (OSError, json.JSONDecodeError):
        pass
    
    return '9999-12-31'


def generate_hamburger_menu(
    path_prefix: Literal["", "../../", "../../../"] = "../../",
    escaped: bool = False
) -> str:
    """
    Generate the hamburger menu HTML with consistent formatting.
    Festivals are sorted by start date in ascending order.
    
    Args:
        path_prefix: Path prefix for links. Options:
            - "" for homepage (docs/index.html)
            - "../../" for festival pages (docs/festival/year/*.html)
            - "../../../" for artist pages (docs/festival/year/artists/*.html)
        escaped: Whether to escape quotes for use in Python f-strings
    
    Returns:
        HTML string for the hamburger menu content
    """
    quote = '\\"' if escaped else '"'
    
    lines = []
    
    # Get festivals with their start dates and sort by date
    festival_list = []
    for slug, config in FESTIVALS.items():
        # Skip festivals marked as hidden from navigation
        if config.get('hide_from_navigation', False):
            continue
        
        start_date = get_festival_start_date(slug, YEAR)
        festival_list.append((start_date, slug, config))
    
    # Sort by start date (ascending)
    festival_list.sort(key=lambda x: x[0])
    
    # Festival sections
    for start_date, slug, config in festival_list:
        name = config.get('name', slug)
        lines.append(f'<div class={quote}festival-section{quote}>{name} {YEAR}</div>')
        lineup_url = f'{path_prefix}{slug}/{YEAR}/index.html'
        timetable_url = f'{path_prefix}{slug}/{YEAR}/timetable.html'
        about_url = f'{path_prefix}{slug}/{YEAR}/about.html'
        
        # Check if festival has schedule data for timetable
        has_timetable = has_schedule_data(slug, YEAR)
        
        if has_timetable:
            lines.append(
                f'<div class={quote}festival-links{quote}>'
                f'<a href={quote}{lineup_url}{quote}>Lineup</a> | '
                f'<a href={quote}{timetable_url}{quote}>Timetable</a> | '
                f'<a href={quote}{about_url}{quote}>About</a>'
                f'</div>'
            )
        else:
            lines.append(
                f'<div class={quote}festival-links{quote}>'
                f'<a href={quote}{lineup_url}{quote}>Lineup</a> | '
                f'<a href={quote}{about_url}{quote}>About</a>'
                f'</div>'
            )
    
    # Charts and FAQ links
    lines.append(f'<div class={quote}festival-section{quote}>General</div>')
    charts_url = f'{path_prefix}charts.html'
    faq_url = f'{path_prefix}faq.html'
    
    lines.append(f'<a href={quote}{charts_url}{quote} class={quote}festival-year{quote}>')
    lines.append(f'<i class={quote}bi bi-bar-chart-fill{quote}></i> Charts')
    lines.append(f'</a>')
    lines.append(f'<a href={quote}{faq_url}{quote} class={quote}festival-year{quote}>')
    lines.append(f'<i class={quote}bi bi-question-circle{quote}></i> FAQ')
    lines.append(f'</a>')
    
    return '\n'.join(lines)
