"""
Artist name to URL slug conversion utilities.
"""

import re
import unicodedata


# Special mappings for artists with unusual names or formatting
# These override the default slug generation logic
SPECIAL_SLUG_CASES = {
    'Florence + The Machine': 'florence-the-machine',
    'The xx': 'the-xx',
    '¥ØU$UK€ ¥UK1MAT$U': 'yenouukeur-yenuk1matu',
    'Derya Yıldırım & Grup Şimşek': 'derya-yildirim-grup-simsek',
    'Arp Frique & The Perpetual Singers': 'arp-frique-the-perpetual-singers',
    'Mall Grab b2b Narciss': 'mall-grab-b2b-narciss',
    "Kin'Gongolo Kiniata": 'kingongolo-kiniata',
    'Lumï': 'lumi',
    'De Staat Becomes De Staat': 'de-staat-becomes-de-staat'
}


def artist_name_to_slug(name: str, special_cases: dict = None) -> str:
    """
    Convert artist name to URL slug format.
    
    Args:
        name: Artist name to convert
        special_cases: Optional dictionary of special case mappings to extend defaults
        
    Returns:
        URL-safe slug string
        
    Examples:
        >>> artist_name_to_slug("The National")
        'the-national'
        >>> artist_name_to_slug("Björk")
        'bjork'
        >>> artist_name_to_slug("Run the Jewels")
        'run-the-jewels'
    """
    # Merge special cases if provided
    cases = SPECIAL_SLUG_CASES.copy()
    if special_cases:
        cases.update(special_cases)
    
    # Check special cases first
    if name in cases:
        return cases[name]
    
    # Normalize unicode characters (e.g., ü -> u, ï -> i)
    slug = unicodedata.normalize('NFKD', name)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    slug = slug.lower()
    
    # Replace spaces and common separators with hyphens
    slug = slug.replace(' ', '-')
    slug = slug.replace('&', '')
    slug = slug.replace('+', '')
    slug = slug.replace("'", '')
    
    # Remove any remaining non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Collapse multiple hyphens into one
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    return slug.strip('-')


def get_sort_name(artist_name: str) -> str:
    """
    Get sort name for artist, ignoring 'The' prefix.
    
    Args:
        artist_name: Full artist name
        
    Returns:
        Artist name with 'The' prefix removed for sorting
        
    Examples:
        >>> get_sort_name("The National")
        'National'
        >>> get_sort_name("Radiohead")
        'Radiohead'
    """
    name = artist_name.strip()
    if name.lower().startswith('the '):
        return name[4:]
    return name
