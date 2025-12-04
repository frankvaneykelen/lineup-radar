# Frank's LineupRadar - Multi-Festival Program Tracker

A personal tracking system for multiple festival programs, maintaining detailed information about artists performing at various festivals each year.

## Purpose

This project helps track and rate artists performing at different festivals. Each festival has its own folder structure with CSV files per year, containing comprehensive artist information including genres, ratings, and personal notes.

## Supported Festivals

- **Down The Rabbit Hole** (Dutch, Beuningen)
- **Pinkpop** (English, Landgraaf)
- **Rock Werchter** (English, Werchter)
- **Footprints Festival** (Dutch, Utrecht - custom scraper with Spotify integration)

Each festival can have its own configuration (language, scraping patterns, etc.).

## Structure

### Festival Organization

- Festivals are organized within the `docs/` directory structure
- Each festival has: `docs/festival-slug/year/year.csv` (e.g., `docs/pinkpop/2026/2026.csv`)
- Festival configuration is stored in `festival_helpers/config.py`
- This structure keeps all published content (CSV + HTML) together

### CSV Files

- One CSV file per festival year stored in `docs/festival-slug/year/year.csv`
- Examples: `docs/down-the-rabbit-hole/2026/2026.csv`, `docs/pinkpop/2026/2026.csv`
- Each file contains the following columns:
  - **Artist**: Name of the artist/band
  - **Genre**: Musical genre
  - **Country**: Country of origin
  - **Bio**: Brief artist biography
  - **My take**: Personal notes and impressions
  - **My rating**: Personal rating (scale: 1-10)
  - **Spotify link**: Link to artist's Spotify profile
  - **Number of People in Act**: Band size
  - **Gender of Front Person**: Gender identification of lead performer
  - **Front Person of Color?**: Yes/No indicator
  - **Cancelled**: Yes/No indicator if the artist has cancelled their performance

### Metadata Tracking

- The system maintains a separate metadata file to track user edits
- This ensures that personal notes (My take, My rating) are never overwritten when updating artist information
- When new artists are announced, only those new entries are added

## Usage

### Setting Up on a New Device

After cloning the repository on a new machine, follow these steps to get the project running:

1. **Clone the repository** (if you haven't already):

   ```powershell
   git clone https://github.com/frankvaneykelen/lineup-radar.git
   cd lineup-radar
   ```

2. **Configure Python environment**:

   The repository includes a pre-configured `.venv` virtual environment. If it doesn't exist or is corrupted, create a new one:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:

   With the virtual environment activated, install all required packages:

   ```powershell
   pip install -r requirements.txt
   ```

   This installs:
   - **beautifulsoup4** - Web scraping library
   - **requests** - HTTP requests library
   - **openai** - Azure OpenAI client for AI enrichment

4. **Verify installation**:

   ```powershell
   python -c "import bs4, requests, openai; print('All dependencies installed!')"
   ```

5. **Run tests to ensure everything works**:

   ```powershell
   pytest tests/ -v
   ```

You're now ready to use the project! Follow the sections below for specific tasks.

### Initial Setup

For adding a new festival:

1. Add festival configuration to `festival_helpers/config.py` in the `FESTIVALS` dictionary:

   ```python
   'festival-slug': {
       'name': 'Festival Name',
       'base_url': 'https://festival.com',
       'lineup_url': 'https://festival.com/lineup',
       'artist_path': '/artist/',
       'bio_language': 'English',  # or 'Dutch'
   }
   ```

2. Activate virtual environment: `.venv\Scripts\Activate.ps1`
3. Scrape initial lineup: `python scripts/fetch_festival_data.py --festival festival-slug --year 2026`
4. The script will automatically create the directory structure and CSV file with all artists

### Updating with New Artists

When new artists are announced on the festival website, follow these steps:

#### Step 1: Scrape lineup from website

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Then run fetch commands
python scripts/fetch_festival_data.py --festival down-the-rabbit-hole --year 2026
python scripts/fetch_festival_data.py --festival pinkpop --year 2026
python scripts/fetch_festival_data.py --festival rock-werchter --year 2026

# For Footprints Festival (custom scraper with Spotify + venue page):
python scripts/scrape_footprints.py --year 2026
```

This will:

1. Fetch the lineup from the festival's program page
2. Scrape artist bios in the festival's language (Dutch/English)
3. Extract social media links and images
4. Track your existing edits to "My take" and "My rating"
5. Add only new artists (preserving all existing user edits)

Your personal notes (My take, My rating) are never overwritten during updates.

#### Step 2: Enriching Artist Data

After scraping new artists, you can enrich their data with AI:

**AI-powered enrichment:**

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
python scripts/enrich_artists.py --festival down-the-rabbit-hole --year 2026 --ai --parallel
python scripts/enrich_artists.py --festival pinkpop --year 2026 --ai --parallel
python scripts/enrich_artists.py --festival rock-werchter --year 2026 --ai --parallel
python scripts/enrich_artists.py --festival footprints --year 2026 --ai --parallel
```

This requires API setup. Run `python scripts/enrich_artists.py --setup` for instructions.

**Quick setup example (Azure OpenAI):**

```powershell
$env:AZURE_OPENAI_KEY = "your-azure-openai-key-here"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.cognitiveservices.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
python scripts/enrich_artists.py --ai --parallel
```

The AI will automatically populate all empty fields including:

- **Objective data**: Genre, Country, Bio, Spotify links, group size, demographics
- **Subjective analysis**: "My take" (critical assessment based on reviews) and "My rating" (1-10 based on critical consensus)

**Important**: Once you edit "My take" or "My rating" manually, those fields will never be overwritten by future AI enrichments. Your personal edits are always preserved.

**Note:** When AI lacks data for an artist, the system automatically uses the festival bio as a fallback, prefixed with "[using festival bio due to a lack of publicly available data]".

#### Step 3: Fetch Spotify Links

After enriching artist data, you can fetch official Spotify links from the festival website or Spotify API:

##### Option 1: Scrape from festival pages (DTRH, Pinkpop, Rock Werchter)

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
python scripts/fetch_spotify_links.py --festival down-the-rabbit-hole --year 2026
python scripts/fetch_spotify_links.py --festival pinkpop --year 2026
python scripts/fetch_spotify_links.py --festival rock-werchter --year 2026
```

##### Option 2: Use Spotify API (Footprints and others)

For festivals that don't embed Spotify links on artist pages (like Footprints), use the Spotify API:

```powershell
# First, set up Spotify API credentials (one-time setup):
$env:SPOTIFY_CLIENT_ID = "your-spotify-client-id"
$env:SPOTIFY_CLIENT_SECRET = "your-spotify-client-secret"
# Get credentials from: https://developer.spotify.com/dashboard

# Then fetch Spotify links by searching artist names:
python scripts/fetch_spotify_links.py --festival footprints --year 2026
# Or explicitly use API for any festival:
python scripts/fetch_spotify_links.py --festival down-the-rabbit-hole --year 2026 --api
```

**Note:** Footprints automatically uses Spotify API (no `--api` flag needed) because TivoliVredenburg doesn't embed Spotify links.

This will:

- Scrape Spotify links from festival pages OR search Spotify API by artist name
- Update existing links if they've changed
- Add new links for artists that didn't have them
- Verify existing links are still correct
- Fall back to Spotify API if scraping fails
- Be respectful to servers with rate limiting (0.5s between requests)

**Example output:**

```text
=== Updating Spotify Links from Down The Rabbit Hole 2026 ===

Processing 65 artists...

Fetching: Florence + The Machine...
  ✓ Verified: Florence + The Machine
Fetching: Little Simz...
  ✓ Added: Little Simz
Fetching: Loyle Carner...
  ✓ Updated: Loyle Carner
    Old: https://open.spotify.com/artist/xyz
    New: https://open.spotify.com/artist/abc

✓ Complete!
  - 15 link(s) added
  - 3 link(s) updated
  - CSV updated: docs/down-the-rabbit-hole/2026/2026.csv
```

**Note:** This script extracts Spotify links from the festival's official artist pages, which are often more reliable than AI-generated links. Run this after `scripts/fetch_festival_data.py` to ensure you have the latest links.

#### Step 4: Translate Festival Bios (Optional)

If your festival has Dutch bios but needs English translations, use the translation helper:

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
# Set up Azure OpenAI credentials (same as enrichment)
$env:AZURE_OPENAI_KEY = "your-azure-openai-key-here"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.cognitiveservices.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"

# Translate Dutch festival bios to English
python scripts/helpers/translate_festival_bios.py --festival footprints --year 2026
```

This will:

- Read all artists from the CSV
- Check for Dutch bios (`Festival Bio (NL)`) without English translations
- Translate each bio using Azure OpenAI
- Save translations to the `Festival Bio (EN)` column
- Skip artists that already have English bios
- Preserve the original Dutch bios

**Note:** This is particularly useful for Dutch festivals like Down The Rabbit Hole and Footprints that provide bios only in Dutch.

### Personal Editing

Feel free to modify these columns at any time:

- My take
- My rating

These changes will be preserved during updates.

#### Editing CSV Files in VS Code

For easier manual editing of CSV files with a spreadsheet-like interface:

1. Install the **Edit CSV** extension in VS Code:
   - Press `Ctrl+Shift+X` (Extensions)
   - Search for **"Edit CSV"** by janisdd
   - Click **Install**

2. Open your CSV file and edit it:
   - Right-click the CSV file → **Edit CSV**
   - Or press `Ctrl+Shift+P` → type "Edit csv" → select **"Edit csv"**
   - Edit in table view with proper columns and rows
   - Changes save automatically back to CSV format

**Alternative**: Install **Rainbow CSV** extension for color-coded columns and SQL-like queries on CSV data.

**Note**: CSV files use UTF-8 encoding. Avoid opening with Excel via double-click as it misreads Unicode characters. Instead, use VS Code or Excel's **Data → From Text/CSV** import feature and select UTF-8 encoding.

### Generating HTML Pages

Create interactive HTML pages from your CSV data for publishing via GitHub Pages:

#### Step 1: Main lineup page

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
python scripts/generate_html.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_html.py --festival pinkpop --year 2026
python scripts/generate_html.py --festival rock-werchter --year 2026
python scripts/generate_html.py --festival footprints --year 2026
```

This will:

1. Generate a beautiful, interactive HTML table in `docs/festival-slug/2026/index.html`
2. Include sorting functionality (click column headers)
3. Add filtering by Genre, Country, Rating, Gender, and Person of Color (with counts shown for each option)
4. Include real-time search across all fields
5. Display artist images as background in the artist name cells
6. Provide Spotify links for each artist
7. Link each artist name to their individual detail page
8. Include dark mode toggle with persistent preference

#### Step 2: Individual artist pages

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
python scripts/generate_artist_pages.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_artist_pages.py --festival pinkpop --year 2026
python scripts/generate_artist_pages.py --festival rock-werchter --year 2026
python scripts/generate_artist_pages.py --festival footprints --year 2026
```

This will:

1. Generate individual HTML pages for each artist in `docs/festival-slug/2026/artists/`
2. Download and display artist photos from the festival website (images only)
3. Include festival bio and social links from CSV (populated by `fetch_festival_data.py`)
4. Include AI-generated background, your personal take and rating
5. Show detailed information (group size, gender, demographics)
6. Display multiple images in a carousel when available
7. Add previous/next navigation between artists
8. Show fallback messages when information is unavailable

#### Step 3: Startup/Landing page

The main landing page at `docs/index.html` serves as the entry point and festival selector. It includes:

- Welcome message and project description
- Overview of features (filtering, discovery, diversity tracking)
- Links to all available festival lineups organized by year
- Dark mode support
- Responsive design for mobile and desktop

**Manual Updates Required:**

When adding a new festival or year, manually update `docs/index.html`:

1. Add new festival/year buttons in the year list section
2. Ensure links point to correct paths: `festival-slug/year/index.html`
3. Update the "Currently tracking" text if adding new festivals

#### Quick regeneration of all HTML pages

Use the provided scripts to regenerate all HTML pages for all festivals at once:

**PowerShell (recommended):**

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Run the regeneration script
.\scripts\regenerate_all.ps1
```

**Batch file (Windows double-click):**

```batch
# Simply double-click scripts\regenerate_all.bat in Windows Explorer
# Or run from command prompt:
scripts\regenerate_all.bat
```

**Manual generation (individual festivals):**

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Generate for all festivals
python scripts/generate_html.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_artist_pages.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_html.py --festival pinkpop --year 2026
python scripts/generate_artist_pages.py --festival pinkpop --year 2026
python scripts/generate_html.py --festival rock-werchter --year 2026
python scripts/generate_artist_pages.py --festival rock-werchter --year 2026
python scripts/generate_html.py --festival footprints --year 2026
python scripts/generate_artist_pages.py --festival footprints --year 2026
python scripts/generate_archive_index.py docs
```

#### Generating Charts (comparison page)

You can generate the charts/summary comparison page independently. This is useful when you've updated CSV data and only want the charts refreshed (the charts script is also invoked by `scripts/regenerate_all.ps1`).

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Generate the charts comparison page
python scripts/helpers/generate_charts.py
```

This will produce `docs/charts.html` with aggregated statistics and visual comparisons across festivals/years.


All pages share common files for consistency:

- **CSS**: `docs/shared/styles.css` - Styling with dark mode support
- **JavaScript**: `docs/shared/script.js` - Dark mode toggle functionality
- **Images**: `docs/festival-slug/year/artists/<slug>/` - Artist photos and additional images

The generated pages are mobile-responsive, include dark mode, and are ready to publish via GitHub Pages.

**Publishing to GitHub Pages:**

1. Commit the generated `docs/` folder to your repository
2. Go to repository Settings → Pages
3. Set source to "main" branch, "/docs" folder
4. Your festival data will be published at <https://frankvaneykelen.github.io/lineup-radar/>

## Data Sources

- **Down The Rabbit Hole**: <https://downtherabbithole.nl/programma> (Dutch)
- **Pinkpop**: <https://www.pinkpop.nl/en/programme/> (English)
- **Rock Werchter**: <https://www.rockwerchter.be/en/line-up/a-z> (English)
- **Footprints Festival**: Spotify playlist + <https://www.tivolivredenburg.nl/agenda/footprints-festival-2026/> (Dutch)
- **AI Enrichment**: Azure OpenAI GPT-4o for artist metadata and analysis
- **Images**: Festival websites and Spotify API fallback

## Testing

The project includes a comprehensive unit test suite to ensure code quality and reliability:

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Run all tests
pytest tests/ -v

# Run tests with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing
```

**Test Coverage:**

- **CSV operations** (`test_csv_operations.py`): Load, save, encoding, error handling
- **Festival configuration** (`test_config.py`): Config loading, URL generation, all festivals
- **Web scraping** (`test_scraper.py`): Artist page fetching, bio extraction, rate limiting
- **Slugification** (`test_slug.py`): Artist name normalization, sort name generation
- **Data fetching** (`test_fetch_festival_data.py`): Social link extraction, data validation

All tests use mock data and fixtures to avoid making real HTTP requests, ensuring fast and reliable test execution.

For more details on running tests and test structure, see `tests/README.md`.

## Notes

- CSV files use UTF-8 encoding to support international characters
- Empty fields are allowed (not all information may be available for every artist)
- The system is designed for personal use and customization
