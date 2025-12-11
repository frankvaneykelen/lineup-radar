# Down The Rabbit Hole 2026

**Festival Dates:** July 03-05, 2026  
**Location:** Beuningen, Netherlands

## Quick Commands

### Scraping & Data Updates

```powershell
# Scrape the full lineup from the festival website
python scripts/scrape_festival.py --festival down-the-rabbit-hole --year 2026

# Fetch Spotify links for all artists
python scripts/fetch_spotify_links.py --festival down-the-rabbit-hole --year 2026

# Fetch festival bios and social links
python scripts/fetch_festival_data.py --festival down-the-rabbit-hole --year 2026

# Fetch bio for a single artist (useful for testing or updates)
python scripts/fetch_festival_data.py --festival down-the-rabbit-hole --year 2026 --artist "Artist Name"

# Enrich artist data with AI-generated insights
python scripts/enrich_artists.py --festival down-the-rabbit-hole --year 2026
```

### HTML Generation

```powershell
# Generate the main lineup HTML page
python scripts/generate_html.py --festival down-the-rabbit-hole --year 2026

# Generate individual artist pages with images
python scripts/generate_artist_pages.py --festival down-the-rabbit-hole --year 2026

# Generate the About page with statistics
python scripts/generate_about.py --festival down-the-rabbit-hole --year 2026

# Generate About page with AI-generated profile
python scripts/generate_about.py --festival down-the-rabbit-hole --year 2026 --ai
```

### Spotify Playlist Generation

```powershell
# Generate or update Spotify playlist for this festival
python scripts/generate_spotify_playlists.py --festival down-the-rabbit-hole --year 2026

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
- **Genre** - Musical genre(s)
- **Country** - Country of origin
- **Bio** - AI-generated or general biography
- **AI Summary** - AI-generated critical assessment (preserved on updates)
- **AI Rating** - AI-generated rating 1-10 (preserved on updates)
- **Spotify** - Spotify artist link
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
- **Dutch Bios**: Festival provides Dutch biographies
- **Image Downloads**: Artist images are automatically downloaded when generating artist pages
