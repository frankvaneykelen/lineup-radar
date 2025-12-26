"""
Festival website scraping utilities with self-learning capabilities.
"""

import re
import time
import urllib.request
import urllib.error
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from .slug import artist_name_to_slug
from .config import FestivalConfig
from .ai_client import clean_scraped_text


# Path to store learned selectors
LEARNED_SELECTORS_FILE = Path(__file__).parent.parent / 'learned_selectors.json'


def load_learned_selectors() -> Dict[str, Any]:
    """Load previously learned CSS selectors and patterns."""
    if LEARNED_SELECTORS_FILE.exists():
        with open(LEARNED_SELECTORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_learned_selectors(selectors: Dict[str, Any]):
    """Save learned selectors for future use."""
    with open(LEARNED_SELECTORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(selectors, indent=2, fp=f)
    print(f"  💾 Saved learned selectors to {LEARNED_SELECTORS_FILE}")


def prompt_user_for_selector(field_name: str, url: str, soup: BeautifulSoup, hints: List[str] = None) -> Optional[str]:
    """
    Interactively prompt user for CSS selector when automatic detection fails.
    
    Args:
        field_name: Name of the field to find (e.g., 'bio', 'image', 'artist links')
        url: URL being scraped
        soup: BeautifulSoup object of the page
        hints: Optional list of common selector patterns to suggest
    
    Returns:
        CSS selector string or None if skipped
    """
    print(f"\n{'='*70}")
    print(f"🔍 HELP NEEDED: Unable to find '{field_name}'")
    print(f"📄 URL: {url}")
    print(f"{'='*70}")
    
    if hints:
        print(f"\n💡 Common patterns for {field_name}:")
        for i, hint in enumerate(hints, 1):
            print(f"   {i}. {hint}")
    
    print(f"\n📝 Please inspect the page in your browser and provide:")
    print(f"   - CSS selector (e.g., '.bio-text', '#description', 'div.artist-info p')")
    print(f"   - Or type 'skip' to skip this field and continue")
    print(f"   - Or type 'exit' to stop scraping")
    
    while True:
        selector = input(f"\n🎯 CSS selector for '{field_name}': ").strip()
        
        if selector.lower() == 'exit':
            raise KeyboardInterrupt("User requested exit")
        
        if selector.lower() == 'skip':
            print(f"  ⏭️  Skipping '{field_name}'")
            return None
        
        if not selector:
            print("  ❌ Empty selector. Please try again or type 'skip'.")
            continue
        
        # Test the selector
        try:
            elements = soup.select(selector)
            if elements:
                print(f"  ✓ Found {len(elements)} element(s) with selector: {selector}")
                if len(elements) > 1:
                    confirm = input(f"    Found multiple elements. Use first one? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                # Show preview of what was found
                preview = str(elements[0])[:200]
                print(f"  📄 Preview: {preview}...")
                confirm = input(f"  ✓ Is this correct? (y/n): ").strip().lower()
                if confirm == 'y':
                    return selector
                else:
                    print("  Try another selector...")
            else:
                print(f"  ❌ No elements found with selector: {selector}")
                print(f"  💡 Tip: Use browser DevTools to copy CSS selector")
                retry = input(f"  Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return None
        except Exception as e:
            print(f"  ❌ Invalid selector: {e}")
            continue


class FestivalScraper:
    """Self-learning scraper for festival websites."""
    
    def __init__(self, config: FestivalConfig, interactive: bool = True):
        """
        Initialize scraper with festival configuration.
        
        Args:
            config: Festival configuration object
            interactive: Whether to prompt user for help when automatic detection fails
        """
        self.config = config
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.interactive = interactive
        self.learned_selectors = load_learned_selectors()
        self.festival_key = config.slug
        
        # Initialize festival-specific selectors if not exists
        if self.festival_key not in self.learned_selectors:
            self.learned_selectors[self.festival_key] = {}
        
        self.session_learned = False  # Track if we learned anything new this session
    
    def fetch_page(self, url: str, timeout: int = 10, use_selenium: bool = False) -> Optional[str]:
        """
        Fetch HTML content from a URL. Uses Selenium for dynamic content if required.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            use_selenium: If True, use Selenium to render dynamic content
        Returns:
            HTML content as string, or None if fetch fails
        """
        # Use Selenium for Rewire artist pages to get dynamic content
        if use_selenium or (self.festival_key == "rewire" and "/artist/" in url):
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument(f'user-agent={self.user_agent}')
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(timeout)
                driver.get(url)
                time.sleep(2)  # Wait for JS to load
                html = driver.page_source
                driver.quit()
                return html
            except Exception as e:
                print(f"  ⚠️  Selenium error fetching {url}: {e}")
                return None
        # Fallback to requests for static pages
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
    
    def extract_bio(self, html: str, artist_name: str = "") -> str:
        """
        Extract artist bio/description from festival page HTML.
        Uses learned selectors first, then falls back to heuristics, then prompts user.
        
        Args:
            html: HTML content
            artist_name: Artist name (for context in prompts)
            
        Returns:
            Bio text or empty string if not found
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try learned selector first
        learned = self.learned_selectors.get(self.festival_key, {}).get('bio_selector')
        if learned:
            try:
                element = soup.select_one(learned)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 50:  # Reasonable bio length
                        # Clean up whitespace issues before returning
                        return clean_scraped_text(text)
                else:
                    print(f"  ⚠️  Learned bio selector '{learned}' no longer works")
            except Exception as e:
                print(f"  ⚠️  Error with learned selector: {e}")
        
        # Try common patterns (existing heuristics)
        bio_text = self._try_bio_heuristics(html, soup)
        if bio_text:
            # Clean up whitespace issues before returning
            return clean_scraped_text(bio_text)
        
        # If interactive and nothing found, ask user
        if self.interactive:
            print(f"\n  ⚠️  Could not find bio for: {artist_name}")
            selector = prompt_user_for_selector(
                'artist bio/description',
                self.config.get_artist_url(artist_name_to_slug(artist_name)) if artist_name else self.config.lineup_url,
                soup,
                hints=[
                    '.artist-bio',
                    '.bio',
                    '.description',
                    'div[class*="bio"]',
                    'div[class*="description"]',
                    '.content p',
                    'main p',
                    'article p'
                ]
            )
            
            if selector:
                # Save the learned selector
                self.learned_selectors[self.festival_key]['bio_selector'] = selector
                self.session_learned = True
                
                # Extract using the new selector
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Clean up whitespace issues before returning
                    return clean_scraped_text(text)
        
        return ""
    
    def _try_bio_heuristics(self, html: str, soup: BeautifulSoup) -> str:
        """Try various heuristic patterns to find bio."""
        import re
        
        # Try Down The Rabbit Hole specific pattern first (most specific)
        dutch_bio_pattern = r'<div[^>]*class="[^"]*column text-xl font-normal prose !max-w-none[^"]*"[^>]*>(.*?)</div>'
        dutch_bio_match = re.search(dutch_bio_pattern, html, re.DOTALL | re.IGNORECASE)
        
        if dutch_bio_match:
            bio_html = dutch_bio_match.group(1).strip()
            bio_text = self._clean_html(bio_html)
            if bio_text:
                return bio_text
        
        # Fallback to old description pattern
        bio_pattern = r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>'
        bio_match = re.search(bio_pattern, html, re.DOTALL | re.IGNORECASE)
        
        if bio_match:
            bio_html = bio_match.group(1).strip()
            bio_text = self._clean_html(bio_html)
            if bio_text:
                return bio_text
        
        # Try common CSS selectors
        bio_selectors = [
            'div.artist-bio',
            'div.artist-description',
            'div.bio',
            'p.description',
            'div.content',
            'article.artist'
        ]
        
        for selector in bio_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 50:
                    return text
        
        # For Pinkpop: Look for the first substantial paragraph after the artist name
        h1 = soup.find('h1')
        if h1:
            candidate_bio = None
            for elem in h1.find_all_next('p'):
                text = elem.get_text(strip=True)
                if len(text) < 100:
                    continue
                if 'you might also like' in text.lower():
                    break
                if not candidate_bio:
                    candidate_bio = text
                bio_keywords = ['artist', 'band', 'music', 'singer', 'songwriter', 'album', 
                               'tour', 'festival', 'released', 'formed', 'world', 'indie', 
                               'pop', 'rock', 'sound', 'debut', 'hit', 'stage', 'performance']
                if any(word in text.lower() for word in bio_keywords):
                    return text
            if candidate_bio:
                return candidate_bio
        
        return ""
    
    def _clean_html(self, html_text: str) -> str:
        """Clean HTML tags from text while preserving structure."""
        import re
        html_text = re.sub(r'<br\s*/?>', '\n', html_text)
        html_text = re.sub(r'<p[^>]*>', '\n', html_text)
        html_text = re.sub(r'</p>', '\n', html_text)
        html_text = re.sub(r'<[^>]+>', '', html_text)
        html_text = re.sub(r'\n\s*\n', '\n\n', html_text).strip()
        return html_text
    
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
        
        return self.extract_bio(html, artist_name)
    
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
    
    def scrape_lineup(self) -> List[dict]:
        """
        Scrape lineup and return list of artist dictionaries.
        Uses learned selectors first, prompts user if needed.
        
        Returns:
            List of dicts with 'name' and 'url' keys
        """
        html = self.fetch_page(self.config.lineup_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try learned selector first
        learned = self.learned_selectors.get(self.festival_key, {}).get('lineup_links_selector')
        if learned:
            try:
                links = soup.select(learned)
                if links:
                    print(f"  ✓ Using learned selector for lineup links: {learned}")
                    return self._process_artist_links(links, soup)
                else:
                    print(f"  ⚠️  Learned selector '{learned}' no longer works")
            except Exception as e:
                print(f"  ⚠️  Error with learned selector: {e}")
        
        # Try heuristic approach
        artists = self._try_lineup_heuristics(soup)
        if artists:
            print(f"  ✓ Found {len(artists)} artists using heuristics")
            return artists
        
        # If interactive and nothing found, ask user
        if self.interactive:
            print(f"\n  ⚠️  Could not find artist links automatically")
            selector = prompt_user_for_selector(
                'artist links (lineup/program page)',
                self.config.lineup_url,
                soup,
                hints=[
                    f'a[href*="{self.config.artist_path}"]',
                    '.artist-list a',
                    '.lineup-item a',
                    '.program-list a',
                    'a[href*="/artist"]',
                    'a[href*="/program"]',
                    'ul.artists a',
                    'div.lineup a'
                ]
            )
            
            if selector:
                # Save the learned selector
                self.learned_selectors[self.festival_key]['lineup_links_selector'] = selector
                self.session_learned = True
                
                # Extract using the new selector
                links = soup.select(selector)
                if links:
                    return self._process_artist_links(links, soup)
        
        return []
    
    def _scrape_grauzone_lineup(self, soup: BeautifulSoup) -> List[dict]:
        """Scrape Grauzone Festival Squarespace layout."""
        artists = []
        seen_names = set()
        
        # Find all artist name elements in image titles
        image_titles = soup.find_all('div', class_='image-title sqs-dynamic-text')
        
        for title_div in image_titles:
            p_tag = title_div.find('p')
            if not p_tag:
                continue
            
            raw_name = p_tag.get_text(strip=True)
            if not raw_name:
                continue
            
            # Clean up the artist name
            # Remove country codes like (US), (UK), etc.
            clean_name = re.sub(r'\s*\([A-Z/]+\)\s*$', '', raw_name)
            
            # Handle special cases
            if clean_name.startswith('DJ:'):
                clean_name = clean_name.replace('DJ:', 'DJ', 1).strip()
            elif clean_name.startswith("DJ'S:"):
                clean_name = clean_name.replace("DJ'S:", '', 1).strip()
            
            # Remove HTML entities
            clean_name = clean_name.replace('&amp;', '&')
            clean_name = re.sub(r'<[^>]+>', '', clean_name)  # Remove any HTML tags
            
            # Fix spacing issues (e.g., "AVISHAG<strong> </strong>C" -> "AVISHAG C")
            clean_name = re.sub(r'<strong>\s*</strong>', ' ', clean_name)
            clean_name = re.sub(r'\s+', ' ', clean_name)  # Collapse multiple spaces
            
            # Convert to title case, but preserve special formatting
            if clean_name.startswith('DJ '):
                # Keep DJ prefix, title case the rest
                clean_name = 'DJ ' + clean_name[3:].title()
            else:
                clean_name = clean_name.title()
                # Fix common acronyms and special names
                clean_name = clean_name.replace("'S", "'s")
                clean_name = clean_name.replace("B2B", "B2B")  # Keep uppercase
            
            # Skip duplicates and navigation items
            if clean_name in seen_names:
                continue
            if clean_name.lower() in ['faq', 'donate', 'tickets', 'line up', 'news', 'info', 'calendar', 'shop', 'policy', 'graukunst']:
                continue
            
            seen_names.add(clean_name)
            
            # Try to find a link to an artist page and image URL
            # Structure: div.image-title → figcaption → figure → a.image-inset
            artist_url = None
            image_url = None
            try:
                figcaption = title_div.find_parent('figcaption')
                if figcaption:
                    figure = figcaption.find_parent('figure')
                    if figure:
                        # Look for <a> tag with class 'image-inset' (or 'sqs-block-image-link')
                        link = figure.find('a', class_='sqs-block-image-link')
                        if link and link.get('href'):
                            href = link.get('href')
                            # Only accept internal festival links
                            if not href.startswith('http') or 'grauzonefestival.nl' in href:
                                if not any(x in href for x in ['/cart', '/faq', '/donate', '/tickets', '/news', '/info', '/shop', '/policy', '/new-events', '/graukunst']):
                                    artist_url = href if href.startswith('http') else f"{self.config.base_url}{href}"
                        
                        # Look for the image within the figure
                        img = figure.find('img')
                        if img:
                            # Try data-src first (Squarespace lazy loading), then src
                            image_url = img.get('data-src') or img.get('src')
            except Exception:
                pass  # Continue without URL if extraction fails
            
            artists.append({
                'name': clean_name,
                'url': artist_url or '',
                'image_url': image_url or ''
            })
        
        return artists
    
    def _try_lineup_heuristics(self, soup: BeautifulSoup) -> List[dict]:
        """Try heuristic patterns to find lineup links."""
        artists = []
        seen_urls = set()
        
        # Grauzone Festival specific: Squarespace layout with image titles
        if 'grauzone' in self.festival_key.lower():
            return self._scrape_grauzone_lineup(soup)
        
        # Look for links containing the artist path
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if self.config.artist_path in href:
                # Skip navigation/tab links (those with just day names)
                link_text = link.get_text(strip=True)
                if link_text in ['Overview', 'Friday', 'FridayFri', 'Saturday', 'SaturdaySat', 'Sunday', 'SundaySun', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']:
                    continue
                
                # Extract artist name from URL slug if link text seems to be a day/date
                artist_name = link_text
                
                # If link text is a day name, extract from URL instead
                if link_text in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Multiple acts']:
                    # Extract from URL: /bands/jack-white -> Jack White
                    url_parts = href.rstrip('/').split('/')
                    if url_parts:
                        slug = url_parts[-1]
                        # Convert slug to title: jack-white -> Jack White
                        artist_name = slug.replace('-', ' ').title()
                
                # Clean up artist name - remove day/date suffixes
                artist_name = re.sub(
                    r'\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d+\s+(January|February|March|April|May|June|July|August|September|October|November|December)$',
                    '', 
                    artist_name, 
                    flags=re.IGNORECASE
                ).strip()
                
                # Build full URL
                full_url = href if href.startswith('http') else f"{self.config.base_url}{href}"
                
                if artist_name and full_url not in seen_urls:
                    seen_urls.add(full_url)
                    artists.append({
                        'name': artist_name,
                        'url': full_url
                    })
        
        return artists
    
    def _process_artist_links(self, links: List, soup: BeautifulSoup) -> List[dict]:
        """Process a list of link elements into artist dicts."""
        artists = []
        seen_urls = set()
        
        for link in links:
            href = link.get('href', '')
            if not href:
                continue
            
            link_text = link.get_text(strip=True)
            
            # Skip navigation/tab links
            if link_text in ['Overview', 'Friday', 'FridayFri', 'Saturday', 'SaturdaySat', 'Sunday', 'SundaySun', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']:
                continue
            
            artist_name = link_text
            
            # If link text is a day name, extract from URL instead
            if link_text in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Multiple acts']:
                # Extract from URL: /bands/jack-white -> Jack White
                url_parts = href.rstrip('/').split('/')
                if url_parts:
                    slug = url_parts[-1]
                    # Convert slug to title: jack-white -> Jack White
                    artist_name = slug.replace('-', ' ').title()
            
            # Clean up artist name
            artist_name = re.sub(
                r'\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d+\s+(January|February|March|April|May|June|July|August|September|October|November|December)$',
                '', 
                artist_name, 
                flags=re.IGNORECASE
            ).strip()
            
            # Build full URL
            full_url = href if href.startswith('http') else f"{self.config.base_url}{href}"
            
            if artist_name and full_url not in seen_urls:
                seen_urls.add(full_url)
                artists.append({
                    'name': artist_name,
                    'url': full_url
                })
        
        return artists
    
    def save_learned_selectors_if_needed(self):
        """Save learned selectors if any were learned this session."""
        if self.session_learned:
            save_learned_selectors(self.learned_selectors)
            print(f"\n  🎓 Selectors learned this session have been saved!")
            print(f"     Next time we scrape {self.config.name}, it will be faster!")
            self.session_learned = False
    
    def rate_limit_delay(self, seconds: float = 0.5):
        """
        Add a delay to respect rate limits.
        
        Args:
            seconds: Number of seconds to wait
        """
        time.sleep(seconds)
    
    @staticmethod
    def convert_day_name_to_date(day_name: str, start_date: str, end_date: str) -> str:
        """
        Convert day name (e.g., 'Friday', 'Saturday') to actual date.
        
        Args:
            day_name: Day name like 'Monday', 'Tuesday', etc.
            start_date: Festival start date in YYYY-MM-DD format
            end_date: Festival end date in YYYY-MM-DD format
        
        Returns:
            Date in YYYY-MM-DD format or original day_name if conversion fails
        """
        if not day_name or not start_date or not end_date:
            return day_name
        
        # Parse dates
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return day_name
        
        # Calculate number of days
        num_days = (end - start).days + 1
        
        # Map day names to dates
        day_map = {}
        for i in range(num_days):
            current_date = start + timedelta(days=i)
            day_name_full = current_date.strftime('%A')  # Monday, Tuesday, etc.
            formatted_date = current_date.strftime('%Y-%m-%d')
            day_map[day_name_full] = formatted_date
        
        # Return the mapped date or original value if not found
        return day_map.get(day_name, day_name)
    
    @staticmethod
    def update_csv_day_column_to_dates(csv_file: Path, start_date: str, end_date: str) -> int:
        """
        Update Date column in CSV file from day names to actual dates.
        Also handles legacy 'Day' column name for backwards compatibility.
        
        Args:
            csv_file: Path to CSV file
            start_date: Festival start date in YYYY-MM-DD format
            end_date: Festival end date in YYYY-MM-DD format
        
        Returns:
            Number of rows updated
        """
        import csv
        
        if not csv_file.exists():
            return 0
        
        # Read all rows
        with csv_file.open('r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            # Check for either 'Date' or 'Day' column
            date_column = 'Date' if 'Date' in fieldnames else ('Day' if 'Day' in fieldnames else None)
            if not fieldnames or not date_column:
                return 0
            rows = list(reader)
        
        # Update Date/Day column
        updated_count = 0
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for row in rows:
            old_day = row.get(date_column, '')
            if old_day and old_day in day_names:
                new_day = FestivalScraper.convert_day_name_to_date(old_day, start_date, end_date)
                if new_day != old_day:
                    row[date_column] = new_day
                    updated_count += 1
        
        # Write back if updates were made
        if updated_count > 0:
            with csv_file.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        return updated_count

