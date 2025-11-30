"""
Festival website scraping utilities.
"""

import re
import time
import urllib.request
import urllib.error
from typing import Optional, List
from bs4 import BeautifulSoup

from .slug import artist_name_to_slug
from .config import FestivalConfig


class FestivalScraper:
    """Scraper for festival websites."""
    
    def __init__(self, config: FestivalConfig):
        """
        Initialize scraper with festival configuration.
        
        Args:
            config: Festival configuration object
        """
        self.config = config
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch HTML content from a URL.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            HTML content as string, or None if fetch fails
        """
        try:
            req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  ⚠️  Page not found (404): {url}")
            else:
                print(f"  ⚠️  HTTP error {e.code}: {url}")
            return None
        except Exception as e:
            print(f"  ⚠️  Error fetching {url}: {e}")
            return None
    
    def get_artist_page_url(self, artist_name: str) -> str:
        """
        Get the URL for an artist's festival page.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            Full URL to artist page
        """
        slug = artist_name_to_slug(artist_name)
        return self.config.get_artist_url(slug)
    
    def fetch_artist_page(self, artist_name: str) -> Optional[str]:
        """
        Fetch an artist's festival page HTML.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            HTML content or None if fetch fails
        """
        url = self.get_artist_page_url(artist_name)
        return self.fetch_page(url)
    
    def extract_spotify_link(self, html: str) -> Optional[str]:
        """
        Extract Spotify artist link from HTML.
        
        Args:
            html: HTML content to search
            
        Returns:
            Spotify URL or None if not found
        """
        pattern = r'https://open\.spotify\.com/artist/[a-zA-Z0-9]+'
        match = re.search(pattern, html)
        return match.group(0) if match else None
    
    def fetch_spotify_link(self, artist_name: str) -> Optional[str]:
        """
        Fetch Spotify link for an artist from their festival page.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            Spotify URL or None if not found
        """
        html = self.fetch_artist_page(artist_name)
        if not html:
            return None
        
        return self.extract_spotify_link(html)
    
    def extract_bio(self, html: str) -> str:
        """
        Extract artist bio/description from festival page HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Bio text or empty string if not found
        """
        import re
        
        # Try Down The Rabbit Hole specific pattern first (most specific)
        # Pattern: <div class="...column text-xl font-normal prose !max-w-none...">bio text</div>
        dutch_bio_pattern = r'<div[^>]*class="[^"]*column text-xl font-normal prose !max-w-none[^"]*"[^>]*>(.*?)</div>'
        dutch_bio_match = re.search(dutch_bio_pattern, html, re.DOTALL | re.IGNORECASE)
        
        if dutch_bio_match:
            bio_html = dutch_bio_match.group(1).strip()
            # Clean up HTML tags but preserve line breaks
            bio_html = re.sub(r'<br\s*/?>', '\n', bio_html)
            bio_html = re.sub(r'<p[^>]*>', '\n', bio_html)
            bio_html = re.sub(r'</p>', '\n', bio_html)
            bio_html = re.sub(r'<[^>]+>', '', bio_html)
            bio_html = re.sub(r'\n\s*\n', '\n\n', bio_html).strip()
            if bio_html:
                return bio_html
        
        # Fallback to old description pattern
        bio_pattern = r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>'
        bio_match = re.search(bio_pattern, html, re.DOTALL | re.IGNORECASE)
        
        if bio_match:
            bio_html = bio_match.group(1).strip()
            bio_html = re.sub(r'<br\s*/?>', '\n', bio_html)
            bio_html = re.sub(r'<p[^>]*>', '\n', bio_html)
            bio_html = re.sub(r'</p>', '\n', bio_html)
            bio_html = re.sub(r'<[^>]+>', '', bio_html)
            bio_html = re.sub(r'\n\s*\n', '\n\n', bio_html).strip()
            if bio_html:
                return bio_html
        
        # Try BeautifulSoup as last resort
        soup = BeautifulSoup(html, 'html.parser')
        bio_selectors = [
            'div.artist-bio',
            'div.artist-description',
            'div.bio',
            'p.description'
        ]
        
        for selector in bio_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        
        return ""
    
    def fetch_artist_bio(self, artist_name: str) -> str:
        """
        Fetch artist bio from their festival page.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            Bio text or empty string if not found
        """
        html = self.fetch_artist_page(artist_name)
        if not html:
            return ""
        
        return self.extract_bio(html)
    
    def fetch_lineup_artists(self) -> List[str]:
        """
        Fetch list of artists from festival lineup page.
        
        Returns:
            List of artist names
        """
        html = self.fetch_page(self.config.lineup_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try common artist list patterns
        artists = []
        
        # Look for links in the lineup/program area
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if self.config.artist_path in href:
                artist_name = link.get_text(strip=True)
                if artist_name and artist_name not in artists:
                    artists.append(artist_name)
        
        return artists
    
    def rate_limit_delay(self, seconds: float = 0.5):
        """
        Add a delay to respect rate limits.
        
        Args:
            seconds: Number of seconds to wait
        """
        time.sleep(seconds)
