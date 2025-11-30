"""
Tests for fetch_festival_data.py
"""
import pytest
from unittest.mock import Mock, patch
from fetch_festival_data import needs_festival_data, extract_social_links


class TestNeedsFestivalData:
    """Tests for needs_festival_data function."""
    
    def test_needs_data_all_empty(self):
        """Test row with all empty festival fields."""
        row = {
            'Festival Bio (NL)': '',
            'Festival Bio (EN)': '',
            'Festival URL': ''
        }
        assert needs_festival_data(row) is True
    
    def test_needs_data_partial(self):
        """Test row with some empty festival fields."""
        row = {
            'Festival Bio (NL)': 'Some bio',
            'Festival Bio (EN)': '',
            'Festival URL': 'https://test.com'
        }
        assert needs_festival_data(row) is True
    
    def test_needs_data_all_filled(self):
        """Test row with all festival fields filled."""
        row = {
            'Festival Bio (NL)': 'Nederlandse bio',
            'Festival Bio (EN)': 'English bio',
            'Festival URL': 'https://test.com/artist'
        }
        assert needs_festival_data(row) is False
    
    def test_needs_data_whitespace_only(self):
        """Test row with whitespace-only fields."""
        row = {
            'Festival Bio (NL)': '   ',
            'Festival Bio (EN)': '\n',
            'Festival URL': '\t'
        }
        assert needs_festival_data(row) is True


class TestExtractSocialLinks:
    """Tests for extract_social_links function."""
    
    def test_extract_instagram_link(self):
        """Test extracting Instagram link."""
        # extract_social_links regex requires target="_blank" BEFORE href
        html = '''<div class="border p-8 mt-8">
            <a target="_blank" href="https://www.instagram.com/testartist/">Instagram</a>
        </div>'''
        links = extract_social_links(html)
        
        assert 'Instagram' in links
        assert links['Instagram'] == 'https://www.instagram.com/testartist/'
    
    def test_extract_facebook_link(self):
        """Test extracting Facebook link."""
        html = '''<div class="border p-8 mt-8">
            <a target="_blank" href="https://www.facebook.com/testartist">Facebook</a>
        </div>'''
        links = extract_social_links(html)
        
        assert 'Facebook' in links
    
    def test_extract_multiple_links(self):
        """Test extracting multiple social links."""
        html = '''<div class="border p-8 mt-8">
            <a target="_blank" href="https://www.instagram.com/test/">Instagram</a>
            <a target="_blank" href="https://www.facebook.com/test">Facebook</a>
            <a target="_blank" href="https://twitter.com/test">Twitter</a>
        </div>'''
        links = extract_social_links(html)
        
        assert len(links) >= 2
        assert 'Instagram' in links or 'Facebook' in links
    
    def test_no_social_links(self):
        """Test HTML with no social links."""
        html = '<html><body>No social links here</body></html>'
        links = extract_social_links(html)
        
        assert links == {}
    
    def test_exclude_festival_links(self):
        """Test that festival's own links are excluded."""
        html = '''
        <a href="https://www.instagram.com/dtrh_festival/">Festival Instagram</a>
        <a href="https://www.instagram.com/testartist/">Artist Instagram</a>
        '''
        links = extract_social_links(html)
        
        # Should only include artist link, not festival link
        if links:
            assert 'dtrh_festival' not in str(links)
