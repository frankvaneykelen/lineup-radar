"""
Pytest configuration and shared fixtures.
"""
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from helpers.config import FestivalConfig


@pytest.fixture
def sample_dtrh_config():
    """Sample Down The Rabbit Hole festival configuration."""
    return FestivalConfig(
        name="Down The Rabbit Hole Test",
        year=2026,
        slug="down-the-rabbit-hole-test",
        base_url="https://downtherabbithole.nl",
        lineup_url="https://downtherabbithole.nl/programma",
        artist_path="/programma/",
        bio_language="Dutch"
    )


@pytest.fixture
def sample_pinkpop_config():
    """Sample Pinkpop festival configuration."""
    return FestivalConfig(
        name="Pinkpop Test",
        year=2026,
        slug="pinkpop-test",
        base_url="https://www.pinkpop.nl",
        lineup_url="https://www.pinkpop.nl/en/programme/",
        artist_path="/en/programme/",
        bio_language="English"
    )


@pytest.fixture
def sample_artist_html_dtrh():
    """Sample DTRH artist page HTML."""
    return """
    <html>
        <body>
            <h1>Test Artist</h1>
            <div class="column text-xl font-normal prose !max-w-none">
                <p>Dit is een testbio van een Nederlandse artiest. 
                Deze artiest maakt geweldige muziek en heeft al meerdere albums uitgebracht.</p>
            </div>
            <a href="https://open.spotify.com/artist/1234567890">Spotify</a>
            <a href="https://www.instagram.com/testartist/">Instagram</a>
        </body>
    </html>
    """


@pytest.fixture
def sample_artist_html_pinkpop():
    """Sample Pinkpop artist page HTML."""
    return """
    <html>
        <body>
            <h1>Test Artist</h1>
            <p>This is a test bio of an English artist. This artist makes great music 
            and has released multiple albums over the years.</p>
            <a href="https://open.spotify.com/artist/1234567890">Spotify</a>
            <a href="https://www.facebook.com/testartist/">Facebook</a>
        </body>
    </html>
    """


@pytest.fixture
def sample_lineup_html():
    """Sample lineup page HTML."""
    return """
    <html>
        <body>
            <h2>Lineup</h2>
            <a href="/programma/artist-one">Artist One</a>
            <a href="/programma/artist-two">Artist Two</a>
            <a href="/programma/artist-three">Artist Three</a>
            <a href="/about">About</a>
        </body>
    </html>
    """


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return {
        'headers': [
            'Artist', 'Genre', 'Country', 'Bio', 'AI Summary', 'AI Rating',
            'Spotify link', 'Number of People in Act', 'Gender of Front Person',
            'Front Person of Color?', 'Festival URL', 'Festival Bio (NL)',
            'Festival Bio (EN)', 'Social Links', 'Images Scraped'
        ],
        'rows': [
            {
                'Artist': 'Test Artist',
                'Genre': 'Rock',
                'Country': 'USA',
                'Bio': 'Test bio',
                'AI Summary': 'Great artist',
                'AI Rating': '8',
                'Spotify link': 'https://open.spotify.com/artist/123',
                'Number of People in Act': '4',
                'Gender of Front Person': 'Male',
                'Front Person of Color?': 'No',
                'Festival URL': 'https://festival.com/artists/test-artist',
                'Festival Bio (NL)': 'Nederlandse bio',
                'Festival Bio (EN)': 'English bio',
                'Social Links': '{"Instagram": "https://instagram.com/test"}',
                'Images Scraped': 'Yes'
            }
        ]
    }


@pytest.fixture
def temp_csv_file(tmp_path, sample_csv_data):
    """Create a temporary CSV file for testing."""
    import csv
    
    csv_file = tmp_path / "test_festival.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sample_csv_data['headers'])
        writer.writeheader()
        writer.writerows(sample_csv_data['rows'])
    
    return csv_file
