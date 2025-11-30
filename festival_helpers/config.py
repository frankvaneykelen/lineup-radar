"""
Festival configuration system.

Supports multiple festivals and years with different URL patterns and settings.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FestivalConfig:
    """Configuration for a festival."""
    
    name: str
    year: int
    base_url: str
    lineup_url: str
    artist_path: str  # Path segment for artist pages (e.g., "/programma/")
    slug: str = ''  # URL/directory slug for the festival
    
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
        return f"docs/{self.year}"


# Festival configurations
FESTIVALS = {
    'down-the-rabbit-hole': {
        'name': 'Down The Rabbit Hole',
        'base_url': 'https://downtherabbithole.nl',
        'lineup_url': 'https://downtherabbithole.nl/programma',
        'artist_path': '/programma/',
    },
    # Add more festivals here as needed
    # 'lowlands': {
    #     'name': 'Lowlands',
    #     'base_url': 'https://lowlands.nl',
    #     'lineup_url': 'https://lowlands.nl/line-up',
    #     'artist_path': '/artist/',
    # },
}


def get_festival_config(
    festival: str = 'down-the-rabbit-hole',
    year: int = 2026
) -> FestivalConfig:
    """
    Get festival configuration.
    
    Args:
        festival: Festival identifier (default: 'down-the-rabbit-hole')
        year: Festival year (default: 2026)
        
    Returns:
        FestivalConfig object
        
    Raises:
        ValueError: If festival is not found
        
    Examples:
        >>> config = get_festival_config('down-the-rabbit-hole', 2026)
        >>> config.name
        'Down The Rabbit Hole'
        >>> config.get_artist_url('radiohead')
        'https://downtherabbithole.nl/programma/radiohead'
    """
    if festival not in FESTIVALS:
        available = ', '.join(FESTIVALS.keys())
        raise ValueError(f"Unknown festival '{festival}'. Available: {available}")
    
    fest_data = FESTIVALS[festival]
    
    return FestivalConfig(
        name=fest_data['name'],
        year=year,
        base_url=fest_data['base_url'],
        lineup_url=fest_data['lineup_url'],
        artist_path=fest_data['artist_path'],
        slug=festival
    )


def get_default_config() -> FestivalConfig:
    """
    Get default festival configuration.
    
    Returns:
        Default FestivalConfig (Down The Rabbit Hole 2026)
    """
    return get_festival_config()
