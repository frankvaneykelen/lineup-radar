"""
Tests for festival_helpers/slug.py
"""
import pytest
from festival_helpers.slug import artist_name_to_slug, get_sort_name


class TestArtistNameToSlug:
    """Tests for artist_name_to_slug function."""
    
    def test_simple_name(self):
        """Test simple artist name."""
        assert artist_name_to_slug("Radiohead") == "radiohead"
    
    def test_name_with_spaces(self):
        """Test name with multiple spaces."""
        assert artist_name_to_slug("The National") == "the-national"
    
    def test_name_with_ampersand(self):
        """Test name with ampersand."""
        assert artist_name_to_slug("Mumford & Sons") == "mumford-sons"
    
    def test_name_with_special_chars(self):
        """Test name with special characters."""
        assert artist_name_to_slug("Sigur Rós") == "sigur-ros"
    
    def test_name_with_numbers(self):
        """Test name with numbers."""
        assert artist_name_to_slug("Twenty One Pilots") == "twenty-one-pilots"
    
    def test_name_with_quotes(self):
        """Test name with quotes."""
        assert artist_name_to_slug("A'ja Wilson") == "aja-wilson"
    
    def test_name_with_emoji(self):
        """Test name with emoji (should be removed)."""
        result = artist_name_to_slug("Test 🎵 Artist")
        assert result == "test-artist"
    
    def test_name_already_lowercase(self):
        """Test name that's already lowercase."""
        assert artist_name_to_slug("gorillaz") == "gorillaz"
    
    def test_empty_string(self):
        """Test empty string."""
        assert artist_name_to_slug("") == ""
    
    def test_multiple_consecutive_spaces(self):
        """Test multiple consecutive spaces."""
        assert artist_name_to_slug("The  National") == "the-national"


class TestGetSortName:
    """Tests for get_sort_name function."""
    
    def test_name_without_article(self):
        """Test name without article."""
        assert get_sort_name("Radiohead") == "Radiohead"
    
    def test_name_with_the(self):
        """Test name starting with 'The'."""
        assert get_sort_name("The National") == "National"
    
    def test_name_with_a(self):
        """Test name starting with 'A'."""
        # get_sort_name only handles 'The', not other articles
        assert get_sort_name("A Perfect Circle") == "A Perfect Circle"
    
    def test_name_with_an(self):
        """Test name starting with 'An'."""
        # get_sort_name only handles 'The', not other articles
        assert get_sort_name("An Artist") == "An Artist"
    
    def test_lowercase_article(self):
        """Test lowercase article."""
        assert get_sort_name("the national") == "national"
    
    def test_name_with_de(self):
        """Test Dutch article 'De'."""
        # get_sort_name only handles 'The', not Dutch articles
        assert get_sort_name("De Staat") == "De Staat"
    
    def test_name_with_het(self):
        """Test Dutch article 'Het'."""
        # get_sort_name only handles 'The', not Dutch articles
        assert get_sort_name("Het Goede Doel") == "Het Goede Doel"
    
    def test_single_word_name(self):
        """Test single word name."""
        assert get_sort_name("Gorillaz") == "Gorillaz"
    
    def test_empty_string(self):
        """Test empty string."""
        assert get_sort_name("") == ""
    
    def test_just_article(self):
        """Test name that's just an article."""
        assert get_sort_name("The") == "The"
