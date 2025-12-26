#!/usr/bin/env python3
"""
Universal Festival Scraper

Scrapes festival lineups from various festival websites based on configuration.
Supports multiple scraping strategies:
- HTML structure scraping (Best Kept Secret style)
- Manual CSV import (Footprints style)
- Generic festival page scraping
"""

import sys
from pathlib import Path

# Add parent directory to sys.path to import festival_helpers
import sys
sys.path.insert(0, str(Path(__file__).parent))

import csv
import json
import argparse
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from helpers.config import get_festival_config, FESTIVALS
from helpers.slug import artist_name_to_slug


def download_image(url: str, save_path: Path) -> bool:
    """Download an image from a URL to a local file."""
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Create parent directory if needed
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  ❌ Error downloading image: {e}")
        return False


class UniversalFestivalScraper:
    """Universal scraper that adapts to different festival website structures."""
    
    def __init__(self, festival_slug: str, year: int):
        self.config = get_festival_config(festival_slug, year)
        self.festival_slug = festival_slug
        self.year = year
        self.festival_config = FESTIVALS.get(festival_slug, {})
    
    def scrape(self) -> List[Dict]:
        """Main scraping method that routes to appropriate strategy."""
        # Check for manual CSV first (Footprints-style)
        if self._has_manual_csv():
            return self._scrape_from_manual_csv()
        # Custom scraper for Rewire
        if self.festival_slug == 'rewire':
            return self._scrape_rewire()
        # Check for custom scraper configuration
        scraper_type = self.festival_config.get('scraper_type', 'generic')
        if scraper_type == 'best-kept-secret':
            return self._scrape_best_kept_secret()
        elif scraper_type == 'tivoli-venue':
            return self._scrape_tivoli_venue()
        else:
            return self._scrape_generic()

    def _scrape_rewire(self) -> List[Dict]:
        """Scrape Rewire festival lineup using Selenium for JavaScript rendering."""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        import time
        import re

        url = self.config.lineup_url
        print(f"\n[selenium] Fetching: {url}")
        options = Options()
        # options.add_argument('--headless')  # Disabled for debugging
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(executable_path="C:/chromedriver-win64/chromedriver.exe", options=options)
        driver.get(url)
        time.sleep(3)  # Wait for JS to load

        artists = []
        links = driver.find_elements(By.ID, 'artistcard')
        for a in links:
            try:
                href = a.get_attribute('href')
                name = ''
                day = ''
                image_url = ''
                # Get artist name
                info_div = a.find_element(By.ID, 'info')
                h1 = info_div.find_element(By.TAG_NAME, 'h1')
                name = h1.text.strip()
                # Get day
                img_div = a.find_element(By.ID, 'img')
                datetag = img_div.find_element(By.ID, 'datetag')
                day = datetag.text.strip()
                # Compose full artist URL
                full_url = href if href.startswith('http') else f"https://www.rewirefestival.nl{href}"
                # Visit artist detail page to get best image
                print(f"    [img search] Preparing to launch Selenium driver for: {full_url}")
                try:
                    driver2 = webdriver.Chrome(executable_path="C:/chromedriver-win64/chromedriver.exe", options=options)
                    print(f"    [img search] Selenium driver launched for: {full_url}")
                except Exception as e:
                    print(f"    [img search] ERROR launching Selenium driver: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                try:
                    driver2.get(full_url)
                    print(f"    [img search] Navigated to detail page: {full_url}")
                    # Save screenshot for debugging
                    slug = name.lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
                    screenshot_path = f"{slug}_debug.png"
                    driver2.save_screenshot(screenshot_path)
                    print(f"    [img search] Screenshot saved: {screenshot_path}")
                except Exception as e:
                    print(f"    [img search] ERROR navigating to detail page: {e}")
                    import traceback
                    traceback.print_exc()
                    driver2.quit()
                    continue
                time.sleep(3)
                try:
                    print(f"    [img search] Page title: {driver2.title}")
                    print(f"    [img search] Current URL: {driver2.current_url}")
                    print(f"    [img search] Page source length: {len(driver2.page_source)}")
                    img_tags = driver2.find_elements(By.TAG_NAME, 'img')
                    print(f"    [img search] Found {len(img_tags)} <img> tags on detail page for {name}")
                    for idx, img in enumerate(img_tags):
                        print(f"      [img {idx}] src: {img.get_attribute('src')}")
                        print(f"      [img {idx}] srcset: {img.get_attribute('srcset')}")
                        print(f"      [img {idx}] alt: {img.get_attribute('alt')}")
                        print(f"      [img {idx}] class: {img.get_attribute('class')}")
                    best_img = None
                    best_width = 0
                    print(f"    [img search] --- Begin candidate selection ---")
                    for img in img_tags:
                        src = img.get_attribute('src')
                        if src and (src.endswith('.jpg') or src.endswith('.png')):
                            print(f"      [img] Candidate: {src}")
                            # Prefer prismic.io/rewirefestival but accept any .jpg/.png
                            if 'prismic.io/rewirefestival' in src:
                                print(f"      [img] Selected (prismic): {src}")
                                best_img = img
                                break
                            if not best_img:
                                print(f"      [img] Selected (first .jpg/.png): {src}")
                                best_img = img
                    print(f"    [img search] --- End candidate selection ---")
                    if best_img:
                        srcset = best_img.get_attribute('srcset')
                        if srcset:
                            candidates = [s.strip().split(' ') for s in srcset.split(',')]
                            print(f"      [img] srcset: {srcset}")
                            max_url = max(candidates, key=lambda x: int(x[1][:-1]) if len(x) > 1 and x[1].endswith('w') else 0)[0]
                            print(f"      [img] Selected highest-res from srcset: {max_url}")
                            image_url = max_url
                        else:
                            image_url = best_img.get_attribute('src')
                            print(f"      [img] Selected src: {image_url}")
                    else:
                        print(f"    ⚠️ No suitable .jpg/.png image found for {name}")
                except Exception as e:
                    import traceback
                    print(f"    ⚠️ No detail image for {name}: {e}")
                    traceback.print_exc()
                driver2.quit()
                artists.append({
                    'Artist': name,
                    'Day': day,
                    'Stage': '',
                    'Cancelled': '',
                    'AI Summary': '',
                    'AI Rating': '',
                    'Tagline': '',
                    'Start Time': '',
                    'End Time': '',
                    'Genre': '',
                    'Country': '',
                    'Bio': '',
                    'Website': '',
                    'Spotify': '',
                    'YouTube': '',
                    'Instagram': '',
                    'Number of People in Act': '',
                    'Gender of Front Person': '',
                    'Front Person of Color?': '',
                    'Festival URL': full_url,
                    'Festival Bio (NL)': '',
                    'Festival Bio (EN)': '',
                    'Social Links': '',
                    'Images Scraped': image_url
                })
                print(f"  ✓ {name} ({day})")
            except Exception as e:
                print(f"  ⚠️ Error parsing artist: {e}")
        driver.quit()
        print(f"✓ Parsed {len(artists)} artists from Rewire lineup page (Selenium)")
        return artists
    
    def _has_manual_csv(self) -> bool:
        """Check if a manual CSV file exists (Book(Sheet1).csv)."""
        csv_path = Path(self.config.output_dir) / "Book(Sheet1).csv"
        return csv_path.exists()
    
    def _scrape_from_manual_csv(self) -> List[Dict]:
        """Import data from manually created CSV file."""
        csv_path = Path(self.config.output_dir) / "Book(Sheet1).csv"
        
        print(f"\n✓ Found Book(Sheet1).csv - using pre-filled data")
        print(f"  Reading from: {csv_path}")
        
        artists = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                artist_name = row.get('Name', '').strip()
                if not artist_name:
                    continue
                
                artists.append({
                    'Artist': artist_name,
                    'Genre': row.get('Genre', '').strip(),
                    'Country': row.get('Country', '').strip(),
                    'Bio': row.get('Bio', '').strip(),
                    'AI Summary': row.get('Live Assessment', '').strip(),
                    'AI Rating': '',
                    'Number of People in Act': row.get('# in Act', '').strip(),
                    'Gender of Front Person': row.get('Front Person Gender', '').strip(),
                    'Front Person of Color?': row.get('Front Person of Color?', '').strip(),
                    'Tagline': '',
                    'Day': '',
                    'Start Time': '',
                    'End Time': '',
                    'Stage': '',
                    'Website': '',
                    'Spotify': '',
                    'YouTube': '',
                    'Instagram': '',
                    'Cancelled': '',
                    'Festival URL': '',
                    'Festival Bio (NL)': '',
                    'Festival Bio (EN)': '',
                    'Social Links': '',
                    'Images Scraped': 'No'
                })
        
        print(f"✓ Parsed {len(artists)} artists from Book(Sheet1).csv")
        return artists
    
    def _scrape_best_kept_secret(self) -> List[Dict]:
        """Scrape Best Kept Secret using their specific HTML structure."""
        url = self.config.lineup_url
        
        print(f"\nFetching: {url}")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        artists = []
        act_items = soup.select('li.act-list__item')
        print(f"Found {len(act_items)} artist entries\n")
        
        for item in act_items:
            link = item.select_one('a.act')
            if not link:
                continue
            
            href = link.get('href', '')
            if not href or '/bands/' not in href:
                continue
            
            # Extract artist name from span
            name_elem = link.select_one('.act__content .act__title span')
            if not name_elem:
                continue
            artist_name = name_elem.get_text(strip=True)
            
            # Extract tagline
            tagline_elem = link.select_one('.act__content .act__tagline')
            tagline = tagline_elem.get_text(strip=True) if tagline_elem else ''
            
            # Extract image URL
            img_elem = link.select_one('img[data-cb-image-format="default_act_item"]')
            photo_url = img_elem.get('src', '') if img_elem else ''
            
            # Extract day
            day_elem = link.select_one('.act__content-meta span')
            day = day_elem.get_text(strip=True) if day_elem else ''
            
            # Build full URL
            full_url = f"https://www.bestkeptsecret.nl{href}" if href.startswith('/') else href
            
            artists.append({
                'Artist': artist_name,
                'Tagline': tagline,
                'Day': day,
                '_image_url': photo_url,
                'Festival URL': full_url,
                'Start Time': '',
                'End Time': '',
                'Stage': '',
                'Genre': '',
                'Country': '',
                'Bio': '',
                'Website': '',
                'Spotify': '',
                'YouTube': '',
                'Instagram': '',
                'AI Summary': '',
                'AI Rating': '',
                'Number of People in Act': '',
                'Gender of Front Person': '',
                'Front Person of Color?': '',
                'Cancelled': '',
                'Festival Bio (NL)': '',
                'Festival Bio (EN)': '',
                'Social Links': '',
                'Images Scraped': ''
            })
            
            print(f"  ✓ {artist_name} ({day})")
        
        return artists
    
    def _scrape_tivoli_venue(self) -> List[Dict]:
        """Scrape TivoliVredenburg venue page (Footprints style)."""
        url = self.config.lineup_url
        artists = []
        
        try:
            print(f"\nFetching: {url}")
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for artist names and bios in accordion items
            accordions = soup.find_all('div', class_='js-accordion accordion')
            for accordion in accordions:
                title_div = accordion.find('div', class_='js-accordion-trigger accordion__title')
                if title_div:
                    h2 = title_div.find('h2')
                    if h2:
                        artist_name = h2.text.strip()
                        # Filter out u-pas entry
                        if 'u-pas' not in artist_name.lower() and artist_name:
                            # Get bio from accordion content
                            content_div = accordion.find('div', class_='js-accordion-target')
                            bio = ''
                            if content_div:
                                paragraphs = content_div.find_all('p')
                                bio = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
                            
                            artists.append({
                                'Artist': artist_name,
                                'Bio': bio,
                                'Tagline': '',
                                'Day': '',
                                'Start Time': '',
                                'End Time': '',
                                'Stage': '',
                                'Genre': '',
                                'Country': '',
                                'Website': '',
                                'Spotify': '',
                                'YouTube': '',
                                'Instagram': '',
                                'AI Summary': '',
                                'AI Rating': '',
                                'Number of People in Act': '',
                                'Gender of Front Person': '',
                                'Front Person of Color?': '',
                                'Cancelled': '',
                                'Festival URL': url,
                                'Festival Bio (NL)': '',
                                'Festival Bio (EN)': '',
                                'Social Links': '',
                                'Images Scraped': 'No'
                            })
            
            print(f"✓ Found {len(artists)} artists with bios from venue page")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"⚠ The venue page returned a 403 Forbidden error.")
                print(f"\n📥 Please download the page manually:")
                print(f"   1. Open {url} in your browser")
                print(f"   2. Right-click and select 'Save As...'")
                print(f"   3. Save in current directory and re-run script\n")
            else:
                print(f"⚠ Error scraping venue page: {e}")
        
        return artists
    
    def _scrape_generic(self) -> List[Dict]:
        """Generic scraper for standard festival pages."""
        # This would use the existing FestivalScraper from festival_helpers
        from helpers.scraper import FestivalScraper
        
        print(f"\nUsing generic scraper for {self.config.name}")
        scraper = FestivalScraper(self.config)
        lineup = scraper.scrape_lineup()
        
        # Convert to standard format
        artists = []
        for artist in lineup:
            artists.append({
                'Artist': artist.get('name', ''),
                'Festival URL': artist.get('url', ''),
                '_image_url': artist.get('image_url', ''),
                'Tagline': '',
                'Day': '',
                'Start Time': '',
                'End Time': '',
                'Stage': '',
                'Genre': '',
                'Country': '',
                'Bio': '',
                'Website': '',
                'Spotify': '',
                'YouTube': '',
                'Instagram': '',
                'AI Summary': '',
                'AI Rating': '',
                'Number of People in Act': '',
                'Gender of Front Person': '',
                'Front Person of Color?': '',
                'Cancelled': '',
                'Festival Bio (NL)': '',
                'Festival Bio (EN)': '',
                'Social Links': '',
                'Images Scraped': 'No'
            })
        
        return artists
    
    def download_images(self, artists: List[Dict]) -> List[Dict]:
        """Download images from image URLs to artist folders."""
        print("\nDownloading artist images...")
        downloaded_count = 0
        
        for artist in artists:
            photo_url = artist.get('_image_url', '')
            if not photo_url:
                continue
            
            artist_name = artist.get('Artist', '')
            if not artist_name:
                continue
            
            # Generate slug for artist
            slug = artist_name_to_slug(artist_name)
            
            # Determine file extension from URL
            ext = '.jpg'
            if photo_url.lower().endswith('.png'):
                ext = '.png'
            elif photo_url.lower().endswith('.webp'):
                ext = '.webp'
            elif photo_url.lower().endswith('.jpeg'):
                ext = '.jpeg'
            
            # Create artist directory and image path
            artist_dir = Path(f"docs/{self.festival_slug}/{self.year}/artists/{slug}")
            image_path = artist_dir / f"{slug}_1{ext}"
            
            # Check if image already exists
            if image_path.exists():
                # Mark as scraped even if it already exists
                artist['Images Scraped'] = 'Yes'
                continue
            
            # Download the image
            print(f"  Downloading {artist_name}...")
            if download_image(photo_url, image_path):
                downloaded_count += 1
                # Update CSV to mark images as scraped
                artist['Images Scraped'] = 'Yes'
        
        if downloaded_count > 0:
            print(f"✓ Downloaded {downloaded_count} images")
        else:
            print("  No new images to download")
        
        return artists
    
    def write_csv(self, artists: List[Dict]):
        """Write artists to CSV file."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.year}.csv"
        
        # Standard field order from template
        fieldnames = [
            'Artist', 'Tagline', 'Day', 'Start Time', 'End Time', 'Stage',
            'Genre', 'Country', 'Bio', 'Website', 
            'Spotify', 'YouTube', 'Instagram',
            'AI Summary', 'AI Rating', 
            'Number of People in Act', 'Gender of Front Person', 'Front Person of Color?',
            'Cancelled', 'Festival URL', 'Festival Bio (NL)', 'Festival Bio (EN)', 
            'Social Links', 'Images Scraped'
        ]
        
        print(f"\nWriting to: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for artist in artists:
                # Ensure all fields are present
                row = {field: artist.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"✓ Wrote {len(artists)} artists to CSV")
        return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Universal festival lineup scraper"
    )
    parser.add_argument(
        "festival",
        type=str,
        help="Festival slug (e.g., 'best-kept-secret', 'footprints', 'down-the-rabbit-hole')"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Festival year (default: 2026)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print(f"Festival Lineup Scraper - {args.festival.upper()} {args.year}")
    print("=" * 60)
    
    try:
        scraper = UniversalFestivalScraper(args.festival, args.year)
        artists = scraper.scrape()
        
        if not artists:
            print("\n❌ No artists found!")
            return 1
        
        print(f"\n✓ Found {len(artists)} artists total")
        
        # Download images if Photo URLs are available
        artists = scraper.download_images(artists)
        
        output_path = scraper.write_csv(artists)
        
        print("\n" + "=" * 60)
        print("Scraping Complete!")
        print("=" * 60)
        
        # Generate README for this festival edition
        try:
            from generate_festival_readme import generate_readme
            readme_path = generate_readme(args.festival, args.year)
            print(f"\n📄 Updated {readme_path}")
        except Exception as e:
            print(f"\n⚠ Could not generate README: {e}")
        
        print(f"\nNext steps:")
        print(f"1. Review the CSV: {output_path}")
        print(f"2. Run: python scripts/fetch_festival_data.py --festival {args.festival} --year {args.year}")
        print(f"3. Run: python scripts/enrich_artists.py {args.festival} {args.year}")
        print(f"4. Run: .\\scripts\\regenerate_all.ps1")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
