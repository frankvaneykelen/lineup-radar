"""
Shared menu generation functions for consistent navigation across all pages.
"""

from typing import Literal

# Festival configurations
FESTIVALS = [
    {"slug": "down-the-rabbit-hole", "name": "Down The Rabbit Hole"},
    {"slug": "pinkpop", "name": "Pinkpop"},
    {"slug": "rock-werchter", "name": "Rock Werchter"},
    {"slug": "footprints", "name": "Footprints"},
    {"slug": "best-kept-secret", "name": "Best Kept Secret"},
]

YEAR = "2026"


def generate_hamburger_menu(
    path_prefix: Literal["", "../../", "../../../"] = "../../",
    escaped: bool = False
) -> str:
    """
    Generate the hamburger menu HTML with consistent formatting.
    
    Args:
        path_prefix: Path prefix for links. Options:
            - "" for homepage (festivals/index.html)
            - "../../" for festival pages (festivals/festival/year/*.html)
            - "../../../" for artist pages (festivals/festival/year/artists/*.html)
        escaped: Whether to escape quotes for use in Python f-strings
    
    Returns:
        HTML string for the hamburger menu content
    """
    quote = '\\"' if escaped else '"'
    
    lines = []
    
    # Festival sections
    for festival in FESTIVALS:
        lines.append(f'<div class={quote}festival-section{quote}>{festival["name"]} {YEAR}</div>')
        lineup_url = f'{path_prefix}{festival["slug"]}/{YEAR}/index.html'
        about_url = f'{path_prefix}{festival["slug"]}/{YEAR}/about.html'
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
