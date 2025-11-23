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

When new artists are announced on the festival website, run the update script:

```powershell
python update_lineup.py
```

The script will:

1. Fetch the updated lineup from <https://downtherabbithole.nl/programma>
2. Track your existing edits to "My take" and "My rating"
3. Compare with existing CSV
4. Add only new artists (preserving all existing user edits)
5. Display which new artists were added

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

### Personal Editing

Feel free to modify these columns at any time:

- My take
- My rating

These changes will be preserved during updates.

### Generating HTML Pages

Create interactive HTML pages from your CSV data for publishing via GitHub Pages:

#### Step 1: Main lineup page

```powershell
python generate_html.py 2026.csv docs
```

This will:

1. Generate a beautiful, interactive HTML table in `docs/2026/index.html`
2. Include sorting functionality (click column headers)
3. Add filtering by Genre, Country, Rating, Gender, and Person of Color
4. Include real-time search across all fields
5. Provide Spotify links for each artist
6. Link each artist name to their individual detail page

#### Step 2: Individual artist pages

```powershell
python generate_artist_pages.py 2026.csv docs
```

This will:

1. Generate individual HTML pages for each artist in `docs/2026/artists/`
2. Download and display artist photos from the festival website
3. Include festival bio (Dutch + English translation), AI-generated background, your personal take and rating
4. Show detailed information (group size, gender, demographics)
5. Provide links to Spotify and festival page
6. Add previous/next navigation between artists

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
python generate_html.py 2026.csv docs; python generate_artist_pages.py 2026.csv docs; python generate_archive_index.py docs
```

All pages share a common CSS file (`docs/2026/styles.css`) for easy styling updates.

The generated pages are mobile-responsive and ready to publish via GitHub Pages.

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
