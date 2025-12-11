# Best Kept Secret 2026

**Festival Dates:** June 12-14, 2026  
**Location:** Hilvarenbeek, Netherlands

## Quick Commands

### Scraping & Data Updates

```powershell
# Scrape the full lineup from the festival website
python scripts/scrape_festival.py --festival best-kept-secret --year 2026

# Fetch Spotify links for all artists
python scripts/fetch_spotify_links.py --festival best-kept-secret --year 2026

# Fetch festival bios and social links
python scripts/fetch_festival_data.py --festival best-kept-secret --year 2026

# Fetch bio for a single artist (useful for testing or updates)
python scripts/fetch_festival_data.py --festival best-kept-secret --year 2026 --artist "Artist Name"

# Enrich artist data with AI-generated insights
python scripts/enrich_artists.py --festival best-kept-secret --year 2026
```

### HTML Generation

```powershell
# Generate the main lineup HTML page
python scripts/generate_html.py --festival best-kept-secret --year 2026

# Generate individual artist pages with images
python scripts/generate_artist_pages.py --festival best-kept-secret --year 2026

# Generate the About page with statistics
python scripts/generate_about.py --festival best-kept-secret --year 2026

# Generate About page with AI-generated profile
python scripts/generate_about.py --festival best-kept-secret --year 2026 --ai
```

### Spotify Playlist Generation

```powershell
# Generate or update Spotify playlist for this festival
python scripts/generate_spotify_playlists.py --festival best-kept-secret --year 2026

# Note: Requires Spotify credentials in .keys.txt
# See setup_spotify.md for configuration instructions
```

### Full Regeneration

```powershell
# Regenerate all HTML files (lineup, about, artist pages)
.\scripts\regenerate_all.ps1
```

## Files in This Directory

- **2026.csv** - Main lineup data with all artist information
- **about.json** - Festival statistics and metadata
- **about.html** - Festival overview and statistics page
- **index.html** - Main lineup page
- **overrides.css** - Festival-specific styling
- **overrides.js** - Festival-specific JavaScript
- **artists/** - Individual artist pages with images

## CSV Structure

The `2026.csv` file contains these columns:

- **Artist** - Artist/band name
- **Tagline** - Festival tagline/description
- **Date** - Performance date (YYYY-MM-DD format)
- **Start Time** - Performance start time
- **End Time** - Performance end time
- **Stage** - Stage name
- **Genre** - Musical genre(s)
- **Country** - Country of origin
- **Bio** - AI-generated or general biography
- **Website** - Official website
- **Spotify** - Spotify artist link
- **YouTube** - YouTube channel
- **Instagram** - Instagram profile
- **Photo URL** - Artist photo URL from festival
- **AI Summary** - AI-generated critical assessment (preserved on updates)
- **AI Rating** - AI-generated rating 1-10 (preserved on updates)
- **Number of People in Act** - Band size
- **Gender of Front Person** - Gender identification
- **Front Person of Color?** - Yes/No
- **Cancelled** - Yes/No if performance is cancelled
- **Festival URL** - Artist's festival page URL
- **Festival Bio (NL)** - Dutch bio from festival
- **Festival Bio (EN)** - English bio from festival
- **Social Links** - JSON with social media links
- **Images Scraped** - Yes/No if images downloaded

## Notes

- **Personal Data Preserved**: The "AI Summary" and "AI Rating" columns are never overwritten when running update scripts
- **Date Format**: Dates are in YYYY-MM-DD format for precise scheduling
- **English Bios**: Festival provides English biographies
- **Image Downloads**: Artist images are automatically downloaded when generating artist pages
