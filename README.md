# Frank's LineupRadar - Multi-Festival Program Tracker

A personal tracking system for multiple festival programs, maintaining detailed information about artists performing at various festivals each year.

## Purpose

This project helps track and rate artists performing at different festivals. Each festival has its own folder structure with CSV files per year, containing comprehensive artist information including genres, ratings, and personal notes.

## Supported Festivals (Examples)

Below are some of the festivals currently supported by LineupRadar. This is not a complete list—new festivals and editions are added regularly. For the most up-to-date coverage, see the festival folders in `docs/`.

- **Down The Rabbit Hole** (Dutch, Beuningen)
- **Pinkpop** (English, Landgraaf)
- **Rock Werchter** (English, Werchter)
- **Footprints Festival** (Dutch, Utrecht - custom scraper with Spotify integration)
- **Best Kept Secret** (Dutch, Hilvarenbeek)

Each festival can have its own configuration (language, scraping patterns, etc.).

## Structure

### Festival Organization

- Festivals are organized within the `docs/` directory structure
- Each festival has: `docs/festival-slug/year/year.csv` (e.g., `docs/pinkpop/2026/2026.csv`)
- Festival configuration is stored in `festival_helpers/config.py`
- This structure keeps all published content (CSV + HTML) together

**Note:** The folder must be named `docs/` (not `festivals/` or any other name) because GitHub Pages only supports publishing from three specific locations: the repository root (`/`), a folder named `/docs`, or a `gh-pages` branch. Since this project uses GitHub Pages for hosting, the `docs/` folder name is required.

### CSV Files

- One CSV file per festival year stored in `docs/festival-slug/year/year.csv`
- Examples: `docs/down-the-rabbit-hole/2026/2026.csv`, `docs/pinkpop/2026/2026.csv`
- Each file contains the following columns:
  - **Artist**: Name of the artist/band
  - **Genre**: Musical genre
  - **Country**: Country of origin
  - **Bio**: Brief artist biography
  - **Website**: Official artist/band website
  - **AI Summary**: AI-generated critical assessment and notes
  - **AI Rating**: AI-generated rating (scale: 1-10)
  - **Spotify link**: Link to artist's Spotify profile
  - **Number of People in Act**: Band size
  - **Gender of Front Person**: Gender identification of lead performer
  - **Front Person of Color?**: Yes/No indicator
  - **Cancelled**: Yes/No indicator if the artist has cancelled their performance

### Data Preservation

- The system checks existing CSV values before updating
- AI-generated notes (AI Summary, AI Rating) are never overwritten once set
- When new artists are announced, only those new entries are added
- User edits to any field are automatically preserved during updates

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

# Then run scrape commands for each festival
python scripts/scrape_festival.py down-the-rabbit-hole --year 2026
python scripts/scrape_festival.py pinkpop --year 2026
python scripts/scrape_festival.py rock-werchter --year 2026
python scripts/scrape_festival.py footprints --year 2026
python scripts/scrape_festival.py best-kept-secret --year 2026

# Then fetch festival-specific data (bios, social links)
python scripts/fetch_festival_data.py --festival down-the-rabbit-hole --year 2026
python scripts/fetch_festival_data.py --festival pinkpop --year 2026
python scripts/fetch_festival_data.py --festival rock-werchter --year 2026
python scripts/fetch_festival_data.py --festival footprints --year 2026
python scripts/fetch_festival_data.py --festival best-kept-secret --year 2026
```

This will:

1. Fetch the lineup from the festival's program page
2. Scrape artist bios in the festival's language (Dutch/English)
3. Extract social media links and images
4. Track your existing edits to "AI Summary" and "AI Rating"
5. Add only new artists (preserving all existing user edits)

Your AI-generated notes (AI Summary, AI Rating) are never overwritten during updates.

#### Step 2: Enriching Artist Data

After scraping new artists, you can enrich their data either manually or with AI:

**Manual enrichment (for local/emerging acts or when you have specific info):**

```powershell
# Interactive prompt-based enrichment
python scripts/manual_enrich_artists.py --festival alkmaarse-eigenste --year 2026

