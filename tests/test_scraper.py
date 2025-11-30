"""
Tests for festival_helpers/scraper.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from festival_helpers.scraper import FestivalScraper


class TestFestivalScraper:
    """Tests for FestivalScraper class."""
    
    def test_init(self, sample_dtrh_config):
        """Test scraper initialization."""
        scraper = FestivalScraper(sample_dtrh_config)
        assert scraper.config == sample_dtrh_config
        assert scraper.user_agent.startswith('Mozilla')
    
    def test_get_artist_page_url(self, sample_dtrh_config):
        """Test artist page URL generation."""
        scraper = FestivalScraper(sample_dtrh_config)
        url = scraper.get_artist_page_url("Test Artist")
        
        assert "downtherabbithole.nl" in url
        assert "test-artist" in url
    
    @patch('urllib.request.urlopen')
    def test_fetch_page_success(self, mock_urlopen, sample_dtrh_config):
        """Test successful page fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'<html>Test content</html>'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        scraper = FestivalScraper(sample_dtrh_config)
        html = scraper.fetch_page("https://test.com")
        
        assert html == '<html>Test content</html>'
        mock_urlopen.assert_called_once()
    
    @patch('urllib.request.urlopen')
    def test_fetch_page_404(self, mock_urlopen, sample_dtrh_config):
        """Test page fetch with 404 error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'https://test.com', 404, 'Not Found', {}, None
        )
        
        scraper = FestivalScraper(sample_dtrh_config)
        html = scraper.fetch_page("https://test.com")
        
        assert html is None
    
    def test_extract_bio_dtrh(self, sample_dtrh_config, sample_artist_html_dtrh):
        """Test bio extraction from DTRH HTML."""
        scraper = FestivalScraper(sample_dtrh_config)
        bio = scraper.extract_bio(sample_artist_html_dtrh)
        
        assert "testbio" in bio
        assert "Nederlandse artiest" in bio
        assert len(bio) > 50
    
    def test_extract_bio_pinkpop(self, sample_pinkpop_config, sample_artist_html_pinkpop):
        """Test bio extraction from Pinkpop HTML."""
        scraper = FestivalScraper(sample_pinkpop_config)
        bio = scraper.extract_bio(sample_artist_html_pinkpop)
        
        assert "test bio" in bio.lower()
        assert "English artist" in bio
        assert len(bio) > 50
    
    def test_extract_bio_no_match(self, sample_dtrh_config):
        """Test bio extraction with no matching pattern."""
        scraper = FestivalScraper(sample_dtrh_config)
        bio = scraper.extract_bio("<html><body>No bio here</body></html>")
        
        assert bio == ""
    
    def test_extract_spotify_link(self, sample_dtrh_config, sample_artist_html_dtrh):
        """Test Spotify link extraction."""
        scraper = FestivalScraper(sample_dtrh_config)
        link = scraper.extract_spotify_link(sample_artist_html_dtrh)
        
        assert link == "https://open.spotify.com/artist/1234567890"
    
    def test_extract_spotify_link_no_match(self, sample_dtrh_config):
        """Test Spotify link extraction with no match."""
        scraper = FestivalScraper(sample_dtrh_config)
        link = scraper.extract_spotify_link("<html>No spotify link</html>")
        
        assert link is None
    
    @patch('urllib.request.urlopen')
    def test_fetch_lineup_artists(self, mock_urlopen, sample_dtrh_config, sample_lineup_html):
        """Test lineup artist fetching."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = sample_lineup_html.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        scraper = FestivalScraper(sample_dtrh_config)
        artists = scraper.fetch_lineup_artists()
        
        assert len(artists) == 3
        assert "Artist One" in artists
        assert "Artist Two" in artists
        assert "Artist Three" in artists
        assert "About" not in artists
    
    @patch('urllib.request.urlopen')
    def test_scrape_lineup(self, mock_urlopen, sample_dtrh_config, sample_lineup_html):
        """Test lineup scraping with URLs."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = sample_lineup_html.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        scraper = FestivalScraper(sample_dtrh_config)
        artists = scraper.scrape_lineup()
        
        assert len(artists) == 3
        assert all('name' in artist and 'url' in artist for artist in artists)
        assert artists[0]['name'] == "Artist One"
        assert "/programma/artist-one" in artists[0]['url']
    
    def test_rate_limit_delay(self, sample_dtrh_config):
        """Test rate limiting delay."""
        import time
        scraper = FestivalScraper(sample_dtrh_config)
        
        start = time.time()
        scraper.rate_limit_delay(0.1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert elapsed < 0.2  # Allow some margin
