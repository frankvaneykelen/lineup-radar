# Down The Rabbit Hole - Personal Festival Program Tracker

A personal tracking system for the Down The Rabbit Hole festival program, maintaining detailed information about artists performing each year.

## Purpose

This project helps track and rate artists performing at Down The Rabbit Hole festival. Each year gets its own CSV file with comprehensive artist information including genres, ratings, and personal notes.

## Structure

### CSV Files

- One CSV file per festival year (e.g., `2026.csv`, `2027.csv`)
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

### Initial Setup

1. Create CSV file for the current/upcoming festival year
2. Populate with artist information from official festival website

### Updating with New Artists

When new artists are announced on the festival website, follow these steps:

#### Step 1: Update lineup from website

```powershell
python update_lineup.py
```

This will:

1. Fetch the updated lineup from <https://downtherabbithole.nl/programma>
2. Track your existing edits to "My take" and "My rating"
3. Compare with existing CSV
4. Add only new artists (preserving all existing user edits)

#### Step 2: Fetch festival data (bio, social links)

```powershell
python fetch_festival_data.py --year 2026
```

This will:

1. Scrape festival bio (Dutch) from artist pages
2. Translate bio to English using AI
3. Extract social media links
4. Store all data in CSV for later use

**Benefits:**

- Only fetches data once per artist
- Future page generation is instant (no API calls)
- Translations are cached
- Can regenerate pages without API costs

Your personal notes (My take, My rating) are never overwritten during updates.

### Enriching Artist Data

After adding new artists, you can fill in their details:

**Manual enrichment:**

```powershell
python enrich_artists.py
```

This will show which artists need data and you can fill them in manually.

**AI-powered enrichment:**

```powershell
python enrich_artists.py --ai
```

This requires API setup. Run `python enrich_artists.py --setup` for instructions.

**Quick setup example (Azure OpenAI):**

```powershell
$env:AZURE_OPENAI_KEY = "your-azure-openai-key-here"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.cognitiveservices.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
python enrich_artists.py --ai --parallel
```

The AI will automatically populate all empty fields including:

- **Objective data**: Genre, Country, Bio, Spotify links, group size, demographics
- **Subjective analysis**: "My take" (critical assessment based on reviews) and "My rating" (1-10 based on critical consensus)

**Important**: Once you edit "My take" or "My rating" manually, those fields will never be overwritten by future AI enrichments. Your personal edits are always preserved.

**Validating AI enrichment:**

To verify that AI enrichment produces accurate data (not hallucinated), you can validate existing enrichments:

```powershell
python validate_enrichment.py --artist "Artist Name"
```

This read-only tool re-runs AI enrichment with updated guidelines and compares results to check if newer, more conservative guidelines would have prevented inaccurate data. Use `--all` to validate all artists (uses many API calls).

### Personal Editing

Feel free to modify these columns at any time:

- My take
- My rating

These changes will be preserved during updates.

### Generating HTML Pages

Create interactive HTML pages from your CSV data for publishing via GitHub Pages:

#### Step 1: Main lineup page

```powershell
python generate_html.py --year 2026 --festival down-the-rabbit-hole
```

This will:

1. Generate a beautiful, interactive HTML table in `docs/2026/index.html`
2. Include sorting functionality (click column headers)
3. Add filtering by Genre, Country, Rating, Gender, and Person of Color
4. Include real-time search across all fields
5. Display artist images as background in the artist name cells
6. Provide Spotify links for each artist
7. Link each artist name to their individual detail page
8. Include dark mode toggle with persistent preference

#### Step 2: Individual artist pages

```powershell
python generate_artist_pages.py --year 2026 --festival down-the-rabbit-hole
```

This will:

1. Generate individual HTML pages for each artist in `docs/2026/artists/`
2. Download and display artist photos from the festival website
3. Include festival bio (Dutch + English translation), AI-generated background, your personal take and rating
4. Show detailed information (group size, gender, demographics)
5. Extract and display social media links from the festival website
6. Display multiple images in a carousel when available
7. Add previous/next navigation between artists
8. Show fallback messages when information is unavailable

#### Step 3: Archive index page

```powershell
python generate_archive_index.py docs
```

This will:

1. Generate the main landing page at `docs/index.html`
2. Automatically detect all year folders with lineup pages
3. Create buttons linking to each year's lineup
4. Serve as the entry point for your GitHub Pages site

#### Quick generation of all pages

```powershell
python generate_html.py --year 2026; python generate_artist_pages.py --year 2026; python generate_archive_index.py docs
```

All pages share common files for consistency:

- **CSS**: `docs/2026/styles.css` - Styling with dark mode support
- **JavaScript**: `docs/2026/script.js` - Dark mode toggle functionality
- **Images**: `docs/2026/artists/<slug>/` - Artist photos and additional images

The generated pages are mobile-responsive, include dark mode, and are ready to publish via GitHub Pages.

**Publishing to GitHub Pages:**

1. Commit the generated `docs/` folder to your repository
2. Go to repository Settings → Pages
3. Set source to "main" branch, "/docs" folder
4. Your festival data will be published at <https://frankvaneykelen.github.io/down-the-rabbit-hole/>

## Data Sources

- **Festival Lineup**: <https://downtherabbithole.nl/programma>
- **Artist Information**: To be populated from various sources (Spotify, Wikipedia, artist websites)

## Notes

- CSV files use UTF-8 encoding to support international characters
- Empty fields are allowed (not all information may be available for every artist)
- The system is designed for personal use and customization