# Or enrich a specific artist
python scripts/manual_enrich_artists.py --festival alkmaarse-eigenste --year 2026 --artist "Marigold"
```

The script will interactively prompt you for:

- Genre
- Country (defaults to Netherlands on Enter)
- Bio (single or multi-line)
- Spotify link
- Gender of Front Person (1=Male, 2=Female, 3=Non-Binary, 4=Band)
- Front Person of Color (y/n)
- Image (URL to download or local file path to copy)

Press Enter to skip any field. Progress is saved after each artist, so you can stop and resume anytime.

**AI-powered enrichment:**

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
python scripts/enrich_artists.py --festival down-the-rabbit-hole --year 2026 --ai --parallel
python scripts/enrich_artists.py --festival pinkpop --year 2026 --ai --parallel
python scripts/enrich_artists.py --festival rock-werchter --year 2026 --ai --parallel
python scripts/enrich_artists.py --festival footprints --year 2026 --ai --parallel
python scripts/enrich_artists.py --festival best-kept-secret --year 2026 --ai --parallel
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
- **Subjective analysis**: "AI Summary" (critical assessment based on reviews) and "AI Rating" (1-10 with discovery-focused weighting)

**AI Rating System**: The rating scale (1-10) is weighted for discovery, meaning emerging artists with innovative sounds, strong buzz, or unique vision can rate 7-9 alongside established acts. This ensures new talent is valued fairly for discovery purposes. See `documentation/RATING_SYSTEM_CHANGES.md` for details.

**Important**: Once "AI Summary" or "AI Rating" are set by AI enrichment, those fields will never be overwritten by future AI enrichments unless cleared. Your edits are always preserved.

**Note:** When AI lacks data for an artist, the system automatically uses the festival bio as a fallback, prefixed with "[using festival bio due to a lack of publicly available data]".

#### Step 3: Fetch Spotify Links

After enriching artist data, you can fetch official Spotify links from the festival website or Spotify API:

##### Option 1: Scrape from festival pages (DTRH, Pinkpop, Rock Werchter)

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
python scripts/fetch_spotify_links.py --festival down-the-rabbit-hole --year 2026
python scripts/fetch_spotify_links.py --festival pinkpop --year 2026
python scripts/fetch_spotify_links.py --festival rock-werchter --year 2026
python scripts/fetch_spotify_links.py --festival best-kept-secret --year 2026
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
python scripts/generate_html.py --festival best-kept-secret --year 2026
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
python scripts/generate_artist_pages.py --festival best-kept-secret --year 2026
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

**Regenerate individual festival:**

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Regenerate pages for a single festival (lineup, about, artist pages, Spotify playlist)
.\scripts\regenerate_festival.ps1 -Festival down-the-rabbit-hole
.\scripts\regenerate_festival.ps1 -Festival pinkpop
.\scripts\regenerate_festival.ps1 -Festival rock-werchter
.\scripts\regenerate_festival.ps1 -Festival footprints
.\scripts\regenerate_festival.ps1 -Festival best-kept-secret

# Optionally specify a different year
.\scripts\regenerate_festival.ps1 -Festival pinkpop -Year 2025
```

**Regenerate individual Spotify playlist only:**

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Update only the Spotify playlist for a festival (requires credentials in .keys.txt)
python scripts/generate_spotify_playlists.py --festival alkmaarse-eigenste --year 2026
python scripts/generate_spotify_playlists.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_spotify_playlists.py --festival pinkpop --year 2026
python scripts/generate_spotify_playlists.py --festival rock-werchter --year 2026
python scripts/generate_spotify_playlists.py --festival footprints --year 2026
python scripts/generate_spotify_playlists.py --festival best-kept-secret --year 2026
```

**Manual generation (individual components):**

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Generate individual components for festivals
python scripts/generate_html.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_artist_pages.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_html.py --festival pinkpop --year 2026
python scripts/generate_artist_pages.py --festival pinkpop --year 2026
python scripts/generate_html.py --festival rock-werchter --year 2026
python scripts/generate_artist_pages.py --festival rock-werchter --year 2026
python scripts/generate_html.py --festival footprints --year 2026
python scripts/generate_artist_pages.py --festival footprints --year 2026
python scripts/generate_html.py --festival best-kept-secret --year 2026
python scripts/generate_artist_pages.py --festival best-kept-secret --year 2026
python scripts/generate_homepage.py docs
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

#### Generating Spotify Playlists

You can generate or update Spotify playlists for each festival. This creates curated playlists with top tracks from lineup artists.

**Setup (one-time):**

1. Create a Spotify Developer App at <https://developer.spotify.com/dashboard>
2. Save credentials to `.keys.txt` in the project root:

   ```text
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

