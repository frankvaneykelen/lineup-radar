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
    bio_language: str = 'Dutch'  # Language of the bio on festival website
    rating_boost: float = 0.0  # Rating adjustment for discovery/underground festivals (e.g., +1.5 for emerging artists)
    description: str = ''  # Short description of the festival
    
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


# Festival configurations
FESTIVALS = {
    'down-the-rabbit-hole': {
        'name': 'Down The Rabbit Hole',
        'base_url': 'https://downtherabbithole.nl',
        'lineup_url': 'https://downtherabbithole.nl/programma',
        'artist_path': '/programma/',
        'description': 'A boutique music and arts festival in Beuningen, Netherlands, known for its eclectic lineup and intimate atmosphere.',
        "lineup_radar_spotify_playlist": "https://open.spotify.com/playlist/3ERLeyNAEgIpUSh1ll3BLM",
    },
    'pinkpop': {
        'name': 'Pinkpop',
        'base_url': 'https://www.pinkpop.nl',
        'lineup_url': 'https://www.pinkpop.nl/en/programme/',
        'artist_path': '/en/line-up/',
        'bio_language': 'English',
        'description': 'The longest-running annual music festival in the Netherlands, held in Landgraaf since 1970.',
        'spotify_playlist': 'https://open.spotify.com/playlist/2lVlLvH6VA3Fsb2NLSN1Ib',
        'lineup_radar_spotify_playlist': 'https://open.spotify.com/playlist/2MMOziv3RBxvz93DQ3i9bT',
    },
    'rock-werchter': {
        'name': 'Rock Werchter',
        'base_url': 'https://www.rockwerchter.be',
        'lineup_url': 'https://www.rockwerchter.be/en/line-up/a-z',
        'artist_path': '/en/acts/',
        'bio_language': 'English',
        'description': "Belgium's largest annual rock music festival, held in Werchter since 1974, featuring major international artists.",
        'lineup_radar_spotify_playlist': 'https://open.spotify.com/playlist/3brJf9tiSKtvbg7jQ1MO0d',
    },
    'footprints': {
        'name': 'Footprints Festival',
        'base_url': 'https://www.tivolivredenburg.nl',
        'lineup_url': 'https://www.tivolivredenburg.nl/agenda/50573414/footprints-festival-21-02-2026',
        'artist_path': '',  # No individual artist pages
        'bio_language': 'Dutch',
        'rating_boost': 1.5,  # Discovery festival: boost emerging artist ratings into 7-9 range
        'description': 'A curated discovery festival at TivoliVredenburg in Utrecht, showcasing emerging international artists across diverse genres.',
        'custom_scraper': True,  # Requires custom scraping logic
        'spotify_playlist': 'https://open.spotify.com/playlist/2Qt2F5Mwnsd56LFfzagivS',
        'lineup_radar_spotify_playlist': 'https://open.spotify.com/playlist/2lWvCj3mbc0Xn4uN7HeTNX',
        # Artists from the description and lineup section
        'manual_artists': [
            'Gizmo Varillas',
            'Islandman',
            'Sessa',
            'Keshavara',
            'Derya Yıldırım & Grup Şimşek',
        ],
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
        slug=festival,
        bio_language=fest_data.get('bio_language', 'Dutch'),
        rating_boost=fest_data.get('rating_boost', 0.0),
        description=fest_data.get('description', '')
    )


def get_default_config() -> FestivalConfig:
    """
    Get default festival configuration.
    
    Returns:
        Default FestivalConfig (Down The Rabbit Hole 2026)
    """
    return get_festival_config()
