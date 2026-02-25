"""
Festival configuration system.

Supports multiple festivals and years with different URL patterns and settings.
"""

from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path


@dataclass
class FestivalConfig:
    """Configuration for a festival."""
    
    name: str
    year: int
    base_url: str
    lineup_url: str
    artist_path: str  # Path segment for artist pages (e.g., "/programma/")
    slug: str = ''  # URL/directory slug for the festival
    bio_language: str = 'Dutch'  # Language of the bio on festival website
    rating_boost: float = 0.0  # Rating adjustment for discovery/underground festivals (e.g., +1.5 for emerging artists)
    description: str = ''  # Short description of the festival
    official_spotify_playlist: str = ''  # Official festival Spotify playlist URL
    spotify_playlist_id: str = ''  # LineupRadar curated Spotify playlist URL
    image_index: Optional[int] = None  # Fixed index into candidate image list (for festivals where auto-detection fails)
    bio_selector: str = ''  # CSS selector for bio text on artist pages (pre-configures the learned selector)
    
    def get_artist_url(self, slug: str) -> str:
        """
        Get full URL for an artist page.
        
        Args:
            slug: Artist slug
            
        Returns:
            Full URL to artist page
        """
        return f"{self.base_url}{self.artist_path}{slug}"
    
    @property
    def csv_filename(self) -> str:
        """Get CSV filename for this festival year."""
        return f"{self.year}.csv"
    
    @property
    def output_dir(self) -> str:
        """Get output directory for generated files."""
        return f"docs/{self.slug}/{self.year}"


def _load_festivals() -> dict:
    """Build FESTIVALS dict by scanning docs/*/year/settings.json files."""
    result = {}
    for base in [Path("docs"), Path("../docs")]:
        if not base.exists():
            continue
        for fest_dir in sorted(base.iterdir()):
            if not fest_dir.is_dir() or fest_dir.name.startswith('.'):
                continue
            # Pick the most recent year directory
            for year_dir in sorted(fest_dir.iterdir(), reverse=True):
                if not year_dir.is_dir() or not year_dir.name.isdigit():
                    continue
                settings_path = year_dir / "settings.json"
                if settings_path.exists():
                    try:
                        with settings_path.open('r', encoding='utf-8') as f:
                            data = json.load(f)
                        result[fest_dir.name] = data
                    except (OSError, json.JSONDecodeError):
                        pass
                    break  # Use most recent year only
        break  # Use first existing base path
    return result


# Festival configurations — dynamically loaded from docs/*/year/settings.json
FESTIVALS = _load_festivals()


def get_festival_config(
    festival: str = 'down-the-rabbit-hole',
    year: int = 2026
) -> FestivalConfig:
    """
    Get festival configuration by reading directly from settings.json.

    Args:
        festival: Festival identifier (default: 'down-the-rabbit-hole')
        year: Festival year (default: 2026)

    Returns:
        FestivalConfig object

    Raises:
        ValueError: If no settings.json is found for the given festival/year

    Examples:
        >>> config = get_festival_config('down-the-rabbit-hole', 2026)
        >>> config.name
        'Down The Rabbit Hole'
        >>> config.get_artist_url('radiohead')
        'https://downtherabbithole.nl/programma/radiohead'
    """
    for base in [Path("docs"), Path("../docs")]:
        settings_path = base / festival / str(year) / "settings.json"
        if settings_path.exists():
            try:
                with settings_path.open('r', encoding='utf-8') as fh:
                    s = json.load(fh)
                scraper_cfg = s.get('scraper', {})
                raw_idx = scraper_cfg.get('image_index')
                image_index = int(raw_idx) if raw_idx is not None else None
                return FestivalConfig(
                    name=s.get('name', festival),
                    year=year,
                    base_url=s.get('base_url', ''),
                    lineup_url=s.get('lineup_url', ''),
                    artist_path=s.get('artist_path', ''),
                    slug=festival,
                    bio_language=s.get('bio_language', 'Dutch'),
                    rating_boost=float(s.get('rating_boost', 0.0)),
                    description=s.get('description', ''),
                    official_spotify_playlist=s.get('official_spotify_playlist', ''),
                    spotify_playlist_id=s.get('spotify_playlist_id', ''),
                    image_index=image_index,
                    bio_selector=scraper_cfg.get('bio_selector', ''),
                )
            except Exception:
                pass

    available = ', '.join(sorted(FESTIVALS.keys()))
    raise ValueError(f"No settings.json found for festival '{festival}' year {year}. Known festivals: {available}")


def get_default_config() -> FestivalConfig:
    """
    Get default festival configuration.
    
    Returns:
        Default FestivalConfig (Down The Rabbit Hole 2026)
    """
    return get_festival_config()