**Generate playlists for individual festivals:**

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
python scripts/generate_spotify_playlists.py --festival alkmaarse-eigenste --year 2026
python scripts/generate_spotify_playlists.py --festival down-the-rabbit-hole --year 2026
python scripts/generate_spotify_playlists.py --festival pinkpop --year 2026
python scripts/generate_spotify_playlists.py --festival rock-werchter --year 2026
python scripts/generate_spotify_playlists.py --festival footprints --year 2026
python scripts/generate_spotify_playlists.py --festival best-kept-secret --year 2026
```

This will:

- Create a public Spotify playlist (or update existing one)
- Add top tracks from each artist in the lineup
- Skip remix versions to avoid duplicates
- Include rate limiting to respect Spotify API limits
- Prompt you to add missing Spotify links interactively
- Update the CSV with playlist URL and track count

**Note:** The playlist generation is also included in `.\scripts\regenerate_all.ps1` unless you use the `-SkipPlaylists` flag.

**Example with skip flag:**

```powershell
# Regenerate all HTML but skip playlist generation
.\scripts\regenerate_all.ps1 -SkipPlaylists
```

### Helper Scripts

The project includes several helper utilities in `scripts/helpers/` for specialized tasks:

#### Clean Scraped Bio Text

Clean up whitespace and formatting issues in scraped festival bios using AI:

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
# Clean bios for a specific festival
python scripts/helpers/clean_csv_bios.py --festival grauzone --year 2026

# Preview changes without saving (dry run)
python scripts/helpers/clean_csv_bios.py --festival grauzone --year 2026 --dry-run

# Clean all festivals at once
python scripts/helpers/clean_csv_bios.py --all
```

**What it fixes:**
- Missing spaces between words (e.g., "presentAvishag" → "present Avishag")
- Missing spaces around parentheses (e.g., "bandCumgirl8(4AD)" → "band Cumgirl8 (4AD)")
- Missing spaces after commas (e.g., ",Vals Alarm" → ", Vals Alarm")
- Other HTML parsing artifacts from web scraping

**When to use:**
- After scraping festival websites with `scrape_festival.py`
- When you notice formatting issues in existing CSV files
- Before regenerating HTML pages to ensure clean text display

**Note:** The scraper now automatically cleans bio text before saving to CSV, but this helper can fix issues in existing data.

#### Extract Text from Images (OCR)

Extract text from images, screenshots, or scanned documents using Azure OpenAI Vision:

```powershell
# Ensure virtual environment is activated (.venv\Scripts\Activate.ps1)
# Set up Azure OpenAI credentials
$env:AZURE_OPENAI_KEY = "your-azure-openai-key-here"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.cognitiveservices.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"

# Extract text from an image
python scripts/helpers/extract_image_text.py path/to/image.jpg

# Or with a custom prompt
python scripts/helpers/extract_image_text.py lineup_poster.png "Extract all artist names from this festival lineup poster"
```

**Use cases:**
- Extract artist names from lineup announcement images
- OCR festival schedules from screenshots
- Extract text from promotional materials
- Convert image-based data to text format

**Or use as a function in your own scripts:**

```python
from helpers.extract_image_text import extract_text_from_image

text = extract_text_from_image("festival_lineup.jpg")
print(text)
```

#### Other Helper Scripts

Additional helper scripts for specific tasks:

- **Generate taglines**: `scripts/helpers/generate_taglines.py` - Generate catchy 3-7 word taglines for all artists
- **Clear ratings**: `scripts/helpers/clear_dtrh_ratings.py`, `clear_pinkpop_ratings.py` - Reset AI ratings and summaries
- **Generate charts**: `scripts/helpers/generate_charts.py` - Create festival statistics visualizations  
- **Generate FAQ**: `scripts/helpers/generate_faq.py` - Create FAQ page from festival data
- **Search images**: `scripts/helpers/search_artist_images.py` - Find and download artist images
- **Translate bios**: `scripts/helpers/translate_festival_bios.py` - Translate Dutch bios to English
- **Validate enrichment**: `scripts/helpers/validate_enrichment.py` - Check data quality after AI enrichment

**Generate Taglines**:

```powershell
# Generate taglines for all artists that don't have one yet
python scripts/helpers/generate_taglines.py
```

This will automatically:
- Process all festival CSVs
- Generate catchy 3-7 word taglines for artists missing them
- Preserve existing taglines
- Use artist bio, genre, and AI summary for context

Example taglines generated:
- "The most famous animated band on earth" (Gorillaz)
- "Rock music's chief anti-hero" (Jack White)
- "Legendary songsmith of darkness and devotion" (Nick Cave)

**Note**: The enrichment script (`enrich_artists.py`) now automatically generates taglines for new artists.

### About pages

- **Purpose**: Generate a short festival-year profile and structured metadata for each festival year. The generator computes simple festival statistics (genre counts, country counts, diversity breakdowns) and writes a human-readable HTML summary alongside a machine-readable `about.json` used by the site.
- **Files written**: `docs/<festival-slug>/<year>/about.json` and `docs/<festival-slug>/<year>/about.html`.

- **Basic usage (no network calls)**:

```powershell
.venv\Scripts\Activate.ps1
python scripts/generate_about.py --festival down-the-rabbit-hole --year 2026
```

- **AI-backed narrative**: To ask the AI to generate a contextual festival-year narrative, add `--ai`. This will call the configured Azure OpenAI deployment and append an AI-written summary to `about.json` and `about.html`.

```powershell
# Requires Azure OpenAI environment variables described in the repo
python scripts/generate_about.py --festival down-the-rabbit-hole --year 2026 --ai
```

- **Notes**:
   - `about.json` includes a `config_properties` object; `festival_helpers/config.py` prefers those values when present, enabling per-year overrides without editing `config.py`.
   - `--ai` will make network requests to Azure OpenAI and may incur costs. Set these env vars before running AI calls:
      - `AZURE_OPENAI_KEY`
      - `AZURE_OPENAI_ENDPOINT`
      - `AZURE_OPENAI_DEPLOYMENT`


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

### Managing TODO Items as GitHub Issues

The project maintains a TODO list in `documentation/TODO.md` with planned improvements and features. You can convert unchecked TODO items into GitHub issues using the provided scripts:

#### Option 1: Using the GitHub Actions Workflow (Recommended)

1. Go to the repository's **Actions** tab on GitHub
2. Select the **"Create Issues from TODO"** workflow
3. Click **"Run workflow"** button
4. The workflow will automatically create GitHub issues for all unchecked TODO items

#### Option 2: Using the Shell Script Locally

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Generate the shell script and other export formats
python scripts/export_todo_as_issues.py

# Run the generated shell script to create issues
# (requires gh CLI authenticated)
bash tmp/create_issues.sh
```

#### Option 3: Manual Issue Creation

```powershell
# Generate export files (shell script, markdown, CSV)
python scripts/export_todo_as_issues.py

# Review the generated files in tmp/ directory:
# - tmp/create_issues.sh - Bash script with gh CLI commands
# - tmp/issues_to_create.md - Formatted issue descriptions for copy-paste
# - tmp/issues.csv - CSV format for bulk import tools
```

**What these scripts do:**

- Parse `documentation/TODO.md` and extract all unchecked items (only from the "To Do List" section)
- Create GitHub issues with the TODO text as the title
- Include the original TODO text and source location in the issue body
- Automatically label issues with `enhancement` and `from-todo` labels
- Skip items in the "Not To Do" section

**Note:** All generated files are created in the `tmp/` directory which is excluded from version control via `.gitignore`.

## Data Sources

- **Down The Rabbit Hole**: <https://downtherabbithole.nl/programma> (Dutch)
- **Pinkpop**: <https://www.pinkpop.nl/en/programme/> (English)
- **Rock Werchter**: <https://www.rockwerchter.be/en/line-up/a-z> (English)
- **Footprints Festival**: Spotify playlist + <https://www.tivolivredenburg.nl/agenda/footprints-festival-2026/> (Dutch)
- **Best Kept Secret**: <https://www.bestkeptsecret.nl/program/list> (Dutch)
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
